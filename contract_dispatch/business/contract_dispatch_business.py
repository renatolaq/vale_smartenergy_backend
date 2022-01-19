from builtins import ValueError
import ast
from copy import copy
from django.core.exceptions import ObjectDoesNotExist

from asset_items.models import AssetItems
from assets.models import Assets, Submarket

from django.db.models.functions import TruncMonth, ExtractYear, ExtractMonth
from contract_dispatch.utils import (
    display_as_str,
    get_index_by_dict_list,
    get_query_params_as_dict,
    translate_field_name,
    execute_filter,
    filter_month_queryset,
    get_field_names,
    is_future_contract,
    retrieve_month,
    translate_field,
)

from energy_contract.models import EnergyContract
from locales.translates_function import translate_label

from contract_dispatch.models import (
    ContractDispatchCategory,
    ContractDispatchOperation,
    CliqContractStatus,
    ContractDispatchCliqContract,
    CliqContractCurrentStatus,
    CliqContract,
)
from django.db.models import (
    Q,
    When,
    Case,
    Value,
    CharField,
    DecimalField,
    BooleanField,
    F,
    OuterRef,
    Subquery,
)
from contract_dispatch.business.contract_dispatch_lib import (
    fields,
    fields_to_show,
    contracts_to_send_fields_to_show,
    translation_dict,
    translation_normal_fields,
    translation_month_fields,
    contract_cliq_translation_dict,
    contract_cliq_translation_normal_fields,
    contract_to_send_translation_normal_fields,
)

from core.models import Log as CoreLog, CceeDescription
from profiles.models import Profile


from balance_report_market_settlement.models import DetailedBalance
from core.models import Seasonality
from datetime import date
from enumchoicefield import EnumChoiceField
from rest_framework.response import Response
from rest_framework import status
from core.views import generic_paginator


