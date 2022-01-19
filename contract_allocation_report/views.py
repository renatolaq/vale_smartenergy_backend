from datetime import datetime, timezone, date
from django.http import HttpRequest
from rest_framework.response import Response
from django.core.paginator import Paginator
from django.db.models import Max, F, OuterRef, Subquery
from calendar import month_name, different_locale
from rest_framework import status
from uuid import uuid4
from django.db import transaction
from copy import copy
from itertools import groupby

from balance_report_market_settlement.models import Report, DetailedBalance, PriorizedCliq
from cliq_contract.models import CliqContract
from company.models import Company

from .models.Revision import Revision
from .models.Destination import Destination
from .models.StateDestination import StateDestination
from .models.ContractAllocationReport import ContractAllocationReport, ContractAllocationReportType
from .models.Source import Source, SourceType
from .ErrorWithCode import ErrorWithCode

from .serializers.ContractAllocationReportSerializer import ContractAllocationReportSerializer
from .serializers.ContractAllocationReportSummarySerializer import ContractAllocationReportSummarySerializer
from .serializers.SaveContractAllocationReportSerializer import SaveContractAllocationReportSerializer
from .services.IntegrationService import IntegrationService
from .services.GenerationService import GenerationService


def list_contract_allocation_report(request: HttpRequest):
    per_page = request.GET.get("perPage")
    page = request.GET.get("page")
    _type = request.GET.get("type", None) or None
    active = request.GET.get("active", None) or None
    sort = request.GET.get("sort", "referenceMonth") or "referenceMonth"

    if(page is None):
        page = 1

    if(per_page is None):
        per_page = 20

    page = int(page)
    per_page = int(per_page)

    result = ContractAllocationReport.objects.all()

    if _type:
        for v in ContractAllocationReportType:
            if _type == v.verbose_name:
                _type = v
                break

    if active:
        result = result.annotate(last_revision_val=Max(
            'revision__revision'))
        result = result.filter(revision__active=True if active == "true" else False,
                               revision__revision=F("last_revision_val"))

    if sort == "referenceMonth":
        sort = "reference_month"
    elif sort == "-referenceMonth":
        sort = "-reference_month"
    else:
        sort = "reference_month"

    result = result.order_by(sort)
    result_page = result

    result_paginator = Paginator(result, per_page)
    result_page = list(result_paginator.get_page(page)
                       .object_list) if result_paginator.num_pages >= page else []

    contract_allocation_report_ids = list(map(lambda v: v.id, result_page))

    revisions = Revision.objects.all()

    newest_revision_query = Revision.objects.filter(
        contract_allocation_report=OuterRef("contract_allocation_report")).order_by('-revision')
    revisions = revisions.annotate(newest_revision=Subquery(
        newest_revision_query.values("id")[:1])).filter(id=F("newest_revision"))
    revisions = list(revisions.filter(
        contract_allocation_report__in=contract_allocation_report_ids))

    result_page = list(map(lambda x: x.__dict__, result_page))
    for d in result_page:
        d["last_revision"] = list(
            filter(lambda v: v.contract_allocation_report_id == d["id"], revisions))[0]

    serializer = ContractAllocationReportSummarySerializer(
        result_page, many=True)

    response = Response(serializer.data)
    if per_page is not None:
        response["X-Total-Count"] = result_paginator.count
        response["X-Total-Pages"] = result_paginator.num_pages
        response["Access-Control-Expose-Headers"] = "X-Total-Count, X-Total-Pages"
    return response


def get_contract_allocation_report(request, id):
    contract_allocation_report = ContractAllocationReport.objects.get(
        id=id)
    last_revision = Revision.objects \
        .filter(contract_allocation_report=id) \
        .order_by("-revision")[0]
    contract_allocation_report = contract_allocation_report.__dict__
    contract_allocation_report["last_revision"] = last_revision
    serializer = ContractAllocationReportSerializer(
        contract_allocation_report)
    return Response(serializer.data)


