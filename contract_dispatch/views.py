import requests
from django.conf import settings
from datetime import datetime
from collections import OrderedDict
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from django.http import HttpResponse
from rest_framework.response import Response
from rest_framework import status
from rest_framework.viewsets import ModelViewSet

from core.views import generic_paginator
from .utils import translate_field_name
from balance_report_market_settlement.models import Report
from contract_dispatch.models import ContractDispatch, CliqContractCCEEState
from contract_dispatch.serializers import (
    CliqContractContractDispatchViewSerializer,
    ContractDispatchSerializer,
    ContractDispatchSerializerView,
    ContractDispatchUpdateContractsSerializer,
    ContractDispatchDetailSerializer,
    ContractDispatchBalanceSerializer, CliqContractCCEEStateCreateSerializer
)

from cliq_contract.models import CliqContract

from contract_dispatch.generators.pdf_generator import (
    generate_pdf,
    generate_pdf_by_contract,
    generate_pdf_contracts_to_send,
    generate_pdf_contracts_by_ids,
)
from contract_dispatch.generators.xlsx_generator import (
    generate_xlsx,
    generate_xlsx_by_contract,
    generate_xlsx_contracts_to_send,
    generate_xlsx_contracts_by_ids,
)
from contract_dispatch.business.contract_dispatch_business import (
    ContractDispatchBusiness,
)
from SmartEnergy.auth import check_module, permissions, modules
import json

CCEE_INTEGRATION_URL_SUFIX = "/api/ccee/importfile"
CCEE_INTEGRATION_URL_SYNCHRONIZE_SUFIX = "/api/ccee/syncronize"
CCEE_INTEGRATION_URL_SYNCHRONIZE_DISCREPANCIES_SUFIX = "/api/ccee/validate"


@api_view(["GET"])
@check_module(modules.contract_dispatch, [permissions.VIEW, permissions.EDITN1])
def contracts_to_send(request, year, month, balance_id=None):
    contracts = ContractDispatchBusiness.retrieve_contracts_to_send(
        request, year, month, balance_id
    )

    data, page_count, page_next, page_previous = generic_paginator(
        request, list(contracts)
    )

    serializer = CliqContractContractDispatchViewSerializer(data, many=True)

    response = OrderedDict(
        [
            ("count", page_count),
            ("next", page_next),
            ("previous", page_previous),
            ("results", serializer.data),
        ]
    )

    return Response(response, status=status.HTTP_200_OK)


@api_view(["POST"])
@authentication_classes([])
@permission_classes([])
def update_contracts_status(request):
    updates = {"updates": request.data}
    serializer = ContractDispatchUpdateContractsSerializer(data=updates)
    serializer.is_valid(raise_exception=True)

    serializer.save()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["GET"])
@check_module(modules.contract_dispatch, [permissions.VIEW, permissions.EDITN1])
def ccee_synchronize(request):
    if settings.CCEE_INTEGRATION_API_URL is not None:
        r = requests.get(
            settings.CCEE_INTEGRATION_API_URL + CCEE_INTEGRATION_URL_SYNCHRONIZE_SUFIX,
            timeout=360,
        )
        r.raise_for_status()
    else:
        raise RuntimeError("CCEE_INTEGRATION_API_URL environment variable is missing")

    return Response(status=status.HTTP_200_OK)

@api_view(["GET"])
@check_module(modules.contract_dispatch, [permissions.VIEW, permissions.EDITN1])
def ccee_synchronize_discrepancies(request):

    if settings.CCEE_INTEGRATION_API_URL is not None:
        r = requests.post(
            settings.CCEE_INTEGRATION_API_URL + CCEE_INTEGRATION_URL_SYNCHRONIZE_DISCREPANCIES_SUFIX,
            json=[],
            timeout=360,
        )
        r.raise_for_status()
    else:
        raise RuntimeError("CCEE_INTEGRATION_API_URL environment variable is missing")

    return Response(status=status.HTTP_200_OK)


