from datetime import datetime, timezone
from django.http import HttpRequest
from rest_framework.response import Response
from django.core.paginator import Paginator
from django.db.models import Max, F, OuterRef, Subquery
from calendar import month_name, different_locale
from rest_framework import status
from uuid import uuid4
from django.db import transaction

from .serializers.EnergyContractPrioritizationSummarySerializer import EnergyContractPrioritizationSummarySerializer
from .serializers.EnergyContractPrioritizationSerializer import EnergyContractPrioritizationSerializer
from .serializers.SaveEnergyContractPrioritizationSerializer import SaveEnergyContractPrioritizationSerializer

from .models.EnergyContractPrioritization import EnergyContractPrioritization, \
    EnergyContractPrioritizationSubtype, EnergyContractPrioritizationType
from .models.Revision import Revision
from .models.Consumer import Consumer
from .models.Contract import Contract
from .models.Generator import Generator
from .models.Parameter import Parameter
from SmartEnergy.utils.exception.ErroWithCode import ErrorWithCode

from core.attachment_utility import generic_csv, generic_pdf, generic_xls
from locales.translates_function import translate_language_header, translate_language

def export_energy_contract_prioritization(request: HttpRequest):
    per_page = request.GET.get("perPage")
    page = request.GET.get("page")
    name = request.GET.get("name", None) or None
    _type = request.GET.get("type", None) or None
    active = request.GET.get("active", None) or None
    sort = request.GET.get("sort", "name") or "name"
    file_format = request.GET.get("fileFormat", "csv") or "csv"

    if(per_page is not None and page is None):
        page = 1

    if(page is not None and per_page is None):
        per_page = 20

    if(page is not None and per_page is not None):
        page = int(page)
        per_page = int(per_page)

    result = EnergyContractPrioritization.objects.all()

    if name:
        result = result.filter(name__contains=name)
    if _type:
        subtype = None

        for v in EnergyContractPrioritizationType:
            if _type == v.verbose_name:
                _type = v
                break
        for v in EnergyContractPrioritizationSubtype:
            if _type == v.verbose_name:
                subtype = v
                _type = None
                break
        if subtype:
            result = result.filter(subtype=subtype)
        if _type:
            result = result.filter(type=_type)

    if active:
        result = result.annotate(last_revision_val=Max(
            'revision__revision'))
        result = result.filter(revision__active=True if active == "true" else False,
                               revision__revision=F("last_revision_val"))

    result = result.order_by(sort)
    result_page = result

    if per_page is not None:
        result_paginator = Paginator(result, per_page)
        result_page = list(result_paginator.get_page(page)
                           .object_list) if result_paginator.num_pages >= page else []

    energy_contract_prioritization_ids = list(map(lambda v: v.id, result_page))

    revisions = Revision.objects.all()

    newest_revision_query = Revision.objects.filter(
        energy_contract_prioritization=OuterRef("energy_contract_prioritization")).order_by('-revision')
    revisions = revisions.annotate(newest_revision=Subquery(
        newest_revision_query.values("id")[:1])).filter(id=F("newest_revision"))
    revisions = list(revisions.filter(
        energy_contract_prioritization__in=energy_contract_prioritization_ids))

    result_page = list(map(lambda x: x.__dict__, result_page))
    for d in result_page:
        d["last_revision"] = list(
            filter(lambda v: v.energy_contract_prioritization_id == d["id"], revisions))[0]

    header = {
                'name' : 'name',
                'type' : 'type',
                'subtype' : 'subtype',
                'active' : 'active'
            }
    header = translate_language_header(header, request)

    mapping = [
        "name", "type", "subtype", "active"
    ]

    results = []

    for item in result_page:
        results.append({
            'name' : item["name"],
            'type' : translate_language("energy_contract_prioritization_type_"+str(item["type"]), request),
            'subtype' : translate_language("energy_contract_prioritization_subtype_"+str(item["subtype"]), request),
            'active' : translate_language("yes", request) if item["last_revision"].active else translate_language("no", request),
        })

    if file_format == 'csv':
        return generic_csv(mapping, header, results, "export")
    elif file_format == 'xlsx':
        styles=[]
        return generic_xls(mapping, header, results, "export", styles)
    elif file_format == 'pdf':
        return generic_pdf(mapping, header, results, "export")
    else:
        raise ErrorWithCode.from_error("UNKNOWN_FILE_FORMAT", "Unknown file format", "")


