import decimal
from datetime import datetime, date
import pytz


def split_words(word):
    return [char for char in word]


def check_parenthesis(string):
    open_parenthesis = string.count("(")
    close_parenthesis = string.count(")")
    return open_parenthesis == close_parenthesis


def clean_db_field(db_field_name):
    clean_field = db_field_name.replace("$", "").replace("{", "").replace("}", "")
    return clean_field


def add_db_variable_brackets(field):
    return f"${{{field}}}"


def display_as_str(value):
    if value == None:
        return ""
    if type(value) == datetime:
        timezone_location = pytz.timezone("America/Sao_Paulo")
        new_value = value.astimezone(timezone_location)

        return new_value.strftime("%d/%m/%Y %H:%M")
    if type(value) == date:
        return value.strftime("%d/%m/%Y")
    if type(value) == decimal.Decimal:
        return decimal_as_str(value)

    return str(value)


def decimal_as_str(value):
    decimal_str = f"{value:,}"
    decimal_with_dots = decimal_str.replace(",", ".")
    # replacing only the last . to ,
    brl_decimal = ",".join(decimal_with_dots.rsplit(".", 1))

    return brl_decimal