@transaction.atomic
def save_contract_allocation_report(request, id=None):
    balance_id = request.data.get("balanceId")
    if not balance_id:
        raise ErrorWithCode.from_error(
            "BALANCE_NOT_FOUND", "Balance not found", "/balanceId")

    integration_service = IntegrationService()
    generation_service = GenerationService(integration_service)

    balance = integration_service.get_balance_data(balance_id)
    if not balance:
        raise ErrorWithCode.from_error(
            "BALANCE_NOT_FOUND", "Balance not found", "/balanceId")

    trans_savepoint = transaction.savepoint()

    revision: Revision = None
    last_revision: Revision = None
    contract_allocation_report: ContractAllocationReport = None
    _type = None
    report = None

    if id:
        contract_allocation_report = ContractAllocationReport.objects.get(
            id=id)

        if contract_allocation_report.reference_month != balance["referenceMonth"]:
            raise ErrorWithCode.from_error(
                "BALANCE_WITH_DIFFERENT_MONTH", "invalid balance, reference month different from previous report.", "/balanceId")

        last_revision = Revision.objects \
            .filter(contract_allocation_report=id) \
            .order_by("-revision")[0]

        revision = last_revision
        _type = revision.type

        if _type == ContractAllocationReportType.consolidated:
            if balance_id == revision.balance_id:
                raise ErrorWithCode.from_error(
                    "BALANCE_NOT_CHANGED", "Balance equal to balance of the report, it is not possible to generate changes with the same report.", "/balanceId")

            change_justification = request.data.get("changeJustification")
            if not change_justification:
                raise ErrorWithCode.from_error(
                    "EMPTY_FIELD", "field changeJustification is empty", "/changeJustification")
            revision = Revision()
            revision.revision = last_revision.revision + 1
            revision.change_justification = change_justification
    else:
        contract_allocation_report = ContractAllocationReport()
        contract_allocation_report.reference_month = balance["referenceMonth"]
        contract_allocation_report.save()

        revision = Revision()
        revision.revision = 1
        revision.manual = False
        _type = ContractAllocationReportType.draft

    if _type == ContractAllocationReportType.draft:
        report = generation_service.generate_allocations_from_balance(balance)
        report = generation_service.calculate_from_allocations(report, balance)
        report = generation_service.mount_report_from_allocations(
            report, balance)
        revision.change_justification = ""
    else:
        contract_allocation_report_dic = contract_allocation_report.__dict__
        contract_allocation_report_dic['last_revision'] = last_revision
        report = ContractAllocationReportSerializer(
            contract_allocation_report).data
        report = generation_service.add_new_contracts_from_balance(
            report, balance)
        report = generation_service.calculate_from_allocations(report, balance)
        report = generation_service.mount_report_from_allocations(
            report, balance)

    revision.contract_allocation_report = contract_allocation_report
    revision.type = _type
    revision.change_at = datetime.now(tz=timezone.utc)
    revision.user = f"{request.auth.get('cn')}-{request.auth.get('UserFullName')}"
    revision.active = True
    revision.balance_id = balance['balance']
    revision.icms_cost = report['ICMSCost']
    revision.icms_cost_not_creditable = report['ICMSCostNotCreditable']

    revision.save()

    if _type == ContractAllocationReportType.draft:
        Source.objects.filter(revision=revision).delete()

    for source_data in report["sources"]:
        source = Source()
        source.revision = revision
        source.unit_id = source_data["sourceUnitId"]
        source.contract_id = source_data["sourceContractId"]
        source.type = SourceType.contract if source_data["type"] == "contract" else SourceType.generation
        source.available_power = source_data["availablePower"]
        source.available_for_sale = source_data["availableForSale"]
        source.cost = source_data["cost"]
        source.balance_id_origin = source_data["balance"]
        source.save()

        for destination_data in source_data["destinations"]:
            destination = Destination()
            destination.source = source
            destination.unit_id = destination_data["unitId"]
            destination.allocated_power = destination_data["allocatedPower"]
            destination.icms_cost = destination_data["ICMSCost"]
            destination.icms_cost_not_creditable = destination_data["ICMSCostNotCreditable"]
            destination.save()

        for destination_state_data in source_data["destinationStates"]:
            state_destination = StateDestination()
            state_destination.source = source
            state_destination.state_id = destination_state_data["stateId"]
            state_destination.allocated_power = destination_state_data["allocatedPower"]
            state_destination.save()

    contract_allocation_report = contract_allocation_report.__dict__
    contract_allocation_report['last_revision'] = revision
    serializer = ContractAllocationReportSerializer(
        contract_allocation_report)

    transaction.savepoint_commit(trans_savepoint)

    return Response(serializer.data)