def list_energy_contract_prioritization(request: HttpRequest):
    per_page = request.GET.get("perPage")
    page = request.GET.get("page")
    name = request.GET.get("name", None) or None
    _type = request.GET.get("type", None) or None
    active = request.GET.get("active", None) or None
    sort = request.GET.get("sort", "name") or "name"

    if(per_page is not None and page is None):
        page = 1

    if(page is not None and per_page is None):
        per_page = 20

    if(page is not None and per_page is not None):
        page = int(page)
        per_page = int(per_page)

    result = EnergyContractPrioritization.objects.all()

    if name:
        result = result.filter(name__contains=name)
    if _type:
        subtype = None

        for v in EnergyContractPrioritizationType:
            if _type == v.verbose_name:
                _type = v
                break
        for v in EnergyContractPrioritizationSubtype:
            if _type == v.verbose_name:
                subtype = v
                _type = None
                break
        if subtype:
            result = result.filter(subtype=subtype)
        if _type:
            result = result.filter(type=_type)

    if active:
        result = result.annotate(last_revision_val=Max(
            'revision__revision'))
        result = result.filter(revision__active=True if active == "true" else False,
                               revision__revision=F("last_revision_val"))

    result = result.order_by(sort)
    result_page = result

    if per_page is not None:
        result_paginator = Paginator(result, per_page)
        result_page = list(result_paginator.get_page(page)
                           .object_list) if result_paginator.num_pages >= page else []

    energy_contract_prioritization_ids = list(map(lambda v: v.id, result_page))

    revisions = Revision.objects.all()

    newest_revision_query = Revision.objects.filter(
        energy_contract_prioritization=OuterRef("energy_contract_prioritization")).order_by('-revision')
    revisions = revisions.annotate(newest_revision=Subquery(
        newest_revision_query.values("id")[:1])).filter(id=F("newest_revision"))
    revisions = list(revisions.filter(
        energy_contract_prioritization__in=energy_contract_prioritization_ids))

    result_page = list(map(lambda x: x.__dict__, result_page))
    for d in result_page:
        d["last_revision"] = list(
            filter(lambda v: v.energy_contract_prioritization_id == d["id"], revisions))[0]

    serializer = EnergyContractPrioritizationSummarySerializer(
        result_page, many=True)

    response = Response(serializer.data)
    if per_page is not None:
        response["X-Total-Count"] = result_paginator.count
        response["X-Total-Pages"] = result_paginator.num_pages
        response["Access-Control-Expose-Headers"] = "X-Total-Count, X-Total-Pages"
    return response


def get_energy_contract_prioritization(request, id):
    energy_contract_prioritization = EnergyContractPrioritization.objects.get(
        id=id)
    last_revision = Revision.objects \
        .prefetch_related("consumer_set") \
        .prefetch_related("contract_set") \
        .prefetch_related("generator_set") \
        .prefetch_related("parameter_set") \
        .filter(energy_contract_prioritization=id) \
        .order_by("-revision")[0]
    energy_contract_prioritization = energy_contract_prioritization.__dict__
    energy_contract_prioritization["last_revision"] = last_revision
    serializer = EnergyContractPrioritizationSerializer(
        energy_contract_prioritization)
    return Response(serializer.data)