@api_view(["GET"])
@check_module(modules.contract_dispatch, [permissions.VIEW, permissions.EDITN1])
def contract_dispatch_detail(request, pk):
    contract_dispatch = get_object_or_404(ContractDispatch, pk=pk)
    serializer = ContractDispatchDetailSerializer(contract_dispatch, context={})
    return Response(data=serializer.data, status=status.HTTP_200_OK)


@api_view(["GET"])
@check_module(modules.contract_dispatch, [permissions.VIEW, permissions.EDITN1])
def list_balance(request, year, month):
    queryset = Report.objects.filter(status__in=["S", "C"])
    queryset = queryset.filter(report_type__initials="BDE")
    queryset = queryset.filter(year=year).filter(month=month)
    serializer = ContractDispatchBalanceSerializer(queryset, many=True)
    return Response(data=serializer.data, status=status.HTTP_200_OK)


@api_view(["GET"])
@check_module(modules.contract_dispatch, [permissions.VIEW, permissions.EDITN1])
def contract_dispatch_detail_contracts(request, pk):
    contract_dispatch = get_object_or_404(ContractDispatch, pk=pk)

    contracts = ContractDispatchBusiness.retrieve_contracts_by_contract_dispatch(
        request, contract_dispatch
    )

    data, page_count, page_next, page_previous = generic_paginator(
        request, list(contracts)
    )

    serializer = CliqContractContractDispatchViewSerializer(
        data, context={"contract_dispatch_pk": pk}, many=True
    )
    response = OrderedDict(
        [
            ("count", page_count),
            ("next", page_next),
            ("previous", page_previous),
            ("results", serializer.data),
        ]
    )
    return Response(response, status=status.HTTP_200_OK)


@api_view(["POST", "GET"])
@check_module(modules.contract_dispatch, [permissions.VIEW, permissions.EDITN1])
def contract_dispatch(request):
    if request.method == "GET":
        return contract_dispatch_get(request)
    if request.method == "POST":
        return contract_dispatch_post(request)


def contract_dispatch_post(request):
    def build_integration_payload(contract_info, supply_date):
        dateformat = "%d/%m/%Y %H"

        contract = CliqContract.objects.get(pk=contract_info.get("contractId"))

        integration_payload = {}
        integration_payload["id_contract_cliq"] = int(contract.id_contract_cliq)
        if contract.id_contract.modality == "Transferencia":
            integration_payload["operation"] = "transfer"
        else:
            integration_payload["operation"] = contract_info.get("operation")
        if contract.id_ccee.code_ccee:
            integration_payload["cliq_code"] = contract.id_ccee.code_ccee
        integration_payload["start_date"] = contract.id_contract.start_supply.strftime(
            dateformat
        )
        integration_payload["end_date"] = contract.id_contract.end_supply.strftime(
            dateformat
        )
        integration_payload["id_buyer"] = int(
            contract.id_buyer_profile.id_agents.id_ccee.code_ccee
        )
        integration_payload["id_seller"] = int(
            contract.id_vendor_profile.id_agents.id_ccee.code_ccee
        )
        integration_payload["id_submarket"] = int(contract.id_submarket.id_ccee.code_ccee)
        integration_payload["reference"] = contract.id_contract.contract_name
        integration_payload["note"] = "NA"
        integration_payload["average_mount"] = {}
        integration_payload["average_mount"][
            "start_date"
        ] = contract.id_contract.start_supply.strftime(dateformat)
        integration_payload["average_mount"][
            "end_date"
        ] = contract.id_contract.end_supply.strftime(dateformat)
        integration_payload["average_mount"]["mon_year"] = {}
        integration_payload["average_mount"]["mon_year"][
            "mon_year"
        ] = datetime.strptime(supply_date, "%Y-%m").strftime("%m/%Y")
        integration_payload["average_mount"]["mon_year"]["average_mount"] = {
            "average_mount": contract_info.get("volume")
        }
        return integration_payload

    serializer = ContractDispatchSerializer(data=request.data)

    serializer.is_valid(raise_exception=True)

    supply_date = serializer.initial_data["supplyDate"]
    contract_info = serializer.initial_data["contractInfo"]
    ccee_integration_payload = [
        build_integration_payload(contract, supply_date) for contract in contract_info
    ]

    if settings.CCEE_INTEGRATION_API_URL is not None:
        r = requests.post(
            settings.CCEE_INTEGRATION_API_URL + CCEE_INTEGRATION_URL_SUFIX,
            json=ccee_integration_payload,
            timeout=360,
        )
        r.raise_for_status()
    else:
        raise RuntimeError("CCEE_INTEGRATION_API_URL environment variable is missing")

    serializer.context["ccee_integration_response"] = r.json()

    serializer.save()
    return Response(data=serializer.data, status=status.HTTP_201_CREATED)