def get_contract_allocation_report_history(request, id):
    contract_allocation_report = ContractAllocationReport.objects.get(
        id=id)

    revisions = contract_allocation_report.revision_set.all()

    results = []
    for rev in revisions:
        d = contract_allocation_report.__dict__.copy()
        d["last_revision"] = rev
        results.append(d)

    serializer = ContractAllocationReportSummarySerializer(
        results, many=True)

    return Response(serializer.data)


def get_contract_allocation_report_revision(request, id, revision):
    contract_allocation_report = ContractAllocationReport.objects.get(
        id=id)
    revision = Revision.objects \
        .filter(contract_allocation_report=id, revision=revision)[0]
    contract_allocation_report = contract_allocation_report.__dict__
    contract_allocation_report["last_revision"] = revision
    serializer = ContractAllocationReportSerializer(
        contract_allocation_report)
    return Response(serializer.data)


def change_state(request, id, state):
    trans_savepoint = transaction.savepoint()
    contract_allocation_report = ContractAllocationReport.objects.get(
        id=id)

    if not request.data.get('changeJustification'):
        raise ErrorWithCode.from_error(
            "JUSTIFICATION_EMPTY", "Justification not sent", "/changeJustification")

    previous_revision = Revision.objects \
        .filter(contract_allocation_report=id) \
        .order_by("-revision")[0]
    revision = Revision.objects \
        .filter(contract_allocation_report=id) \
        .order_by("-revision")[0]
    if(revision.active != state):
        revision.pk = None
        revision.id = None
        revision.revision += 1
        revision.change_justification = request.data['changeJustification']
        revision.active = state
        revision.save()

        for allocation_by_state in previous_revision.state_set.all():
            allocation = list(allocation_by_state.stateallocation_set.all())
            allocation_by_state.pk = None
            allocation_by_state.id = None
            allocation_by_state.revision = revision
            allocation_by_state.save()

            for allocated in allocation:
                allocated.id = None
                allocated.pk = None
                allocated.report_state = allocation_by_state
                allocated.save()

        for allocation_by_unit in previous_revision.unit_set.all():
            allocation_by_unit.pk = None
            allocation_by_unit.id = None
            allocation_by_unit.revision = revision
            allocation_by_unit.save()

        transaction.savepoint_commit(trans_savepoint)

    contract_allocation_report = contract_allocation_report.__dict__
    contract_allocation_report['last_revision'] = revision
    serializer = ContractAllocationReportSerializer(
        contract_allocation_report)

    return Response(serializer.data)


@transaction.atomic
def activate_contract_allocation_report(request, id):
    return change_state(request, id, True)


@transaction.atomic
def deactivate_contract_allocation_report(request, id):
    return change_state(request, id, False)