@transaction.atomic
def save_energy_contract_prioritization(request, id=None):
    serializer = SaveEnergyContractPrioritizationSerializer(data=request.data)
    if serializer.is_valid(True):
        trans_savepoint = transaction.savepoint()
        previous_revision = None
        revision = None

        _type = None
        subtype = None

        for v in EnergyContractPrioritizationType:
            if serializer.validated_data['type'] == v.verbose_name:
                _type = v
                break
        for v in EnergyContractPrioritizationSubtype:
            if serializer.validated_data['subtype'] == v.verbose_name:
                subtype = v
                break

        if id:
            energy_contract_prioritization = EnergyContractPrioritization.objects.get(
                id=id)

            energy_contract_prioritization.name = serializer.validated_data['name']
            energy_contract_prioritization.type = _type
            energy_contract_prioritization.subtype = subtype
            energy_contract_prioritization.save()

            previous_revision = Revision.objects \
                .prefetch_related("consumer_set") \
                .prefetch_related("contract_set") \
                .prefetch_related("generator_set") \
                .prefetch_related("parameter_set") \
                .filter(energy_contract_prioritization=id) \
                .order_by("-revision")[0]

            revision = Revision()
            revision.energy_contract_prioritization = energy_contract_prioritization
            revision.active = serializer.validated_data['active']
            revision.revision = previous_revision.revision + 1
            revision.change_at = datetime.now(tz=timezone.utc)
            revision.user = f"{request.auth.get('cn')}-{request.auth.get('UserFullName')}"
            revision.active = serializer.validated_data['active']
            revision.order = previous_revision.order
        else:
            energy_contract_prioritization = EnergyContractPrioritization()

            energy_contract_prioritization.name = serializer.validated_data['name']
            energy_contract_prioritization.type = _type
            energy_contract_prioritization.subtype = subtype

            energy_contract_prioritization.save()

            revision = Revision()
            revision.energy_contract_prioritization = energy_contract_prioritization
            revision.active = serializer.validated_data['active']
            revision.revision = 1
            revision.change_at = datetime.now(tz=timezone.utc)
            revision.user = f"{request.auth.get('cn')}-{request.auth.get('UserFullName')}"
            revision.active = serializer.validated_data['active']
            if subtype == EnergyContractPrioritizationSubtype.compulsory or subtype == EnergyContractPrioritizationSubtype.preferred:
                revision.order = (Revision.objects.filter(energy_contract_prioritization__subtype=subtype).aggregate(Max("order"))[
                    'order__max'] or 0) + 1
            else:
                revision.order = 0

            previous_revision = revision

        revision.contracts_edited = False
        revision.generators_edited = False
        revision.consumers_edited = False
        revision.parameters_edited = False
        revision.save()

        for contract_data in serializer.validated_data['contracts']:
            if contract_data['provider'] and not contract_data['contracts']:
                contract = Contract()
                contract.revision = revision
                contract.company_provider = contract_data['provider']
                contract.save()
            else:
                for contract_cliq in contract_data['contracts']:
                    contract = Contract()
                    contract.revision = revision
                    contract.company_provider = contract_data['provider']
                    contract.contract_cliq_provider = contract_cliq
                    contract.save()

        for generator_data in serializer.validated_data['generators']:
            generator = Generator()
            generator.revision = revision
            generator.company_generator = generator_data
            generator.save()

        for consumer_data in serializer.validated_data['consumers']:
            if consumer_data['state'] and not consumer_data['units']:
                consumer = Consumer()
                consumer.revision = revision
                consumer.state_consumer = consumer_data['state']
                consumer.save()
            else:
                for unit_data in consumer_data['units']:
                    consumer = Consumer()
                    consumer.revision = revision
                    consumer.state_consumer = consumer_data['state']
                    consumer.company_consumer = unit_data
                    consumer.save()

        for parameter_data in serializer.validated_data['parameters']:
            parameter = Parameter()
            parameter.revision = revision
            parameter.company_provider = parameter_data['provider']
            parameter.contract_cliq_provider = parameter_data['contract']
            parameter.state_comsumer = parameter_data['state']
            parameter.company_comsumer = parameter_data['unit']
            parameter.value = parameter_data['value']
            parameter.save()

        if previous_revision.contract_set.count() != revision.contract_set.count():
            revision.contracts_edited = True
        else:
            olds = list((x.company_provider, x.contract_cliq_provider)
                        for x in previous_revision.contract_set.all())
            news = list((x.company_provider, x.contract_cliq_provider)
                        for x in revision.contract_set.all())
            revision.contracts_edited = not all(x in olds for x in news)

        if previous_revision.generator_set.count() != revision.generator_set.count():
            revision.generators_edited = True
        else:
            olds = list((x.company_generator)
                        for x in previous_revision.generator_set.all())
            news = list((x.company_generator)
                        for x in revision.generator_set.all())
            revision.generators_edited = not all(x in olds for x in news)

        if previous_revision.consumer_set.count() != revision.consumer_set.count():
            revision.consumers_edited = True
        else:
            olds = list((x.state_consumer,
                         x.company_consumer) for x in previous_revision.consumer_set.all())
            news = list((x.state_consumer,
                         x.company_consumer) for x in revision.consumer_set.all())
            revision.consumers_edited = not all(x in olds for x in news)

        if previous_revision.parameter_set.count() != revision.parameter_set.count():
            revision.parameters_edited = True
        else:
            olds = list((x.company_provider,
                         x.contract_cliq_provider,
                         x.state_comsumer,
                         x.company_comsumer,
                         x.value) for x in previous_revision.parameter_set.all())
            news = list((x.company_provider,
                         x.contract_cliq_provider,
                         x.state_comsumer,
                         x.company_comsumer,
                         x.value) for x in revision.parameter_set.all())
            revision.parameters_edited = not all(x in olds for x in news)

        revision.save()
        transaction.savepoint_commit(trans_savepoint)

        energy_contract_prioritization = energy_contract_prioritization.__dict__
        energy_contract_prioritization['last_revision'] = revision
        serializer = EnergyContractPrioritizationSerializer(
            energy_contract_prioritization)

        return Response(serializer.data)


def get_energy_contract_prioritization_history(request, id):
    energy_contract_prioritization = EnergyContractPrioritization.objects.get(
        id=id)

    revisions = energy_contract_prioritization.revision_set.all()

    results = []
    for rev in revisions:
        d = energy_contract_prioritization.__dict__.copy()
        d["last_revision"] = rev
        results.append(d)

    serializer = EnergyContractPrioritizationSummarySerializer(
        results, many=True)

    return Response(serializer.data)