def contract_dispatch_get(request):
    def validate_ymd_date_format(date_text, field_name):
        try:
            datetime.strptime(date_text, "%Y-%m-%d")
        except ValueError:
            raise ValueError(
                f"Incorrect data format, {field_name} should be YYYY-MM-DD"
            )

    sort_translation_dict = {
        "sentDate": "dispatch_date",
        "-sentDate": "-dispatch_date",
        "lastUpdateDate": "last_status_update_date",
        "-lastUpdateDate": "-last_status_update_date",
        "user": "dispatch_username",
        "-user": "-dispatch_username",
        "supplyDate": "supply_date",
        "-supplyDate": "-supply_date",
        "has_processment_errors": "contractdispatchcliqcontract__cliq_ccee_processment__processment_result__status",
        "-has_processment_errors": "-contractdispatchcliqcontract__cliq_ccee_processment__processment_result__status"
    }

    queryset = ContractDispatch.objects.all().order_by("-dispatch_date")

    dispatch_date = request.query_params.get("sentDate")
    last_status_update_date = request.query_params.get("lastUpdateDate")
    dispatch_username = request.query_params.get("user")
    supply_date = request.query_params.get("supplyDate")
    sort = request.query_params.get("sort")
    has_processment_errors = request.query_params.get("has_processment_errors")

    try:
        if dispatch_date is not None:
            validate_ymd_date_format(dispatch_date, "sentDate")
            queryset = queryset.filter(dispatch_date__date=dispatch_date)
        if last_status_update_date is not None:
            validate_ymd_date_format(last_status_update_date, "lastUpdateDate")
            queryset = queryset.filter(
                last_status_update_date__date=last_status_update_date
            )
        if supply_date is not None:
            validate_ymd_date_format(supply_date, "supplyDate")
            year, month, day = supply_date.split("-", 2)
            queryset = queryset.filter(supply_date__year=year, supply_date__month=month)
        if dispatch_username is not None:
            queryset = queryset.filter(dispatch_username__icontains=dispatch_username)
        if sort is not None:
            queryset = queryset.order_by(
                translate_field_name(sort_translation_dict, sort)
            )
        if has_processment_errors:
            error_query = Q(
                contractdispatchcliqcontract__cliq_ccee_processment__processment_result__status="ERRO"
            )
            if has_processment_errors == "true":
                queryset = queryset.filter(error_query)
            else:
                queryset = queryset.filter(~error_query)
    except ValueError as e:
        return Response(str(e), status=status.HTTP_400_BAD_REQUEST)

    data, page_count, page_next, page_previous = generic_paginator(
        request, list(queryset.distinct())
    )
    serializer = ContractDispatchSerializerView(data, many=True)
    response = OrderedDict(
        [
            ("count", page_count),
            ("next", page_next),
            ("previous", page_previous),
            ("results", serializer.data),
        ]
    )

    return Response(response, status=status.HTTP_200_OK)


@api_view(["GET"])
@check_module(modules.contract_dispatch, [permissions.VIEW, permissions.EDITN1])
def contract_dispatch_pdf(request):
    pdf = generate_pdf(request)
    return HttpResponse(pdf, content_type="application/pdf", status=status.HTTP_200_OK)


