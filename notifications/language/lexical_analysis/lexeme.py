from enum import Enum


class LexemeTypes(Enum):
    LO = "Logical Operation"  # logical operation (&& or ||)
    LC = "Logical Comparison"  # logical comparison (== != > < >= <=)
    AR = "Arithmetical Operation"  # arithmetical operation (+ - / *)
    VAR = "Variable"  # variable (currentDate, date)
    DB = "Database Attribute"  # database attribute (table column name, ${a-Z, 0-9, _})
    STR = "String"  # string value ("any")
    NUM = "Number"  # integer value (0-9)
    OPA = "Open Parenthesis"  # open parenthesis ("(")
    EPA = "End of Parenthesis"  # close parenthesis (")")
    EOS = "End of state"  # end of state


def get_lexeme_types():
    result = {}
    for type in LexemeTypes:
        result[type.name] = {type.name: type.value}

    return result


class Lexeme:
    def __init__(self, type):
        self.type = type
        self.value = ""
