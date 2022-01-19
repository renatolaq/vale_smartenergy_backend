import os

from datetime import date, datetime, timedelta
from typing import List
from dateutil.relativedelta import relativedelta
import logging
import sys
import json
import ast

from django.http import HttpResponse, FileResponse
from django.utils import timezone
from django_filters import rest_framework as filters
from django.core.files.storage import FileSystemStorage
from django.shortcuts import get_object_or_404

from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.serializers import ValidationError
from rest_framework.settings import api_settings

from SmartEnergy import settings
from SmartEnergy.auth import check_module
import SmartEnergy.auth.permissions as permissions
import SmartEnergy.auth.modules as modules

from locales.translates_function import translate_label, get_language
from core.models import Log
from core.serializers import generic_update
from company.models import Company
from gauge_point.models import GaugePoint, GaugeEnergyDealership
from budget.models.CompanyBudget import CompanyBudget

from pandas import ExcelWriter
from io import BytesIO

from .uteis.ctu_json import CTUJson
from .uteis.csv_parser import CTUParser
from .uteis.error import generate_delete_msg
from .uteis.error import return_linked_budgets
from .uteis.error import return_linked_gauges
from .serializers import CompanySerializer
from .serializers import EnergyDealerSerializer
from .serializers import RatePostExceptionSerializer
from .serializers import RatedVoltageSerializer
from .serializers import UploadFileUsageContractSerializer
from .serializers import UsageContractCompleteSerializer
from .serializers import UsageContractDistributorSerializer
from .serializers import UsageContractTransmitterSerializer
from .models import TypeUsageContract, RatedVoltage
from .models import UsageContract, UploadFileUsageContract
from .models import Cct, TaxModality, RatePostException, ContractCycles

from pathlib import Path

class UsageContractFilter(filters.FilterSet):
    usage_contract_type = filters.ModelChoiceFilter(
        queryset=TypeUsageContract.objects.all()
    )
    create_date = filters.DateTimeFilter(
        lookup_expr="icontains", field_name="create_date"
    )
    company_name = filters.CharFilter(
        lookup_expr="icontains", field_name="company__company_name"
    )
    company_city = filters.CharFilter(
        lookup_expr="icontains", field_name="company__id_address__id_city__city_name"
    )
    company_state = filters.CharFilter(
        lookup_expr="icontains",
        field_name="company__id_address__id_city__id_state__name",
    )
    company_cnpj = filters.CharFilter(
        lookup_expr="icontains", field_name="company__state_number"
    )
    energy_dealer = filters.CharFilter(
        lookup_expr="icontains", field_name="energy_dealer__company_name"
    )
    agent_cnpj = filters.CharFilter(
        lookup_expr="icontains", field_name="energy_dealer__state_number"
    )
    connection_point = filters.CharFilter(
        lookup_expr="icontains", field_name="connection_point"
    )
    contract_number = filters.CharFilter(lookup_expr="icontains")
    rated_voltage = filters.CharFilter(
        lookup_expr="icontains", field_name="rated_voltage__voltages"
    )
    bought_voltage = filters.CharFilter(
        lookup_expr="icontains", field_name="bought_voltage"
    )
    group = filters.CharFilter(
        lookup_expr="icontains", field_name="rated_voltage__group"
    )
    subgroup = filters.CharFilter(
        lookup_expr="icontains", field_name="rated_voltage__subgroup"
    )
    start_date = filters.DateFilter(lookup_expr="icontains", field_name="start_date")
    end_date = filters.DateFilter(lookup_expr="icontains", field_name="end_date")
    status = filters.CharFilter(lookup_expr="icontains", field_name="status")

    class Meta:
        model = UsageContract
        fields = (
            "usage_contract_type",
            "create_date",
            "company_name",
            "company_city",
            "company_state",
            "company_cnpj",
            "energy_dealer",
            "agent_cnpj",
            "connection_point",
            "contract_number",
            "rated_voltage",
            "bought_voltage",
            "group",
            "subgroup",
            "start_date",
            "end_date",
            "status",
        )


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class CompanyViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = (
        Company.objects.filter(gauge_company__gauge_type="Fronteira")
        .distinct()
        .order_by("company_name")
    )
    serializer_class = CompanySerializer
    filter_fields = ['status']