@api_view(["GET"])
@check_module(modules.contract_dispatch, [permissions.VIEW, permissions.EDITN1])
def contract_dispatch_xlsx(request):
    xlsx = generate_xlsx(request)

    return HttpResponse(
        xlsx,
        content_type="application/excel; charset=utf-8-sig",
        status=status.HTTP_200_OK,
    )


@api_view(["GET"])
@check_module(modules.contract_dispatch, [permissions.VIEW, permissions.EDITN1])
def contract_dispatch_detail_contracts_pdf(request, pk):
    contract_dispatch = get_object_or_404(ContractDispatch, pk=pk)

    pdf = generate_pdf_by_contract(request, contract_dispatch)

    return HttpResponse(pdf, content_type="application/pdf", status=status.HTTP_200_OK)


@api_view(["GET"])
@check_module(modules.contract_dispatch, [permissions.VIEW, permissions.EDITN1])
def contract_dispatch_detail_contracts_xlsx(request, pk):
    contract_dispatch = get_object_or_404(ContractDispatch, pk=pk)

    xlsx = generate_xlsx_by_contract(request, contract_dispatch)

    return HttpResponse(
        xlsx,
        content_type="application/excel; charset=utf-8-sig",
        status=status.HTTP_200_OK,
    )


@api_view(["GET"])
@check_module(modules.contract_dispatch, [permissions.VIEW, permissions.EDITN1])
def contracts_to_send_pdf(request, year, month, balance_id=None):
    pdf = generate_pdf_contracts_to_send(request, year, month, balance_id)

    return HttpResponse(pdf, content_type="application/pdf", status=status.HTTP_200_OK)


@api_view(["GET"])
@check_module(modules.contract_dispatch, [permissions.VIEW, permissions.EDITN1])
def contracts_to_send_xlsx(request, year, month, balance_id=None):
    xlsx = generate_xlsx_contracts_to_send(request, year, month, balance_id)

    return HttpResponse(
        xlsx,
        content_type="application/excel; charset=utf-8-sig",
        status=status.HTTP_200_OK,
    )


@api_view(["GET"])
@check_module(modules.contract_dispatch, [permissions.VIEW, permissions.EDITN1])
def pdf_by_ids(request, year, month, balance_id=None):
    str_ids = request.query_params.get("ids")
    ids = json.loads(str_ids)
    pdf = generate_pdf_contracts_by_ids(request, year, month, balance_id, ids)

    return HttpResponse(pdf, content_type="application/pdf", status=status.HTTP_200_OK)


@api_view(["GET"])
@check_module(modules.contract_dispatch, [permissions.VIEW, permissions.EDITN1])
def xlsx_by_ids(request, year, month, balance_id=None):
    str_ids = request.query_params.get("ids")
    ids = json.loads(str_ids)
    xlsx = generate_xlsx_contracts_by_ids(request, year, month, balance_id, ids)

    return HttpResponse(
        xlsx,
        content_type="application/excel; charset=utf-8-sig",
        status=status.HTTP_200_OK,
    )


class CliqContractCCEEStateViewset(ModelViewSet):
    queryset = CliqContractCCEEState.objects.all()
    serializer_class = CliqContractCCEEStateCreateSerializer
    permission_classes = []
    authentication_classes = []
    http_method_names = ('post',)

    def get_serializer(self, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        kwargs['context'] = self.get_serializer_context()
        return serializer_class(many=True, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        # TODO: this is a temporary solution to unknown submarket values, please change it to a long term solution
        filtered_data = [data for data in request.data if data.get("submarket") in (1, 2, 3, 4)]
        error_data = [data for data in request.data if data.get("submarket") not in (1, 2, 3, 4)]

        serializer = self.get_serializer(data=filtered_data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        if len(error_data) > 0:
            return Response({"invalid_submarkets": error_data}, status=status.HTTP_201_CREATED)
        else:
            return Response({'ok': True}, status=status.HTTP_201_CREATED)
