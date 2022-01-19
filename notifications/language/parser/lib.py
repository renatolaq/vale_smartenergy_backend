from enum import Enum

class ExpressionTypes(Enum):
    LOGICAL_OPERATION = "logical_operation"  # && or ||
    LOGICAL_COMPARISON = "logical_comparison"  # == != > < >= <=
    ARITIMETICAL_OPERATION = "aritimetical_operation"  # + - / *


operators = {
    "<": "__lt",
    ">": "__gt",
    "<=": "__lte",
    ">=": "__gte",
    "==": "__exact",
    "!=": "!=",  # needs ~Q
}