def generate_contract_allocation_report(request, year, month, balance):
    contract_allocation_report: ContractAllocationReport = ContractAllocationReport.objects.filter(
        reference_month=date(year, month, 1)).first()

    integration_service = IntegrationService()
    generation_service = GenerationService(integration_service)
    balance = integration_service.get_balance_data(balance)
    report = None
    if not balance:
        raise ErrorWithCode.from_error(
            "BALANCE_NOT_FOUND", "Balance not found", "/balanceId")

    if contract_allocation_report:
        last_revision: Revision = Revision.objects \
            .filter(contract_allocation_report=contract_allocation_report) \
            .order_by("-revision")[0]
        if last_revision.balance_id == balance["balance"]:
            contract_allocation_report = contract_allocation_report.__dict__
            contract_allocation_report["last_revision"] = last_revision
            serializer = ContractAllocationReportSerializer(
                contract_allocation_report)
            return Response(serializer.data)

        if last_revision.type == ContractAllocationReportType.draft:
            report = generation_service.generate_allocations_from_balance(balance)
            report = generation_service.calculate_from_allocations(report, balance)
            report = generation_service.mount_report_from_allocations(
                report, balance)
        else:
            contract_allocation_report_dic = contract_allocation_report.__dict__
            contract_allocation_report_dic['last_revision'] = last_revision
            report = ContractAllocationReportSerializer(
                contract_allocation_report).data
            report = generation_service.add_new_contracts_from_balance(
                report, balance)
            report = generation_service.calculate_from_allocations(report, balance)
            report = generation_service.mount_report_from_allocations(
                report, balance)

        report["id"] = contract_allocation_report.id
        report["revision"] = last_revision.revision
        report["referenceMonth"]: balance["referenceMonth"]
        report["type"] = str(last_revision.type)
        report["balance"] = balance["balance"]
        report["active"] = True
        report["manual"] = last_revision.manual
    else:
        report = generation_service.generate_allocations_from_balance(balance)
        report = generation_service.calculate_from_allocations(
            report, balance)
        report = generation_service.mount_report_from_allocations(
            report, balance)  
        report["id"] = 0
        report["revision"] = 0
        report["referenceMonth"]: balance["referenceMonth"]
        report["type"] = "Draft"
        report["balance"] = balance["balance"]
        report["active"] = True  
        report["manual"] = False

    return Response(report)


def list_balance(request, year, month):
    reports = Report.objects.filter(
        status__in=['C'], report_type__initials='BDE', year=year, month=month)
    reports = map(lambda x: {"id": x.id, "name": x.report_name}, reports)
    return Response(reports)


def list_balance_source_destination(request, id):
    integration_service = IntegrationService()
    balance = integration_service.get_balance_data(id)
    ret = {
        "sources": [],
        "destinations": []
    }

    for source in balance['contracts']:
        ret['sources'].append({
            "sourceContractId": int(source['contract_id']),
            "sourceUnitId": int(source['unit_id']),
            "sourceName": source['provider_name'],
            "type": source['type'],
            "availablePower": source['available_power']
        })

    for source in balance['generators']:
        ret['sources'].append({
            "sourceContractId": None,
            "sourceUnitId": int(source['unit_id']),
            "sourceName": source['provider_name'],
            "type": source['type'],
            "availablePower": source['available_power']
        })

    for destination in balance['consumers']:
        ret['destinations'].append({
            "unitId": int(destination['unit_id']),
            "unitName": destination['unit_name'],
            "consumption": destination['volume']
        })

    return Response(ret)


def consolidate_contract_allocation_report(request, id):
    change_justification = request.data.get("changeJustification")
    if not change_justification:
        raise ErrorWithCode.from_error(
            "EMPTY_FIELD", "field changeJustification is empty", "/changeJustification")

    contract_allocation_report = ContractAllocationReport.objects.get(
        id=id)
    last_revision: Revision = Revision.objects \
        .filter(contract_allocation_report=id) \
        .order_by("-revision")[0]

    if last_revision.type == ContractAllocationReportType.draft:
        last_revision.type = ContractAllocationReportType.consolidated
        last_revision.user = f"{request.auth.get('cn')}-{request.auth.get('UserFullName')}"
        last_revision.change_at = datetime.now(tz=timezone.utc)
        last_revision.change_justification = change_justification
        last_revision.save()

    contract_allocation_report = contract_allocation_report.__dict__
    contract_allocation_report["last_revision"] = last_revision
    serializer = ContractAllocationReportSerializer(
        contract_allocation_report)
    return Response(serializer.data)


