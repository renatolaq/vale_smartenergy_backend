from datetime import date, datetime
from decimal import Decimal
from locales.translates_function import translate_label
import os
from django.db.models import Value
from rest_framework.exceptions import ValidationError
from distutils.util import strtobool
import pytz


def get_query_params(request, param_list):
    query_params = []
    for param in param_list:
        query_params.append(request.query_params.get(param))
    return query_params


def get_query_params_as_dict(request, param_list):
    query_params = {}
    for param in param_list:
        query_params[param] = request.query_params.get(param)
    return query_params


def translate_field_name(sort_translation_dict, sort_field_name):
    sortable_field_name = sort_translation_dict.get(sort_field_name)
    if sortable_field_name is None:
        raise ValidationError(
            {"detail": f"{sort_field_name} is not a valid sortable field"}
        )

    return (
        sortable_field_name
        if type(sortable_field_name) == str
        else sortable_field_name[0]
    )


def execute_filter(translation_dict, param_name, param_value, enum_class, queryset):
    if param_value is not None:
        if param_name == "status":
            queryset = filter_queryset_enum(enum_class, queryset, param_value)
        else:
            queryset = filter_queryset(
                translation_dict, param_name, queryset, param_value,
            )

    return queryset


def filter_queryset(translation_dict, field_name, queryset, value):
    query_field_name_tuple = translation_dict.get(field_name)
    query_field_name = query_field_name_tuple[0]
    operator = query_field_name_tuple[1]

    query_filter = (
        {query_field_name: bool(strtobool(value))}
        if operator == "boolean"
        else {f"{query_field_name}__{operator}": value}
    )
    new_queryset = queryset.filter(**query_filter)
    return new_queryset


def filter_queryset_enum(enum_class, queryset, value):
    enum = get_enum_by_value(enum_class, value)
    if enum == None:
        return queryset

    new_queryset = queryset.filter(status_val=Value(enum.name))
    return new_queryset


def filter_month_queryset(translation_dict, field_name, queryset, value):
    month, year = value.split("-", 2)

    query_field_name = translation_dict.get(field_name)
    query_filter = {
        f"{query_field_name}__year": year,
        f"{query_field_name}__month": month,
    }

    new_queryset = queryset.filter(**query_filter)
    return new_queryset


def is_future_contract(year, month):
    request_date = datetime.strptime(f"{year}-{month}", "%Y-%m")
    today = date.today()
    if request_date.year >= today.year and request_date.month > today.month:
        return True
    else:
        return False


def retrieve_month(month):
    switcher = {
        1: "january",
        2: "february",
        3: "march",
        4: "april",
        5: "may",
        6: "june",
        7: "july",
        8: "august",
        9: "september",
        10: "october",
        11: "november",
        12: "december",
    }

    return switcher[int(month)]


def get_field_value(data, field_name):
    if data == None:
        return ""

    splited_field = field_name.split("__", 1)

    if len(splited_field) > 1:
        return get_field_value(getattr(data, splited_field[0]), splited_field[1])

    return getattr(data, field_name)


def display_as_str(value):
    if value == None:
        return ""
    if type(value) == datetime:
        timezone_location = pytz.timezone("America/Sao_Paulo")
        new_value = value.astimezone(timezone_location)

        return new_value.strftime("%d/%m/%Y %H:%M")
    if type(value) == date:
        return value.strftime("%d/%m/%Y")
    if type(value) == Decimal:
        return decimal_as_str(value)

    return str(value)


def get_index_by_dict_list(data_list, name, value):
    for index, data in enumerate(data_list):
        if data[name] == value:
            return index

    return None


def decimal_as_str(value):
    decimal_str = f"{round(value, 2):,}"
    decimal_with_dots = decimal_str.replace(",", ".")
    # replacing only the last . to ,
    brl_decimal = ",".join(decimal_with_dots.rsplit(".", 1))

    return brl_decimal


def retrieve_month_year_from_contract_dispatch(contract_dispatch):
    supply_date_str = contract_dispatch.supply_date.strftime("%Y-%m")
    year, month = supply_date_str.split("-", 1)
    return year, month


def add_sort_fields(fields_dict):
    new_dict = {}
    new_dict.update(fields_dict)

    for field_name in fields_dict:
        field_dict_value = fields_dict[field_name]
        field_value = (
            field_dict_value if type(field_dict_value) == str else field_dict_value[0]
        )

        new_dict[f"-{field_name}"] = f"-{field_value}"

    return new_dict


def get_ymd_as_date(date_string):
    return datetime.strptime(date_string, "%Y-%m-%d")


def get_field_names(fields_dict):
    result = []

    for field_name in fields_dict:
        result.append(field_name)

    return result


def translate_field(request, field, value):
    result = translate_label(f"contract_dispatch_{field}_{value}", request)
    return result


def get_enum_by_value(enum_class, value):
    for enum_option in enum_class:
        if enum_option.verbose_name.lower() == value.lower():
            return enum_option

    raise ValidationError({"detail": f"{value} is an invalid enum value"})
