from contract_dispatch.utils import add_sort_fields

# global fields for pdf and xlsx generation
fields = [
    "contract_dispatches__contract_dispatch__dispatch_date",
    "contract_dispatches__contract_dispatch__last_status_update_date",
    "contract_dispatches__contract_dispatch__dispatch_username",
    "contract_dispatches__contract_dispatch__supply_date",
    "ccee_type_contract",
    "id_ccee__code_ccee",
    "id_contract__modality",
    "contract_dispatches__volume_on_dispatch",
    "id_contract__contract_name",
    "id_contract__id_buyer_agents__vale_name_agent",
    "id_buyer_profile__name_profile",
    "id_contract__id_seller_agents__vale_name_agent",
    "id_vendor_profile__name_profile",
    "id_contract__type",
]
unnrelated_fields = [
    "status_val",
    "category",
    "operation",
]
filter_fields = [
    "dispatch_date",
    "last_status_update_date",
    "dispatch_username",
    "supply_date",
    "sort",
]

fields_to_show = []
fields_to_show.extend(fields)
fields_to_show.extend(unnrelated_fields)

contracts_to_send_fields_to_show = []
contracts_to_send_fields_to_show.extend(fields_to_show)
contracts_to_send_fields_to_show.remove(
    "contract_dispatches__contract_dispatch__dispatch_date"
)
contracts_to_send_fields_to_show.remove(
    "contract_dispatches__contract_dispatch__last_status_update_date"
)
contracts_to_send_fields_to_show.remove(
    "contract_dispatches__contract_dispatch__dispatch_username"
)
contracts_to_send_fields_to_show.remove(
    "contract_dispatches__contract_dispatch__supply_date"
)
contracts_to_send_fields_to_show.remove("contract_dispatches__volume_on_dispatch")
contracts_to_send_fields_to_show.extend(["volume_final", "available"])

# contract dispatch filters
translation_normal_fields = {
    "user": ("contract_dispatches__contract_dispatch__dispatch_username", "icontains"),
    "sentDate": ("contract_dispatches__contract_dispatch__dispatch_date", "date"),
    "lastUpdateDate": (
        "contract_dispatches__contract_dispatch__last_status_update_date",
        "date",
    ),
}
translation_month_fields = {
    "supplyDate": "contract_dispatches__contract_dispatch__supply_date",
}

translation_dict = {}
translation_dict.update(translation_normal_fields)
translation_dict.update(translation_month_fields)
translation_dict = add_sort_fields(translation_dict)

# contract cliq filters
contract_cliq_translation_normal_fields = {
    "contractType": ("ccee_type_contract", "iexact"),
    "category": ("category", "iexact"),
    "operation": ("operation", "iexact"),
    "cliqCode": ("id_ccee__code_ccee", "icontains"),
    "modality": ("id_contract__modality", "icontains"),
    "name": ("id_contract__contract_name", "icontains"),
    "volume": ("contract_dispatches__volume_on_dispatch", "icontains"),
    "buyerAgent": ("id_contract__id_buyer_agents__vale_name_agent", "icontains"),
    "buyerProfile": ("id_buyer_profile__name_profile", "icontains"),
    "salesAgent": ("id_contract__id_seller_agents__vale_name_agent", "icontains"),
    "salesProfile": ("id_vendor_profile__name_profile", "icontains"),
    "status": ("status_val", "in"),
    "has_processment_errors": (
        "contract_dispatches__cliq_ccee_processment__processment_result__status",
        "iexact",
    ),
}
contract_to_send_translation_normal_fields = {
    "contractType": ("ccee_type_contract", "iexact"),
    "category": ("category", "iexact"),
    "operation": ("operation", "iexact"),
    "cliqCode": ("id_ccee__code_ccee", "icontains"),
    "modality": ("id_contract__modality", "icontains"),
    "name": ("id_contract__contract_name", "icontains"),
    "volume": ("volume_final", "iexact"),
    "buyerAgent": ("id_buyer_profile__id_agents__vale_name_agent", "icontains"),
    "buyerProfile": ("id_buyer_profile__name_profile", "icontains"),
    "salesAgent": ("id_vendor_profile__id_agents__vale_name_agent", "icontains"),
    "salesProfile": ("id_vendor_profile__name_profile", "icontains"),
    "status": ("status_val", "in"),
    "available": ("available", "boolean"),
}

# specified variables must be here (if needed)

contract_cliq_translation_dict = {}
contract_cliq_translation_dict.update(contract_cliq_translation_normal_fields)
contract_cliq_translation_dict = add_sort_fields(contract_cliq_translation_dict)
