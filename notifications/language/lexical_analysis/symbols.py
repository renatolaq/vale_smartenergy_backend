"""
LET = limited characters [a-Z, 0-9, _, /, :]
NUM = number [0-9]
LC = logical comparison [>, <]
ULC = uncompleted logical comparison [=, !]
LO = logical operation [&, |]
AR = arithmetical operation [+, -, *, /]
AD = arithmetical date [+, -]
QUO = quote ["]
"""

from enum import Enum

class Symbols(Enum):
    LET = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_/:"
    NUM = "0123456789"
    LC = "><"
    ULC = "=!"
    LO = "&|"
    AR = "+-*/"
    AD = "+-"
    QUO = '"'

    def find(self, character):
        return self.value.find(character) != -1