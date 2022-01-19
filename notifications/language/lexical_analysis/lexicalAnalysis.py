""" Grammar
let = limited characters [a-Z, 0-9, _, /, :]
num = number [0-9] with . as decimals
lc  = logical comparison [>, <] // can be completed with "=" [>=, <=]
ulc = uncompleted logical comparison [=, !] // must be completed with "=" [==, !=]
ar  = arithmetical operation [+, -, *, /]
any = anything [*]
quo = quotes ["]
λ   = final state

>q0 -> "$" q1 | "{" q2 | num q4 | quo q5 | lc q6 | ulc q7 | "|" q9 | "&" q10 | ar λ | opa λ | epa λ
q1  -> "{" q2
q2  -> let q3
q3  -> let q3 | "}" q8
q4  -> num q4 | "." q11 | λ
q5  -> any q5 | quo q8
q6  -> "=" q8 | λ
q7  -> "=" q8
q8  -> λ
q9  -> "|" q8
q10 -> "&" q8
q11 -> num q12
q12 -> num q12 | λ

Tip: in this code, q8 will be equal to q0, because various lexemes is implemented sequentially
"""
from .symbols import Symbols
from .lexeme import Lexeme, LexemeTypes


class LexicalAnalysis:
    def __init__(self):
        self.__current = None
        self.lexemes = []

    def __new_lexeme(self, lexeme_type):
        if self.__current:
            self.lexemes.append(self.__current)
        self.__current = Lexeme(lexeme_type)

    def __add_to_lexeme(self, value):
        self.__current.value += value

    def analyze(self, string):
        result = Result()
        state = 0

        # checks string characters
        for character in string:
            result.character = character

            state = self.__check_char(character, state)
            if state == -1:
                break

            self.__add_to_lexeme(character)
            result.index += 1

        # add last lexeme to list
        self.lexemes.append(self.__current)

        # checks if string ended correctly
        if result.index > 0 and self.__check_char("end", state) == True:
            result.is_correct = True
            result.add_lexemes_dict(self.lexemes)
            result.lexemes = self.lexemes
            del result.index
            del result.character

        return result

    # graph that analysis the grammar for current char
    def __check_char(self, character, state):
        if state == 0:
            # "$" q1 | "{" q2 | num q4 | quo q5 | lc q6 | ulc q7 | "|" q9 | "&" q10 | ar λ | opa λ | epa λ
            if character == "$":
                self.__new_lexeme(LexemeTypes.DB)
                return 1
            elif character == "{":
                self.__new_lexeme(LexemeTypes.VAR)
                return 2
            elif Symbols.NUM.find(character):
                self.__new_lexeme(LexemeTypes.NUM)
                return 4
            elif Symbols.QUO.find(character):
                self.__new_lexeme(LexemeTypes.STR)
                return 5
            elif Symbols.LC.find(character):
                self.__new_lexeme(LexemeTypes.LC)
                return 6
            elif Symbols.ULC.find(character):
                self.__new_lexeme(LexemeTypes.LC)
                return 7
            elif character == "|":
                self.__new_lexeme(LexemeTypes.LO)
                return 9
            elif character == "&":
                self.__new_lexeme(LexemeTypes.LO)
                return 10
            elif Symbols.AR.find(character):
                self.__new_lexeme(LexemeTypes.AR)
                return 0
            elif character == "(":
                self.__new_lexeme(LexemeTypes.OPA)
                return 0
            elif character == ")":
                self.__new_lexeme(LexemeTypes.EPA)
                return 0
            elif character == "end":
                return True
        if state == 1:  # "{" q2
            if character == "{":
                return 2
        if state == 2:  # let q3
            if Symbols.LET.find(character):
                return 3
        if state == 3:  # let q3 | "}" λ
            if Symbols.LET.find(character):
                return 3
            elif character == "}":
                return 0
        if state == 4:  # num q4 | "." q11 | λ
            if Symbols.NUM.find(character):
                return 4
            elif character == "end":
                return True
            if character == ".":
                return 11
            else:
                return self.__check_char(character, 0)  # validate next lexeme
        if state == 5:  # any q5 | quo λ
            if character != '"':
                return 5
            elif Symbols.QUO.find(character):
                return 0
        if state == 6:  # "=" λ | λ
            if character == "=":
                return 0
            elif character == "end":
                return True
            else:
                return self.__check_char(character, 0)  # validate next lexeme
        if state == 7:  # "=" λ
            if character == "=":
                return 0
        if state == 9:  # "=" λ
            if character == "|":
                return 0
        if state == 10:  # "=" λ
            if character == "&":
                return 0
        if state == 11:  # num q12
            if Symbols.NUM.find(character):
                return 12
        if state == 12:  # num q12 | λ
            if Symbols.NUM.find(character):
                return 12
            elif character == "end":
                return True
            else:
                return self.__check_char(character, 0)  # validate next lexeme

        return -1


class Result:
    def __init__(self):
        self.index = 0
        self.character = ""
        self.is_correct = False
        self.lexemes_dict = None
        self.lexemes = None

    def add_lexemes_dict(self, lexemes):
        parsed_lexemes = []
        for lexeme in lexemes:
            parsed_lexemes.append({"type": lexeme.type.value, "value": lexeme.value})

        self.lexemes_dict = parsed_lexemes