class ContractDispatchBusiness:
    @staticmethod
    def retrieve_contracts_dict_list_by_month(request):
        cliq_contracts = CliqContract.objects.filter(contract_dispatches__isnull=False)
        cliq_contracts = ContractDispatchBusiness.contract_cliq_queryset_set_values(
            cliq_contracts
        )
        cliq_contracts = ContractDispatchBusiness.contract_cliq_queryset_annotate_values(
            cliq_contracts
        )
        cliq_contracts = ContractDispatchBusiness.contract_cliq_queryset_annotate_current_status(
            cliq_contracts
        )
        cliq_contracts = ContractDispatchBusiness.cliq_contract_annotate_category(
            cliq_contracts
        )
        cliq_contracts = ContractDispatchBusiness.contract_cliq_queryset_annotate_operation(
            cliq_contracts
        )
        cliq_contracts = ContractDispatchBusiness.contract_cliq_queryset_add_order_by(
            cliq_contracts
        )

        cliq_contracts = ContractDispatchBusiness.contract_dispatch_set_filter(
            request, cliq_contracts
        )

        result = ContractDispatchBusiness.generate_contract_list_dict(
            cliq_contracts, request
        )

        return result

    @staticmethod
    def retrieve_contracts_by_contract_dispatch(
        request, contract_dispatch, set_values=False
    ):
        cliq_contracts = contract_dispatch.contracts
        if set_values == True:
            cliq_contracts = ContractDispatchBusiness.contract_cliq_queryset_set_values(
                cliq_contracts
            )

        cliq_contracts = ContractDispatchBusiness.contract_cliq_queryset_annotate_values(
            cliq_contracts
        )

        cliq_contracts = ContractDispatchBusiness.contract_cliq_queryset_annotate_current_status(
            cliq_contracts
        )
        cliq_contracts = ContractDispatchBusiness.cliq_contract_annotate_category(
            cliq_contracts
        )
        cliq_contracts = ContractDispatchBusiness.contract_cliq_queryset_annotate_operation(
            cliq_contracts
        )
        cliq_contracts = ContractDispatchBusiness.contract_dispatch_queryset_annotate_volume_final(
            cliq_contracts, contract_dispatch.pk
        )

        cliq_contracts = ContractDispatchBusiness.contract_cliq_set_filter(
            request, cliq_contracts
        )

        return cliq_contracts

    @staticmethod
    def retrieve_contracts_dict_list_by_contract_dispatch(request, contract_dispatch):
        cliq_contracts = ContractDispatchBusiness.retrieve_contracts_by_contract_dispatch(
            request, contract_dispatch, True
        )

        result = ContractDispatchBusiness.generate_contract_list_dict(
            cliq_contracts, request
        )

        return result

    @staticmethod
    def retrieve_contracts_to_send(request, year, month, balance_id, ids=None):
        cliq_contracts = CliqContract.objects.filter(status__iexact="S")

        if ids != None:
            cliq_contracts = cliq_contracts.filter(pk__in=ids)

        cliq_contracts = ContractDispatchBusiness.contract_cliq_annotate_status_val(
            cliq_contracts, year, month
        )
        cliq_contracts = ContractDispatchBusiness.cliq_contract_annotate_category(
            cliq_contracts
        )
        cliq_contracts = ContractDispatchBusiness.contract_cliq_queryset_annotate_availability(
            cliq_contracts
        )
        cliq_contracts = ContractDispatchBusiness.contract_dispatch_annotate_operation(
            cliq_contracts
        )
        cliq_contracts = ContractDispatchBusiness.contract_cliq_queryset_annotate_volume_on_register(
            cliq_contracts
        )
        cliq_contracts = ContractDispatchBusiness.contract_cliq_queryset_annotate_volume_on_seasonality(
            cliq_contracts, month
        )
        cliq_contracts = ContractDispatchBusiness.contract_cliq_queryset_annotate_future_contract_volume(
            cliq_contracts, year, month
        )
        cliq_contracts = ContractDispatchBusiness.contract_cliq_queryset_annotate_volume_on_balance(
            cliq_contracts, balance_id
        )
        cliq_contracts = ContractDispatchBusiness.contract_cliq_queryset_annotate_volume_final(
            cliq_contracts, balance_id
        )

        cliq_contracts = ContractDispatchBusiness.filter_has_variancy(
            cliq_contracts,
            request.query_params.get("has_variancy"),
            date(day=1, month=month, year=year),
        )

        try:
            request_date = date(year, month, 1)

            cliq_contracts = cliq_contracts.filter(
                id_contract__start_supply__date__lte=request_date,
                id_contract__end_supply__date__gte=request_date,
            )

            cliq_contracts = ContractDispatchBusiness.contracts_to_send_set_filter(
                request, cliq_contracts
            )
        except ValueError as e:
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)

        return cliq_contracts

    @staticmethod
    def filter_has_variancy(contracts, check_has_variancy, date):
        if check_has_variancy == None:
            return contracts

        has_variancy_query_filter = Q(
            Q(cliqcontractcceestate__isnull=False),
            Q(operation__isnull=False),
            Q(
                operation__in=[
                    ContractDispatchOperation.VALIDATE_REGISTER.value,
                    ContractDispatchOperation.ADJUSTMENT.value,
                    ContractDispatchOperation.VALIDATE_ADJUSTMENT.value,
                ]
            ),
            Q(
                ~Q(cliqcontractcceestate__buyer_agent=F("id_buyer_profile__id_agents"))
                | ~Q(
                    cliqcontractcceestate__seller_agent=F(
                        "id_vendor_profile__id_agents"
                    )
                )
                | ~Q(cliqcontractcceestate__submarket=F("id_submarket"))
                | Q(
                    Q(cliqcontractcceestate__cliqcontractcceeperiodinfo__date=date),
                    ~Q(
                        volume_final=F(
                            "cliqcontractcceestate__cliqcontractcceeperiodinfo__volume"
                        )
                    ),
                )
            ),
        )

        if check_has_variancy == "true":
            contracts = contracts.filter(has_variancy_query_filter)
        else:
            contracts = contracts.exclude(has_variancy_query_filter)

        return contracts

    @staticmethod
    def retrieve_contracts_dict_list_contracts_to_send(
        request, year, month, balance_id=None, ids=None
    ):
        cliq_contracts = ContractDispatchBusiness.retrieve_contracts_to_send(
            request, year, month, balance_id, ids
        )

        cliq_contracts = ContractDispatchBusiness.contracts_to_send_queryset_set_values(
            cliq_contracts
        )

        result = ContractDispatchBusiness.generate_contract_to_send_list_dict(
            cliq_contracts, request
        )

        return result

    @staticmethod
    def retrieve_contracts_dict_list_by_contract_cliq_ids(
        request, year, month, balance_id, cliq_contract_ids
    ):
        result = ContractDispatchBusiness.retrieve_contracts_dict_list_contracts_to_send(
            request, year, month, balance_id, cliq_contract_ids
        )

        return result

    @staticmethod
    def generate_contract_list_dict(cliq_contracts, request):
        if cliq_contracts == None:
            return []

        result = []
        translated_fields = ContractDispatchBusiness.get_translated_fields(request)

        # add pagination
        data, page_count, page_next, page_previous = generic_paginator(
            request, list(cliq_contracts)
        )

        for cliq_contract in data.object_list:
            year_month = cliq_contract.get("year_month")

            if year_month != None:
                date_month = year_month.strftime("%Y/%m")
                title = translate_label("contract_dispatch_title_info", request)
                title = title.replace("{date}", date_month)
            else:
                title = ""

            current_index = get_index_by_dict_list(result, "title", title)

            contract_dict = {"values": []}

            for field in fields_to_show:
                db_value = cliq_contract.get(field, None)
                translated_field = translate_field(request, field, db_value)

                display_value = (
                    translated_field
                    if translated_field != ""
                    else display_as_str(db_value)
                )
                contract_dict["values"].append(display_value)

            if current_index != None:
                result[current_index]["contracts"].append(contract_dict)
            else:
                result.append(
                    {
                        "title": title,
                        "contracts": [contract_dict,],
                        "fields": translated_fields,
                    }
                )

        return result

    @staticmethod
    def generate_contract_to_send_list_dict(cliq_contracts, request):
        if cliq_contracts == None:
            return []

        result = []
        translated_fields = ContractDispatchBusiness.get_translated_fields(
            request, contracts_to_send_fields_to_show
        )

        title = translate_label("contract_dispatch_title", request)

        result.append(
            {"title": title, "contracts": [], "fields": translated_fields,}
        )

        # add pagination
        data, page_count, page_next, page_previous = generic_paginator(
            request, list(cliq_contracts)
        )

        for cliq_contract in data.object_list:

            contract_dict = {"values": []}
            for field in contracts_to_send_fields_to_show:
                db_value = cliq_contract.get(field, None)
                translated_field = translate_field(request, field, db_value)

                display_value = (
                    translated_field
                    if translated_field != ""
                    else display_as_str(db_value)
                )
                contract_dict["values"].append(display_value)

            result[0]["contracts"].append(contract_dict)

        return result

    @staticmethod
    def get_translated_fields(request, display_fields=fields_to_show):
        result = []

        for field in display_fields:
            translated_field = translate_label(f"contract_dispatch_{field}", request)
            result.append(
                {
                    "value": field,
                    "name": field if translated_field == None else translated_field,
                }
            )

        return result

    @staticmethod
    def contract_dispatch_annotate_operation(queryset):
        return queryset.annotate(
            operation=Case(
                When(
                    Q(status_val__isnull=True)
                    | Q(status_val=CliqContractStatus.CANCELED)
                    | Q(status_val=CliqContractStatus.NOT_SENT),
                    then=Value(ContractDispatchOperation.REGISTER.value),
                ),
                When(
                    Q(status_val=CliqContractStatus.REGISTERED_NOT_VALIDATED),
                    then=Value(ContractDispatchOperation.VALIDATE_REGISTER.value),
                ),
                When(
                    Q(status_val=CliqContractStatus.REGISTERED_VALIDATED),
                    then=Value(ContractDispatchOperation.ADJUSTMENT.value),
                ),
                When(
                    Q(status_val=CliqContractStatus.ADJUSTED_NOT_VALIDATED),
                    then=Value(ContractDispatchOperation.VALIDATE_ADJUSTMENT.value),
                ),
                default=Value(None),
                output_field=CharField(),
            )
        )

    @staticmethod
    def cliq_contract_annotate_category(queryset):
        return queryset.annotate(
            category=Case(
                When(
                    id_contract__modality__iexact="Transferencia",
                    then=Value(ContractDispatchCategory.TRANSFER.value),
                ),
                When(
                    id_contract__type__iexact="C",
                    then=Value(ContractDispatchCategory.PURCHASE.value),
                ),
                When(
                    id_contract__type__iexact="V",
                    then=Value(ContractDispatchCategory.SALE.value),
                ),
                default=Value(None),
                output_field=CharField(),
            )
        )

    @staticmethod
    def contract_cliq_annotate_status_val(queryset, year, month):
        cliq_contract_current_status = CliqContractCurrentStatus.objects.filter(
            cliq_contract=OuterRef("pk"),
            status_date__month=month,
            status_date__year=year,
        )

        subquery = Subquery(cliq_contract_current_status.values("status")[:1])

        new_queryset = queryset.annotate(temp_status_val=subquery)

        new_queryset = new_queryset.annotate(
            status_val=Case(
                When(
                    (Q(temp_status_val__isnull=True) & ~Q(id_ccee__code_ccee="")),
                    then=Value(CliqContractStatus.WAITING_CCEE.name),
                ),
                When(
                    Q(temp_status_val__isnull=True),
                    then=Value(CliqContractStatus.NOT_SENT.name),
                ),
                default=F("temp_status_val"),
                output_field=EnumChoiceField(CliqContractStatus),
            )
        )

        return new_queryset

    @staticmethod
    def contract_cliq_queryset_set_values(queryset):
        new_queryset = queryset.values(
            *fields, "contract_dispatches__contract_status_on_dispatch", "pk",
        )

        return new_queryset

    @staticmethod
    def contract_cliq_queryset_annotate_values(queryset):
        new_queryset = queryset.annotate(
            year=ExtractYear("contract_dispatches__contract_dispatch__supply_date"),
            month=ExtractMonth("contract_dispatches__contract_dispatch__supply_date"),
            year_month=TruncMonth(
                "contract_dispatches__contract_dispatch__dispatch_date"
            ),
        )

        return new_queryset

    @staticmethod
    def contracts_to_send_queryset_set_values(queryset):
        new_queryset = queryset.values(
            *contracts_to_send_fields_to_show,
            "contract_dispatches__contract_status_on_dispatch",
            "pk",
        )

        return new_queryset

    @staticmethod
    def contract_cliq_queryset_annotate_current_status(queryset):
        cliq_contract_current_status = CliqContractCurrentStatus.objects.filter(
            cliq_contract=OuterRef("pk"),
            status_date__month=OuterRef("month"),
            status_date__year=OuterRef("year"),
        )

        new_queryset = queryset.annotate(
            status_val=Subquery(cliq_contract_current_status.values("status")[:1])
        )

        return new_queryset

    @staticmethod
    def contract_cliq_queryset_annotate_operation(queryset):
        new_queryset = queryset.annotate(
            operation=Case(
                When(
                    Q(contract_dispatches__contract_status_on_dispatch__isnull=True)
                    | Q(
                        contract_dispatches__contract_status_on_dispatch=CliqContractStatus.CANCELED
                    )
                    | Q(
                        contract_dispatches__contract_status_on_dispatch=CliqContractStatus.NOT_SENT
                    ),
                    then=Value(ContractDispatchOperation.REGISTER.value),
                ),
                When(
                    Q(
                        contract_dispatches__contract_status_on_dispatch=CliqContractStatus.REGISTERED_NOT_VALIDATED
                    ),
                    then=Value(ContractDispatchOperation.VALIDATE_REGISTER.value),
                ),
                When(
                    Q(
                        contract_dispatches__contract_status_on_dispatch=CliqContractStatus.REGISTERED_VALIDATED
                    ),
                    then=Value(ContractDispatchOperation.ADJUSTMENT.value),
                ),
                When(
                    Q(
                        contract_dispatches__contract_status_on_dispatch=CliqContractStatus.ADJUSTED_NOT_VALIDATED
                    ),
                    then=Value(ContractDispatchOperation.VALIDATE_ADJUSTMENT.value),
                ),
                default=Value(None),
                output_field=CharField(),
            )
        )

        return new_queryset

    @staticmethod
    def contract_cliq_queryset_add_order_by(queryset):
        new_queryset = queryset.order_by(
            "-contract_dispatches__contract_dispatch__dispatch_date"
        )

        return new_queryset

    @staticmethod
    def contract_dispatch_set_filter(request, queryset):
        fields_params = get_query_params_as_dict(
            request, get_field_names(translation_dict)
        )
        sort = request.query_params.get("sort")

        for param_name in translation_normal_fields:
            param_value = fields_params.get(param_name)

            queryset = execute_filter(
                translation_dict, param_name, param_value, CliqContractStatus, queryset,
            )

        for param_name in translation_month_fields:
            param_value = fields_params.get(param_name)

            if param_value is not None:
                queryset = filter_month_queryset(
                    translation_dict, param_name, queryset, param_value
                )

        if sort is not None:
            queryset = queryset.order_by(translate_field_name(translation_dict, sort))

        return queryset.distinct()

    @staticmethod
    def contract_cliq_set_filter(request, queryset):
        fields_params = get_query_params_as_dict(
            request, get_field_names(contract_cliq_translation_dict)
        )
        sort = request.query_params.get("sort")
        has_processment_errors = request.query_params.get("has_processment_errors")

        for param_name in contract_cliq_translation_normal_fields:
            param_value = fields_params.get(param_name)
            queryset = execute_filter(
                contract_cliq_translation_dict,
                param_name,
                param_value,
                CliqContractStatus,
                queryset,
            )

        if sort is not None:
            queryset = queryset.order_by(
                translate_field_name(contract_cliq_translation_dict, sort)
            )

        if has_processment_errors:
            error_query = Q(
                contract_dispatches__cliq_ccee_processment__processment_result__status="ERRO"
            )
            if has_processment_errors == "true":
                queryset = queryset.filter(error_query)
            else:
                queryset = queryset.filter(~error_query)

        return queryset.distinct()

    @staticmethod
    def contracts_to_send_set_filter(request, queryset):
        fields_params = get_query_params_as_dict(
            request, get_field_names(contract_to_send_translation_normal_fields)
        )
        sort = request.query_params.get("sort")

        for param_name in contract_to_send_translation_normal_fields:
            param_value = fields_params.get(param_name)
            queryset = execute_filter(
                contract_to_send_translation_normal_fields,
                param_name,
                param_value,
                CliqContractStatus,
                queryset,
            )

        if sort is not None:
            queryset = queryset.order_by(
                translate_field_name(contract_to_send_translation_normal_fields, sort)
            )

        return queryset.distinct()

    @staticmethod
    def contract_cliq_queryset_annotate_availability(queryset):
        new_queryset = queryset.annotate(
            available=Case(
                When(
                    Q(
                        Q(status_val__isnull=False)
                        & (
                            Q(status_val=CliqContractStatus.WAITING_CCEE)
                            | Q(status_val=CliqContractStatus.ADJUSTED_VALIDATED)
                        )
                        | (
                            Q(category=ContractDispatchCategory.PURCHASE.value)
                            & ~Q(status_val=CliqContractStatus.REGISTERED_NOT_VALIDATED)
                            & ~Q(status_val=CliqContractStatus.ADJUSTED_NOT_VALIDATED)
                        )
                        | (
                            Q(category=ContractDispatchCategory.SALE.value)
                            & Q(status_val__isnull=False)
                            & ~Q(status_val=CliqContractStatus.CANCELED)
                            & ~Q(status_val=CliqContractStatus.NOT_SENT)
                            & ~Q(status_val=CliqContractStatus.REGISTERED_VALIDATED)
                        )
                        | (
                            Q(category=ContractDispatchCategory.TRANSFER.value)
                            & Q(status_val__isnull=False)
                            & ~Q(status_val=CliqContractStatus.CANCELED)
                            & ~Q(status_val=CliqContractStatus.NOT_SENT)
                            & ~Q(status_val=CliqContractStatus.REGISTERED_VALIDATED)
                        )
                    ),
                    then=False,
                ),
                default=True,
                output_field=BooleanField(),
            )
        )

        return new_queryset

    @staticmethod
    def contract_cliq_queryset_annotate_volume_on_register(queryset):
        new_queryset = queryset.annotate(
            volume_on_register=Case(
                When(
                    Q(operation=ContractDispatchOperation.REGISTER.value), then=Value(0)
                ),
                default=Value(None),
                output_field=DecimalField(),
            )
        )

        return new_queryset

    @staticmethod
    def contract_cliq_queryset_annotate_volume_on_seasonality(queryset, month):
        seasonality = Seasonality.objects.filter(
            Q(
                Q(seasonalityCliq_seasonality__isnull=False)
                & Q(seasonalityCliq_seasonality__id_contract_cliq=OuterRef("pk"))
            )
        )
        new_queryset = queryset.annotate(
            volume_on_seasonality=Subquery(
                seasonality.values(retrieve_month(month))[:1]
            )
            * F("mwm_volume")
        )

        return new_queryset

    @staticmethod
    def contract_cliq_queryset_annotate_future_contract_volume(queryset, year, month):
        if is_future_contract(year, month):
            new_queryset = queryset.annotate(
                future_contract_volume=Case(
                    When(
                        Q(volume_on_seasonality__isnull=False),
                        then="volume_on_seasonality",
                    ),
                    default="mwm_volume",
                    output_field=DecimalField(),
                )
            )
        else:
            new_queryset = queryset.annotate(
                future_contract_volume=Value(None, DecimalField())
            )

        return new_queryset

    @staticmethod
    def contract_cliq_queryset_annotate_volume_on_balance(queryset, balance_id):
        if balance_id is not None:
            detailed_balance = DetailedBalance.objects.filter(
                id_balance__id_report=balance_id, id_balance__id_balance_type=2
            )
            detailed_balance = detailed_balance.filter(
                id_detailed_balance_type__id__in=[1, 2, 4]
            )
            detailed_balance = detailed_balance.filter(id_contract_cliq=OuterRef("pk"))
            new_queryset = queryset.annotate(
                volume_on_balance=Subquery(detailed_balance.values("volume")[:1])
            )
        else:
            new_queryset = queryset.annotate(
                volume_on_balance=Value(None, DecimalField())
            )

        return new_queryset

    @staticmethod
    def contract_dispatch_queryset_annotate_volume_final(
        queryset, contract_dispatch_id
    ):
        contract_dispatch_cliq_contract = ContractDispatchCliqContract.objects.filter(
            contract_dispatch__pk=contract_dispatch_id, cliq_contract=OuterRef("pk")
        )
        new_queryset = queryset.annotate(
            volume_final=Subquery(
                contract_dispatch_cliq_contract.values("volume_on_dispatch")[:1]
            )
        )

        return new_queryset

    @staticmethod
    def contract_cliq_queryset_annotate_volume_final(queryset, balance_id):
        if balance_id is not None:
            new_queryset = queryset.annotate(
                volume_final=Case(
                    When(
                        Q(volume_on_register__isnull=False), then="volume_on_register"
                    ),
                    When(
                        Q(future_contract_volume__isnull=False),
                        then="future_contract_volume",
                    ),
                    default="volume_on_balance",
                    output_field=DecimalField(),
                )
            )
        else:
            new_queryset = queryset.annotate(
                available=Case(
                    When(
                        ~Q(
                            id_contract__flexib_energy_contract__flexibility_type="Flat"
                        ),
                        then=False,
                    ),
                    default="available",
                    output_field=BooleanField(),
                )
            )

            new_queryset = new_queryset.annotate(
                volume_final=Case(
                    When(
                        Q(volume_on_register__isnull=False), then="volume_on_register"
                    ),
                    When(
                        Q(volume_on_seasonality__isnull=False),
                        then="volume_on_seasonality",
                    ),
                    default="mwm_volume",
                    output_field=DecimalField(),
                )
            )

        return new_queryset

    @staticmethod
    def retrieve_cliq_contract_last_log_by_contract(contract_obj):
        def get_or_none(model, **kwargs):
            try:
                return model.objects.get(**kwargs)
            except (model.DoesNotExist, ValueError):
                return None

        def build_cc_by_log(cc_log_dict):
            cc = CliqContract()

            cc.id_contract_cliq = cc_log_dict.get("id_contract_cliq")
            cc.id_vendor_profile = Profile.objects.get(
                pk=cc_log_dict["id_vendor_profile"]
            )
            cc.id_contract = EnergyContract.objects.get(
                id_contract=cc_log_dict["id_contract"]
            )
            cc.ccee_type_contract = cc_log_dict.get("ccee_type_contract")
            cc.transaction_type = cc_log_dict.get("ccee_transaction_type")
            cc.flexibility = cc_log_dict.get("flexibility")
            cc.mwm_volume = cc_log_dict.get("mwm_volume")
            cc.contractual_loss = cc_log_dict.get("contractual_loss")
            cc.status = cc_log_dict.get("status")

            cc.id_buyer_profile = get_or_none(
                Profile, pk=cc_log_dict.get("id_buyer_profile")
            )
            cc.id_ccee = get_or_none(
                CceeDescription, id_ccee=cc_log_dict.get("id_ccee")
            )
            cc.id_buyer_assets = get_or_none(
                Assets, id_assets=cc_log_dict.get("id_buyer_assets")
            )
            cc.id_buyer_asset_items = get_or_none(
                AssetItems, id_asset_items=cc_log_dict.get("id_buyer_asset_items")
            )
            cc.id_submarket = get_or_none(
                Submarket, id_submarket=cc_log_dict.get("id_submarket")
            )

            return cc

        def build_ccee_description_by_log(ccee_log_dict):
            ccee = CceeDescription(**ccee_log_dict)
            return ccee

        # returns none if contract status is none or not CANCELED
        if (
            contract_obj.status_val is None
            or contract_obj.status_val.value != CliqContractStatus.CANCELED.value
        ):
            return None

        # fetch last update log from cliq_contract
        try:
            cliq_contract_log = CoreLog.objects.filter(
                field_pk=contract_obj.pk,
                table_name="CLIQ_CONTRACT",
                action_type="UPDATE",
            ).latest("date")
        except (ObjectDoesNotExist):
            cliq_contract_log = None

        # fetch last update log from ccee_description
        try:
            ccee_description_log = CoreLog.objects.filter(
                field_pk=contract_obj.id_ccee_id,
                table_name="CCEE_DESCRIPTION",
                action_type="UPDATE",
            ).latest("date")
        except (ObjectDoesNotExist):
            ccee_description_log = None

        if cliq_contract_log is None and ccee_description_log:
            # if doesn't exist cc log but exists ccee_description_log so update current object with ccee_description_log
            ccee_description_last_version = build_ccee_description_by_log(
                ast.literal_eval(ccee_description_log.old_value)
            )
            cc_last_version = copy(contract_obj)
            cc_last_version.id_ccee = ccee_description_last_version
        elif cliq_contract_log and ccee_description_log is None:
            # if doesn't exist ccee_log but exists cc_log so build an object from cc_log info
            cc_last_version = build_cc_by_log(
                ast.literal_eval(cliq_contract_log.old_value)
            )
        elif cliq_contract_log and ccee_description_log:
            # if exists cc and ccee logs build a cc from cc_log and update id_ccee by building ccee_description log
            cc_last_version = build_cc_by_log(
                ast.literal_eval(cliq_contract_log.old_value)
            )
            ccee_description_last_version = build_ccee_description_by_log(
                ast.literal_eval(ccee_description_log.old_value)
            )
            cc_last_version.id_ccee = ccee_description_last_version
        else:
            # there is no update logs from both so it is
            cc_last_version = None

        return cc_last_version