def get_energy_contract_prioritization_revision(request, id, revision):
    energy_contract_prioritization = EnergyContractPrioritization.objects.get(
        id=id)
    revision = Revision.objects \
        .prefetch_related("consumer_set") \
        .prefetch_related("contract_set") \
        .prefetch_related("generator_set") \
        .prefetch_related("parameter_set") \
        .filter(energy_contract_prioritization=id, revision=revision)[0]
    energy_contract_prioritization = energy_contract_prioritization.__dict__
    energy_contract_prioritization["last_revision"] = revision
    serializer = EnergyContractPrioritizationSerializer(
        energy_contract_prioritization)
    return Response(serializer.data)


def change_state(request, id, state):
    trans_savepoint = transaction.savepoint()
    energy_contract_prioritization = EnergyContractPrioritization.objects.get(
        id=id)

    if not request.data.get('changeJustification'):
        raise ErrorWithCode.from_error("JUSTIFICATION_EMPTY", "Justification not sent", "/changeJustification")

    previous_revision = Revision.objects \
        .prefetch_related("consumer_set") \
        .prefetch_related("contract_set") \
        .prefetch_related("generator_set") \
        .prefetch_related("parameter_set") \
        .filter(energy_contract_prioritization=id) \
        .order_by("-revision")[0]
    revision = Revision.objects \
        .prefetch_related("consumer_set") \
        .prefetch_related("contract_set") \
        .prefetch_related("generator_set") \
        .prefetch_related("parameter_set") \
        .filter(energy_contract_prioritization=id) \
        .order_by("-revision")[0]
    revision.pk = None
    revision.id = None
    revision.revision += 1
    revision.change_justification = request.data['changeJustification']
    revision.active = state
    revision.contracts_edited = False
    revision.generators_edited = False
    revision.consumers_edited = False
    revision.parameters_edited = False
    revision.save()

    for contract in previous_revision.contract_set.all():
        contract.pk = None
        contract.id = None
        contract.revision = revision
        contract.save()

    for generator in previous_revision.generator_set.all():
        generator.pk = None
        generator.id = None
        generator.revision = revision
        generator.save()

    for consumer in previous_revision.consumer_set.all():
        consumer.pk = None
        consumer.id = None
        consumer.revision = revision
        consumer.save()

    for parameter in previous_revision.parameter_set.all():
        parameter.pk = None
        parameter.id = None
        parameter.revision = revision
        parameter.save()

    transaction.savepoint_commit(trans_savepoint)

    energy_contract_prioritization = energy_contract_prioritization.__dict__
    energy_contract_prioritization['last_revision'] = revision
    serializer = EnergyContractPrioritizationSerializer(
        energy_contract_prioritization)

    return Response(serializer.data)


@transaction.atomic
def activate_energy_contract_prioritization(request, id):
    return change_state(request, id, True)


@transaction.atomic
def deactivate_energy_contract_prioritization(request, id):
    return change_state(request, id, False)


@transaction.atomic
def save_energy_contract_prioritization_order(request: HttpRequest):
    _type = request.GET.get("type")

    if _type == "Preferred":
        _type = EnergyContractPrioritizationSubtype.preferred
    elif _type == "Compulsory":
        _type = EnergyContractPrioritizationSubtype.compulsory
    else:
        raise ErrorWithCode.from_error(
            "TYPE_NOT_ALLOWED", "Order changes can only occur in types Preferred and Compulsory")

    newest_revision_query = Revision.objects.filter(
        energy_contract_prioritization=OuterRef("energy_contract_prioritization")).order_by('-revision')
    revisions = Revision.objects.select_related('energy_contract_prioritization').annotate(newest_revision=Subquery(
        newest_revision_query.values("id")[:1])).filter(id=F("newest_revision"), energy_contract_prioritization__subtype=_type).order_by('order')

    trans_savepoint = transaction.savepoint()
    orders = sorted(request.data, key=lambda v: v['order'])
    last_created_order = len(orders) + 1
    for revision in revisions:
        revision.order = None
        for index, order in enumerate(orders):
            if order["id"] == revision.energy_contract_prioritization.id:
                revision.order = index + 1
                break
        if not revision.order:
            revision.order = last_created_order
            last_created_order += 1
        revision.save()

    transaction.savepoint_commit(trans_savepoint)

    results = []
    for rev in revisions:
        d = rev.energy_contract_prioritization.__dict__
        d["last_revision"] = rev
        results.append(d)

    serializer = EnergyContractPrioritizationSummarySerializer(
        results, many=True)

    return Response(serializer.data)