def manual_calculate_contract_allocation_report(request, id=None):
    serializer = SaveContractAllocationReportSerializer(data=request.data)
    if serializer.is_valid(True):
        integration_service = IntegrationService()
        generation_service = GenerationService(integration_service)

        balance = integration_service.get_balance_data(
            serializer.validated_data["balance"])
        if not balance:
            raise ErrorWithCode.from_error(
                "BALANCE_NOT_FOUND", "Balance not found", "/balance")

        for source in serializer.validated_data["sources"]:
            source["balance"] = serializer.validated_data["balance"]

        revision: Revision = None
        last_revision: Revision = None
        contract_allocation_report: ContractAllocationReport = None
        _type = None
        report = None

        if id:
            contract_allocation_report = ContractAllocationReport.objects.get(
                id=id)

            if contract_allocation_report.reference_month != balance["referenceMonth"]:
                raise ErrorWithCode.from_error(
                    "BALANCE_WITH_DIFFERENT_MONTH", "invalid balance, reference month different from previous report.", "/balanceId")

            last_revision = Revision.objects \
                .filter(contract_allocation_report=id) \
                .order_by("-revision")[0]

            _type = last_revision.type

            if _type == ContractAllocationReportType.consolidated:
                if serializer.validated_data["balance"] == last_revision.balance_id:
                    raise ErrorWithCode.from_error(
                        "BALANCE_NOT_CHANGED", "Balance equal to balance of the report, it is not possible to generate changes with the same report.", "/balanceId")
        else:
            _type = ContractAllocationReportType.draft

        if _type == ContractAllocationReportType.draft:
            report = serializer.validated_data["sources"]
            report = generation_service.calculate_from_allocations(
                report, balance)
            report = generation_service.mount_report_from_allocations(
                report, balance)
        else:
            last_revision.manual = True
            contract_allocation_report_dic = contract_allocation_report.__dict__
            contract_allocation_report_dic['last_revision'] = last_revision
            report = ContractAllocationReportSerializer(
                contract_allocation_report).data
            report = SaveContractAllocationReportSerializer(data=report)
            report.is_valid(True)
            report = report.validated_data
            report = report["sources"]                
            report = report + generation_service.calculate_from_allocations(
                serializer.validated_data["sources"], balance)
            report = generation_service.mount_report_from_allocations(
                report, balance)
            report["id"] = contract_allocation_report.id
            report["revision"] = last_revision.revision

        report["referenceMonth"]: balance["referenceMonth"]
        report["type"] = str(_type)
        report["balance"] = balance["balance"]
        report["active"] = True
        return Response(report)