class EnergyDealerViewSet(viewsets.ReadOnlyModelViewSet):

    serializer_class = EnergyDealerSerializer

    def get_queryset(self):

        if "id" in self.request.query_params:

            list_ids = []
            id_company = int(self.request.query_params["id"])
            company = Company.objects.get(id_company=id_company)
            gauge_points = GaugePoint.objects.filter(id_company=company.id_company)

            for gp in gauge_points:
                gauge_dealers = GaugeEnergyDealership.objects.filter(
                    id_gauge_point=gp.pk
                )
                for gd in gauge_dealers:
                    if gd.id_dealership is not None:
                        list_ids.append(int(gd.id_dealership.pk))

            queryset = (
                Company.objects.filter(pk__in=list_ids)
                .distinct()
                .order_by("company_name")
            )
            return queryset
        else:
            queryset = Company.objects.filter(
                company_dealership__id_gauge_point__id_company__isnull=False
            ).distinct()
            return queryset


class RatedVoltageViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = RatedVoltage.objects.all()
    serializer_class = RatedVoltageSerializer


class RatePostExceptionViewSet(viewsets.ModelViewSet):
    queryset = RatePostException.objects.all()
    serializer_class = RatePostExceptionSerializer


class UsageContractViewSet(viewsets.ModelViewSet):
    queryset = UsageContract.objects.all().order_by("id_usage_contract")
    serializer_class = UsageContractCompleteSerializer
    pagination_class = StandardResultsSetPagination
    filterset_class = UsageContractFilter

    @check_module(modules.usage_contract, [permissions.VIEW, permissions.EDITN1])
    def get_queryset(self):
        return self.queryset

    @check_module(modules.usage_contract, [permissions.VIEW, permissions.EDITN1])
    def list(self, request, *args, **kwargs):

        _date = ""
        if "start_date" in request.query_params:
            _date = request.query_params["start_date"]
        if "end_date" in request.query_params:
            _date = request.query_params["end_date"]
        if "create_date" in request.query_params:
            _date = request.query_params["create_date"]
        try:
            if _date.strip() != "":
                datetime.strptime(_date, "%Y-%m-%d")
        except ValueError:
            resp = {"message": translate_label("error_ctu_find_date", request)}
            return Response(resp, status=status.HTTP_400_BAD_REQUEST)

        queryset = self.filter_queryset(self.get_queryset())
        if 'ordering' in request.query_params:

            _order_by = request.query_params['ordering']
            if 'company_name' == _order_by:
                _order_by = 'company__company_name'
            elif '-company_name' == _order_by:
                _order_by = '-company__company_name'
            
            if 'company_cnpj' == _order_by:
                _order_by = 'company__state_number'
            elif '-company_cnpj' == _order_by:
                _order_by = '-company__state_number'

            if 'company_state' == _order_by:
                _order_by = 'company__id_address__id_city__id_state__name'
            elif '-company_state' == _order_by:
                _order_by = '-company__id_address__id_city__id_state__name'

            if 'company_city' == _order_by:
                _order_by = 'company__id_address__id_city__city_name'
            elif '-company_city' == _order_by:
                _order_by = '-company__id_address__id_city__city_name'

            if 'energy_dealer' == _order_by:
                _order_by = 'energy_dealer__company_name'
            elif '-energy_dealer' == _order_by:
                _order_by = '-energy_dealer__company_name'

            if 'agent_cnpj' == _order_by:
                _order_by = 'energy_dealer__state_number'
            elif '-agent_cnpj' == _order_by:
                _order_by = '-energy_dealer__state_number'

            if 'group' == _order_by:
                _order_by = 'rated_voltage__group'
            elif '-group' == _order_by:
                _order_by = '-rated_voltage__group'

            if 'subgroup' == _order_by:
                _order_by = 'rated_voltage__subgroup'
            elif '-subgroup' == _order_by:
                _order_by = '-rated_voltage__subgroup'

            queryset = queryset.order_by(_order_by)

        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)

        for d in serializer.data:
            desc = d["usage_contract_type"]["description"]
            # if transmissao or transmission in desc
            if "distribu" in desc.lower():
                d["usage_contract_type"]["description"] = translate_label(
                    "field_ctu_type_d", request
                )
            else:
                d["usage_contract_type"]["description"] = translate_label(
                    "field_ctu_type_t", request
                )

        if page is not None:
            return self.get_paginated_response(serializer.data)
        else:
            return Response(serializer.data)

    @staticmethod
    def choose_serialize(usage_request):
        try:
            contract_type = TypeUsageContract.objects.filter(
                pk=usage_request.data["usage_contract_type"]
            )
            contract_type_id = contract_type[0].id_usage_contract_type
        except Exception:
            raise ValidationError()

        if contract_type_id == 1:
            return UsageContractDistributorSerializer
        elif contract_type_id == 2:
            return UsageContractTransmitterSerializer
        else:
            raise ValidationError()

    @check_module(modules.usage_contract, [permissions.EDITN1])
    def create(self, request, *args, **kwargs):
        try:
            upload_file_usage_contract_ids = []
            if "upload_file" in request.data:
                upload_file_usage_contract_ids = [
                    x["id_upload_file_usage_contract"]
                    for x in request.data["upload_file"]
                ]
                del request.data["upload_file"]

            if request.data["rate_post_exception"] is None:
                request.data["rate_post_exception"] = []

            if request.data["energy_transmitter"] is not None:
                if request.data["energy_transmitter"]["aneel_publication"] == "":
                    request.data["energy_transmitter"]["aneel_publication"] = None

                audit_renovation = request.data["energy_transmitter"].get(
                    "audit_renovation", "N"
                )
                request.data["energy_transmitter"][
                    "audit_renovation"
                ] = audit_renovation

            if request.data["energy_distributor"] is not None:

                if request.data["energy_distributor"]["aneel_publication"] == "":
                    request.data["energy_distributor"]["aneel_publication"] = None

                if request.data["energy_distributor"]["audit_renovation"] == "":
                    request.data["energy_distributor"]["audit_renovation"] = "N"

                if request.data["energy_distributor"]["audit_renovation"] is None:
                    request.data["energy_distributor"]["audit_renovation"] = "N"

            if request.data["peak_begin_time"] is not None:
                if request.data["peak_begin_time"] == "":
                    request.data["peak_begin_time"] = None

            if request.data["peak_end_time"] is not None:
                if request.data["peak_end_time"] == "":
                    request.data["peak_end_time"] = None

            _username = request.auth["cn"] + " - " + request.auth["UserFullName"]
            context = {
                "username": _username,
                "upload_file_usage_contract_ids": upload_file_usage_contract_ids,
            }

            serializer = self.choose_serialize(request)
            serializer = serializer(data=request.data, context=context)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)

            headers = self.get_success_headers(serializer.data)
            return Response(
                serializer.data, status=status.HTTP_201_CREATED, headers=headers
            )

        except Exception as e:
            print(e.args)
            resp = {"error": translate_label("error_ctu_save", request), "msg": e.args}
            return Response(resp, status=status.HTTP_400_BAD_REQUEST)

    def get_success_headers(self, data):
        try:
            return {"Location": str(data[api_settings.URL_FIELD_NAME])}
        except (TypeError, KeyError):
            return {}

    def destroy(self, request, *args, **kwargs):
        resp = {"error": translate_label("error_ctu_delete", request)}
        return Response(resp, status=status.HTTP_400_BAD_REQUEST)

    @check_module(modules.usage_contract, [permissions.EDITN1])
    def update(self, request, *args, **kwargs):

        try:
            id_usage_contract = int(kwargs["pk"])
            usage_contract = UsageContract.objects.get(pk=id_usage_contract)
            _status = usage_contract.status

            # Se o contrato de uso estiver desabilitado, entao nao deve ser atualizado
            if "N" in _status and "justification" not in request.data:
                return Response(status=status.HTTP_100_CONTINUE)
            else:
                if "upload_file" in request.data:
                    # files are not updated but the rest of the fields are
                    for item in request.data["upload_file"]:
                        del item["file_path"]
                        upload_file_uc = UploadFileUsageContract.objects.get(
                            pk=item["id_upload_file_usage_contract"]
                        )
                        serializer = UploadFileUsageContractSerializer(
                            upload_file_uc, item, partial=True
                        )
                        serializer.is_valid(raise_exception=True)
                        serializer.save()

                    upload_file_usage_contract_ids = [
                        x["id_upload_file_usage_contract"]
                        for x in request.data["upload_file"]
                    ]

                    files = UploadFileUsageContract.objects.filter(
                        id_upload_file_usage_contract__in=upload_file_usage_contract_ids
                    )
                    serializer = UploadFileUsageContractSerializer(files, many=True)
                    usage_contract.upload_file.set(files)
                    usage_contract.save()

                    del request.data["upload_file"]

                if "justification" in request.data:
                    _company_id = usage_contract.company_id

                    # Try to enable usage contratc
                    if "N" in _status:

                        _gauge = GaugePoint.objects.filter(id_company=_company_id)
                        if "S" in _gauge[0].status:

                            usage_contract.status = request.data["status"]
                            usage_contract.save()

                            _log_ctu = Log.objects.filter(
                                field_pk=usage_contract.id_usage_contract,
                                table_name="USAGE_CONTRACT",
                            ).order_by("-date")
                            if len(_log_ctu) > 0:

                                _log_ctu = _log_ctu[0]
                                _old = _log_ctu.new_value

                                if "'status': 'S'" in _old:
                                    _str_new = _old.replace(
                                        "'status': 'S'", "'status': 'N'"
                                    )
                                else:
                                    _str_new = _old.replace(
                                        "'status': 'N'", "'status': 'S'"
                                    )

                                _username = (
                                    request.auth["cn"]
                                    + " - "
                                    + request.auth["UserFullName"]
                                )

                                _new_log = Log()
                                _new_log.field_pk = _log_ctu.field_pk
                                _new_log.table_name = _log_ctu.table_name
                                _new_log.action_type = "UPDATE"
                                _new_log.old_value = _old
                                _new_log.new_value = _str_new
                                _new_log.user = _username
                                _new_log.date = timezone.now()
                                _new_log.observation = request.data["justification"]
                                _new_log.save()

                                return Response(status=status.HTTP_200_OK)
                        else:
                            resp = {
                                "msg": translate_label(
                                    "error_ctu_update_gauge", request
                                )
                            }
                            return Response(resp, status=status.HTTP_400_BAD_REQUEST)

                    # Try to disable usage contratc
                    if "S" in _status:

                        error = False

                        _budgets = return_linked_budgets(usage_contract)
                        _gauges = return_linked_gauges(usage_contract)

                        if len(_budgets) > 0 or len(_gauges) > 0:
                            error = True

                        if not error:
                            usage_contract.status = request.data["status"]
                            usage_contract.save()

                            _log_ctu = Log.objects.filter(
                                field_pk=usage_contract.id_usage_contract,
                                table_name="USAGE_CONTRACT",
                            ).order_by("-date")
                            if len(_log_ctu) > 0:
                                _log_ctu = _log_ctu[0]
                                _old = _log_ctu.new_value

                                if "'status': 'S'" in _old:
                                    _str_new = _old.replace(
                                        "'status': 'S'", "'status': 'N'"
                                    )
                                else:
                                    _str_new = _old.replace(
                                        "'status': 'N'", "'status': 'S'"
                                    )

                                _username = (
                                    request.auth["cn"]
                                    + " - "
                                    + request.auth["UserFullName"]
                                )

                                _new_log = Log()
                                _new_log.field_pk = _log_ctu.field_pk
                                _new_log.table_name = _log_ctu.table_name
                                _new_log.action_type = "UPDATE"
                                _new_log.old_value = _old
                                _new_log.new_value = _str_new
                                _new_log.user = _username
                                _new_log.date = timezone.now()
                                _new_log.observation = request.data["justification"]
                                _new_log.save()

                            return Response(status=status.HTTP_200_OK)
                        else:
                            resp = {
                                "msg": generate_delete_msg(_budgets, _gauges, request)
                                + "."
                            }
                            return Response(resp, status=status.HTTP_400_BAD_REQUEST)
                else:
                    partial = kwargs.pop("partial", False)
                    instance = self.get_object()
                    serializer = self.choose_serialize(request)

                    if "peak_begin_time" in request.data:
                        if request.data["peak_begin_time"] == "":
                            request.data["peak_begin_time"] = None

                    if "peak_end_time" in request.data:
                        if request.data["peak_end_time"] == "":
                            request.data["peak_end_time"] = None

                    if request.data["energy_transmitter"] is not None:
                        if "aneel_publication" in request.data["energy_transmitter"]:
                            if (
                                request.data["energy_transmitter"]["aneel_publication"]
                                == ""
                            ):
                                request.data["energy_transmitter"][
                                    "aneel_publication"
                                ] = None

                        if "cct" in request.data["energy_transmitter"]:
                            cct_list = request.data["energy_transmitter"]["cct"]
                            for _cct in cct_list:
                                if _cct["end_date"] == "":
                                    _cct["end_date"] = None

                        audit_renovation = request.data["energy_transmitter"].get(
                            "audit_renovation"
                        )
                        if not audit_renovation:
                            request.data["energy_transmitter"]["audit_renovation"] = "N"
                            request.data["energy_transmitter"]["renovation_period"] = 0

                        if (
                            request.data["energy_transmitter"]["renovation_period"]
                            == ""
                        ):
                            request.data["energy_transmitter"][
                                "renovation_period"
                            ] = None

                    if request.data["energy_distributor"] is not None:

                        if "aneel_publication" in request.data["energy_distributor"]:
                            if (
                                request.data["energy_distributor"]["aneel_publication"]
                                == ""
                            ):
                                request.data["energy_distributor"][
                                    "aneel_publication"
                                ] = None

                        if request.data["energy_distributor"]["audit_renovation"] == "":
                            request.data["energy_distributor"]["audit_renovation"] = "N"
                            request.data["energy_distributor"]["renovation_period"] = 0

                        if (
                            request.data["energy_distributor"]["audit_renovation"]
                            is None
                        ):
                            request.data["energy_distributor"]["audit_renovation"] = "N"
                            request.data["energy_distributor"]["renovation_period"] = 0

                        if (
                            request.data["energy_distributor"]["renovation_period"]
                            == ""
                        ):
                            request.data["energy_distributor"][
                                "renovation_period"
                            ] = None

                    _username = (
                        request.auth["cn"] + " - " + request.auth["UserFullName"]
                    )
                    context = {"username": _username}

                    serializer = serializer(
                        instance, data=request.data, partial=partial, context=context
                    )
                    serializer.is_valid(raise_exception=True)
                    self.perform_update(serializer)

                    if getattr(instance, "_prefetched_objects_cache", None):
                        # If 'prefetch_related' has been applied to a queryset, we need to
                        # forcibly invalidate the prefetch cache on the instance.
                        instance._prefetched_objects_cache = {}

                    return Response(serializer.data)

        except Exception as e:
            print(e.args)
            resp = {
                "error": translate_label("error_ctu_update", request),
                "msg": e.args,
            }
            return Response(resp, status=status.HTTP_400_BAD_REQUEST)

    def perform_update(self, serializer):
        serializer.save()

    def partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)

    @action(methods=["get"], detail=False)
    def export_file(self, request, *args, **kwargs):

        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        file_type = request.query_params['type_file']
        output_file = translate_label(
            'field_ctu_output_file', request) + '.' + file_type

        if file_type == 'xlsx':
            bio = BytesIO()
            writer = ExcelWriter(bio,engine='xlsxwriter')
            ctu_parser = CTUParser()
            df = ctu_parser.generate_data_frame(serializer.data, request, get_language(request))
            df.to_excel(writer, startrow= 2, header = False,index=False)
            workbook  = writer.book
            ws = writer.sheets[next(iter(writer.sheets))]
            ws.insert_image('A1', 'uploads/images/vale.png')
            ws.set_row(0, 48)
            header_format = workbook.add_format({
                'bold': True,
                'text_wrap': False,
                'valign': 'top',
                'fg_color': '#007E7A',
                'color': "#ffffff"})
            for col_num, value in enumerate(df.columns.values):
                ws.write(1, col_num, value, header_format)
            writer.save()
            bio.seek(0)
            excelFile = bio.read()

            response = HttpResponse(
                excelFile, content_type="application/excel; charset=utf-8-sig"
            )
            response["Content-Disposition"] = f'attachment; filename="{output_file}"'
            return response

        else:
            ctu_parser = CTUParser()
            pdf_file = ctu_parser.generate_pdf(serializer.data, request)
            response = HttpResponse(pdf_file)
            response['Content-Type'] = 'application/pdf'
            response['Content-disposition'] = 'attachment;filename={}'.format(output_file)
            return response


