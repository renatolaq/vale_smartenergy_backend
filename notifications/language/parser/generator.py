from django.db.models import F, Q
from datetime import date, timedelta
from notifications.utils.date import transform_django_datetime, add_day_to_date
from notifications.utils.db import get_db_field_internal_type
from notifications.language.lexical_analysis.lexeme import LexemeTypes

## logical operations
def get_arg(field_name, arg_value, operator):
    arg = {}
    if operator == "!=":
        arg[field_name] = arg_value
        # it's a negation (!=)
        return deny_arg(arg)

    arg[field_name + operator] = get_operator_value(arg_value)

    return Q(**arg)


def deny_arg(args):
    return ~Q(**args)


def get_args(args):
    if type(args).__name__ == "dict":
        return Q(**args)
    return args


def filter_or(args1, args2):
    return Q(get_args(args1)) | Q(get_args(args2))


def filter_and(args1, args2):
    return Q(get_args(args1)) & Q(get_args(args2))


# aritimetical operations


def make_operation(operator_left, operator_right, operator):
    # datetime operations

    if type(operator_left) in [date]:
        return add_day_to_date(operator_left, operator_right)

    if operator_left["field_internal_type"] in ["DateField", "DateTimeField"]:
        return add_day_to_date_field(operator_left["value"], int(operator_right))

    if operator_left["field_internal_type"] in ["currentDate"]:
        return add_day_to_date(date.today(), operator_right)

    operator_left_value = get_operator_value(operator_left)
    operator_right_value = get_operator_value(operator_right)

    operation_functions = {
        "+": sum_to,
        "-": subtract_from,
        "*": multiply_to,
        "/": divide_by,
    }

    return operation_functions[operator](operator_left_value, operator_right_value)


def get_operator_value(operator):
    if type(operator) in [dict]:
        return F(operator["value"])

    return operator


def add_day_to_date_field(field_name, value):
    return F(field_name) + timedelta(days=value)


def sum_to(operator_left, operator_right):
    return operator_left + operator_right


def subtract_from(operator_left, operator_right):
    return operator_left - operator_right


def multiply_to(operator_left, operator_right):
    return operator_left * operator_right


def divide_by(operator_left, operator_right):
    return operator_left / operator_right


# get variable


def get_variable(variable):
    if variable["value"] == "currentDate":
        return date.today()
    else:
        return transform_django_datetime(variable["value"])
    return None


def get_field(field, module):
    field_internal_type = get_db_field_internal_type(field["value"], module)

    field_value = (
        (field["value"] + "__date")
        if field_internal_type == "DateTimeField"
        else field["value"]
    )
    return {"value": field_value, "field_internal_type": field_internal_type}


def get_value(variable, module):
    if variable["type"] == LexemeTypes.VAR.value:
        return get_variable(variable)

    if variable["type"] == LexemeTypes.DB.value:
        return get_field(variable, module)

    if variable["type"] == LexemeTypes.NUM.value:
        return float(variable["value"])

    return variable["value"]


## Queryset Generator
def generate_logical_operation(logical_block, module, FilterTypes):
    operator_left = generate_filter(logical_block["operator_left"], module, FilterTypes)

    operator_right = generate_filter(
        logical_block["operator_right"], module, FilterTypes
    )

    if logical_block["operation"] == "&&":
        return filter_and(operator_left, operator_right)

    return filter_or(operator_left, operator_right)


def generate_logical_comparison(comparison_block, module, FilterTypes):
    field = get_field(comparison_block["field"], module)

    comparison_value = generate_filter(comparison_block["value"], module, FilterTypes)

    return get_arg(field["value"], comparison_value, comparison_block["operation"])


def generate_aritimetical_operation(aritimetical_block, module, FilterTypes):
    operator_left = generate_filter(
        aritimetical_block["operator_left"], module, FilterTypes
    )
    operator_right = generate_filter(
        aritimetical_block["operator_right"], module, FilterTypes
    )

    return make_operation(
        operator_left, operator_right, aritimetical_block["operation"],
    )


def generate_filter(dict_query, module, FilterTypes):
    if dict_query["type"] == FilterTypes.LOGICAL_OPERATION.value:
        return generate_logical_operation(dict_query, module, FilterTypes)
    if dict_query["type"] == FilterTypes.LOGICAL_COMPARISON.value:
        return generate_logical_comparison(dict_query, module, FilterTypes)
    elif dict_query["type"] == FilterTypes.ARITIMETICAL_OPERATION.value:
        return generate_aritimetical_operation(dict_query, module, FilterTypes)
    else:
        return get_value(dict_query, module)