@transaction.atomic
def manual_save_contract_allocation_report(request, id=None):
    serializer = SaveContractAllocationReportSerializer(data=request.data)
    if serializer.is_valid(True):
        integration_service = IntegrationService()
        generation_service = GenerationService(integration_service)

        balance = integration_service.get_balance_data(
            serializer.validated_data["balance"])
        if not balance:
            raise ErrorWithCode.from_error(
                "BALANCE_NOT_FOUND", "Balance not found", "/balance")

        for source in serializer.validated_data["sources"]:
            source["balance"] = serializer.validated_data["balance"]

        trans_savepoint = transaction.savepoint()

        revision: Revision = None
        last_revision: Revision = None
        contract_allocation_report: ContractAllocationReport = None
        _type = None
        report = None

        if id:
            contract_allocation_report = ContractAllocationReport.objects.get(
                id=id)

            if contract_allocation_report.reference_month != balance["referenceMonth"]:
                raise ErrorWithCode.from_error(
                    "BALANCE_WITH_DIFFERENT_MONTH", "invalid balance, reference month different from previous report.", "/balanceId")

            last_revision = Revision.objects \
                .filter(contract_allocation_report=id) \
                .order_by("-revision")[0]

            revision = last_revision
            _type = revision.type

            if _type == ContractAllocationReportType.consolidated:
                if balance_id == revision.balance_id:
                    raise ErrorWithCode.from_error(
                        "BALANCE_NOT_CHANGED", "Balance equal to balance of the report, it is not possible to generate changes with the same report.", "/balanceId")

                change_justification = request.data.get("changeJustification")
                if not change_justification:
                    raise ErrorWithCode.from_error(
                        "EMPTY_FIELD", "field changeJustification is empty", "/changeJustification")
                revision = Revision()
                revision.revision = last_revision.revision + 1
                revision.change_justification = change_justification
        else:
            contract_allocation_report = ContractAllocationReport()
            contract_allocation_report.reference_month = balance["referenceMonth"]
            contract_allocation_report.save()

            revision = Revision()
            revision.revision = 1
            _type = ContractAllocationReportType.draft

        if _type == ContractAllocationReportType.draft:
            report = serializer.validated_data["sources"]
            report = generation_service.calculate_from_allocations(
                report, balance)
            report = generation_service.mount_report_from_allocations(
                report, balance)
            revision.change_justification = ""
        else:
            contract_allocation_report_dic = contract_allocation_report.__dict__
            contract_allocation_report_dic['last_revision'] = last_revision
            report = ContractAllocationReportSerializer(
                contract_allocation_report_dic).data
            report["sources"] = report["sources"] + \
                serializer.validated_data["sources"]
            report = generation_service.calculate_from_allocations(
                report, balance)
            report = generation_service.mount_report_from_allocations(
                report, balance)

        revision.contract_allocation_report = contract_allocation_report
        revision.type = _type
        revision.change_at = datetime.now(tz=timezone.utc)
        revision.user = f"{request.auth.get('cn')}-{request.auth.get('UserFullName')}"
        revision.active = True
        revision.balance_id = balance['balance']
        revision.icms_cost = report['ICMSCost']
        revision.icms_cost_not_creditable = report['ICMSCostNotCreditable']
        revision.manual = True

        revision.save()

        if _type == ContractAllocationReportType.draft:
            Source.objects.filter(revision=revision).delete()

        for source_data in report["sources"]:
            source = Source()
            source.revision = revision
            source.unit_id = source_data["sourceUnitId"]
            source.contract_id = source_data["sourceContractId"]
            source.type = SourceType.contract if source_data[
                "type"] == "contract" else SourceType.generation
            source.available_power = source_data["availablePower"]
            source.available_for_sale = source_data["availableForSale"]
            source.cost = source_data["cost"]
            source.balance_id_origin = source_data["balance"]
            source.save()

            for destination_data in source_data["destinations"]:
                destination = Destination()
                destination.source = source
                destination.unit_id = destination_data["unitId"]
                destination.allocated_power = destination_data["allocatedPower"]
                destination.icms_cost = destination_data["ICMSCost"]
                destination.icms_cost_not_creditable = destination_data["ICMSCostNotCreditable"]
                destination.save()

            for destination_state_data in source_data["destinationStates"]:
                state_destination = StateDestination()
                state_destination.source = source
                state_destination.state_id = destination_state_data["stateId"]
                state_destination.allocated_power = destination_state_data["allocatedPower"]
                state_destination.save()

        contract_allocation_report = contract_allocation_report.__dict__
        contract_allocation_report['last_revision'] = revision
        serializer = ContractAllocationReportSerializer(
            contract_allocation_report)

        transaction.savepoint_commit(trans_savepoint)

        return Response(serializer.data)