class UploadFileUsageContractFilter(filters.FilterSet):
    id_usage_contract = filters.ModelChoiceFilter(queryset=UsageContract.objects.all())

    class Meta:
        model = UploadFileUsageContract
        fields = [
            "id_usage_contract",
        ]


class UploadFileUsageContractViewSet(viewsets.ModelViewSet):

    queryset = UploadFileUsageContract.objects.all()
    serializer_class = UploadFileUsageContractSerializer
    pagination_class = StandardResultsSetPagination
    filterset_class = UploadFileUsageContractFilter

    def create(self, request, *args, **kwargs):
        try:
            headers = None
            if request.data.getlist("file_path").__len__() > 1:
                serializer = None
                list_file_path = request.data.getlist("file_path")
                for __file_path in list_file_path:
                    del request.data["file_path"]
                    request.data.update({"file_path": __file_path})
                    serializer = self.get_serializer(data=request.data)
                    serializer.is_valid(raise_exception=True)
                    self.perform_create(serializer)
                    headers = self.get_success_headers(serializer.data)
                return Response(
                    serializer.data, status=status.HTTP_201_CREATED, headers=headers
                )
            else:
                serializer = self.get_serializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                self.perform_create(serializer)
                headers = self.get_success_headers(serializer.data)
                return Response(
                    serializer.data, status=status.HTTP_201_CREATED, headers=headers
                )

        except Exception as e:
            print(e.args)
            resp = {
                "error": translate_label("error_ctu_upload", request),
                "msg": e.args,
            }
            return Response(resp, status=status.HTTP_400_BAD_REQUEST)

    def perform_create(self, serializer):
        serializer.save()

    def get_success_headers(self, data):
        try:
            return {"Location": str(data[api_settings.URL_FIELD_NAME])}
        except (TypeError, KeyError):
            return {}

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)

        resp = {"error": translate_label("error_ctu_upload_delete", request)}
        return Response(resp, status=status.HTTP_204_NO_CONTENT)

    def perform_destroy(self, instance):
        instance.delete()


@api_view(["GET"])
def session_log(request, pk):

    _log_tm = []
    _log_cc = []
    _log_cct = []
    _log_rpe = []

    dic_data = {}
    dic_counts = {}

    try:
        _json = CTUJson(pk)

        list_ctu = []
        _log_ctu = Log.objects.filter(
            field_pk=pk, table_name="USAGE_CONTRACT"
        ).order_by("-date")
        dic_counts["USAGE_CONTRACT"] = {
            "total": len(_log_ctu),
            "values": _log_ctu[0].new_value,
        }
        for _log in _log_ctu:
            _json.set_model_object("LOG", _log)
            list_ctu.append(_json.get_dic_log())
        dic_data["USAGE_CONTRACT"] = list_ctu

        _rpe_list = RatePostException.objects.filter(id_usage_contract=pk)
        if len(_rpe_list) > 0:

            _rpe_list_data = []
            _rpe_list_count = []

            for _rpe in _rpe_list:
                _log_rpe_list = Log.objects.filter(
                    field_pk=_rpe.id_rate_post_exception,
                    table_name="RATE_POST_EXCEPTION",
                ).order_by("-date")
                _dic_rpe = {
                    "total": len(_log_rpe_list),
                    "values": _log_rpe_list[0].new_value,
                }
                _rpe_list_count.append(_dic_rpe)

                for _log in _log_rpe_list:
                    _json.set_model_object("LOG", _log)
                    _rpe_list_data.append(_json.get_dic_log())

            dic_data["RATE_POST_EXCEPTION"] = _rpe_list_data
            dic_counts["RATE_POST_EXCEPTION"] = _rpe_list_count

        _tax_list = TaxModality.objects.filter(id_usage_contract=pk)
        if len(_tax_list) > 0:

            _tax_list_data = []
            _tax_list_count = []
            for _tax in _tax_list:
                _log_tax_list = Log.objects.filter(
                    field_pk=_tax.id_tax_modality, table_name="TAX_MODALITY"
                ).order_by("-date")
                _dic_tax = {
                    "total": len(_log_tax_list),
                    "values": _log_tax_list[0].new_value,
                }
                _tax_list_count.append(_dic_tax)

                for _log in _log_tax_list:
                    _json.set_model_object("LOG", _log)
                    _tax_list_data.append(_json.get_dic_log())

            dic_data["TAX_MODALITY"] = _tax_list_data
            dic_counts["TAX_MODALITY"] = _tax_list_count

        _cc_list = ContractCycles.objects.filter(id_usage_contract=pk)
        if len(_cc_list) > 0:

            cc_list_data = []
            cc_list_count = []
            for _cc in _cc_list:

                _log_cc_list = Log.objects.filter(
                    field_pk=_cc.id_contract_cycles, table_name="CONTRACT_CYCLES"
                ).order_by("-date")
                _dic_cc = {
                    "total": len(_log_cc_list),
                    "values": _log_cc_list[0].new_value,
                }
                cc_list_count.append(_dic_cc)

                for _log in _log_cc_list:
                    _json.set_model_object("LOG", _log)
                    cc_list_data.append(_json.get_dic_log())

            dic_data["CONTRACT_CYCLES"] = cc_list_data
            dic_counts["CONTRACT_CYCLES"] = cc_list_count

        _cct_list = Cct.objects.filter(id_usage_contract=pk)
        if len(_cct_list) > 0:

            cct_list_data = []
            cct_list_count = []
            for _cct in _cct_list:
                _log_cct_list = Log.objects.filter(
                    field_pk=_cct.id_cct, table_name="CCT"
                ).order_by("-date")
                _dic_cct = {
                    "total": len(_log_cct_list),
                    "values": _log_cct_list[0].new_value,
                }
                cct_list_count.append(_dic_cct)

                for _log in _log_cct_list:
                    _json.set_model_object("LOG", _log)
                    cct_list_data.append(_json.get_dic_log())

            dic_data["CCT"] = cct_list_data
            dic_counts["CCT"] = cct_list_count

        dic_response = {"counts": dic_counts}
        dic_response.update(dic_data)

        return Response(dic_response)

    except Exception as e:
        print(e.args)
        resp = {"error": translate_label("error_ctu_log", request), "msg": e.args}
        return Response(resp, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
def renovacao(request, _pk):
    _ctu = UsageContract.objects.filter(pk=_pk)
    if len(_ctu) > 0:

        if hasattr(_ctu[0], "energy_transmitter"):
            if _ctu[0].energy_transmitter is not None:
                dic = {"usage_contract": _pk, "status": "invalid"}
                return Response(dic, status=status.HTTP_200_OK)
        else:
            if "N" in _ctu[0].energy_distributor.audit_renovation:
                dic = {"usage_contract": _pk, "status": "not_renovable"}
                return Response(dic, status=status.HTTP_200_OK)
            else:
                _end_date = _ctu[0].end_date
                _perild_renovation = date.today() + relativedelta(days=+180)
                _interval_of_renovation = (_perild_renovation - _end_date).days

                # if the renovation date was passed
                if _interval_of_renovation >= 0:

                    mouths = _ctu[0].energy_distributor.renovation_period
                    _new_date = _end_date + relativedelta(months=+int(mouths))
                    _ctu[0].end_date = _new_date
                    _ctu[0].save()

                    _tax = TaxModality.objects.filter(id_usage_contract=_pk).order_by(
                        "-end_date"
                    )
                    if len(_tax) > 0:
                        _tax[0].end_date = _new_date
                        _tax[0].save()

                    print("Contrato de uso atualizado")
                    dic = {
                        "usage_contract": _pk,
                        "status": "new_date",
                        "date": _new_date.strftime("%d/%m/%Y"),
                    }
                    return Response(dic, status=status.HTTP_200_OK)
                else:
                    print("Contrato de uso não precisa ser atualizado")
                    dic = {
                        "usage_contract": _pk,
                        "status": "same_date",
                        "date": _end_date.strftime("%d/%m/%Y"),
                    }
                    return Response(dic, status=status.HTTP_200_OK)
    else:
        dic = {"usage_contract": _pk, "status": "invalid"}
        return Response(dic, status=status.HTTP_200_OK)


@api_view(["GET"])
def download_file(request, _pk):

    _download_file = UploadFileUsageContract.objects.filter(pk=_pk)
    if len(_download_file) > 0:
        try:

            _file_path = _download_file[0].file_path.path
            _file_name, file_ext = os.path.splitext(_file_path)
            if os.path.exists(_file_path):

                with open(_file_path, "rb") as file:
                    _file = file.read()

                response = None
                if ".pdf" in file_ext:
                    response = FileResponse(
                        open(_file_path, "rb"), content_type="application/pdf"
                    )
                    response["Content-Disposition"] = "filename={}".format(_file_name)
                return response
            else:
                resp = {"error": translate_label("error_ctu_find", request)}
                return Response(resp, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            print(e.args)
            resp = {
                "error": translate_label("error_ctu_download", request),
                "msg": e.args,
            }
            return Response(resp, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
def check_ctu_number(request, _number, _ctu_id=None):
    # remove whitespaces and do lowercase
    if _number:
        _number = str(_number).replace(" ", "").lower()

    _ctu = UsageContract.objects.extra(
        where=[f"LOWER(REPLACE(contract_number,' ','')) = '{_number}'"]
    )

    if _ctu_id is not None:
        get_object_or_404(UsageContract, pk=_ctu_id)
        _ctu = _ctu.exclude(id_usage_contract=_ctu_id)

    if not _ctu:
        return Response({"ctu_number_exist": False}, status=status.HTTP_200_OK)
    else:
        usage_contract = _ctu.first()
        if usage_contract.status == "S":
            return Response(
                {"ctu_number_exist": True, "active": True}, status=status.HTTP_200_OK
            )
        else:
            return Response(
                {"ctu_number_exist": True, "active": False}, status=status.HTTP_200_OK
            )


@api_view(["GET"])
def get_contract_number(request, company_id):
    contract = (
        UsageContract.objects.filter(company_id=company_id, status="S")
        .order_by("end_date")
        .last()
    )
    if contract:
        return Response(
            {
                "id_usage_contract": contract.pk,
                "contract_number": contract.contract_number,
            }
        )
    else:
        return Response(
            ["Não há contrato valido para esta empresa"],
            status=status.HTTP_204_NO_CONTENT,
        )

@api_view(['PUT'])
@check_module(modules.usage_contract, [permissions.EDITN1])
def renew_expired_contracts(request):
    reference_expired_offset = date.today() - relativedelta(days=180)

    expired_contracts: List[UsageContract] = UsageContract.objects.filter(
        status='S', 
        end_date__lt=reference_expired_offset,
        energy_transmitter__audit_renovation = "S")

    result = {'updateds': [], 'not_updateds': []}

    for expired_contract in expired_contracts:
        try:
            end_date = expired_contract.end_date
            new_end_date = end_date + relativedelta(months=expired_contract.energy_transmitter.renovation_period)
            if new_end_date <= date.today():
                new_end_date = date.today()
            expired_contract.end_date = new_end_date
            expired_contract.save()

            try:
                last_log: Log = Log.objects.filter(field_pk=expired_contract.pk, table_name='USAGE_CONTRACT').order_by('-date').last()
                new_value_log =  json.loads(str.replace(last_log.new_value, "'", '"'))
                new_value_log['end_date'] = new_end_date.strftime("%d/%m/%Y")

                log_entry = Log()
                log_entry.field_pk = expired_contract.pk
                log_entry.table_name = "USAGE_CONTRACT"
                log_entry.action_type = "UPDATE"
                log_entry.old_value = last_log.new_value
                log_entry.new_value = str.replace(str(new_value_log), ": None", ": null")
                log_entry.user = "SYSTEM"
                log_entry.date = timezone.now()
                log_entry.observation = "Automatic renovation"
                log_entry.save()
            except:
                pass  
            result['updateds'].append(expired_contract.pk)
        except Exception as ex:
            logging.error(f"Error while update usage contract id: {expired_contract.pk}", exc_info=sys.exc_info())
            result['not_updateds'].append({
                "id_usage_contract": expired_contract.pk, 
                "error": "error_while_update", 
                "message": str(ex)})

    return Response(result)