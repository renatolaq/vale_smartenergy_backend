"""
Labels:
Lo  = logical operation (&& or ||)
Lc  = logical comparison (== != > < >= <=)
Ar  = arithmetical operation (+ - / *)
Var = variable (currentDate, date)
Db  = database attribute (table column name, ${a-Z, 0-9, _})
Str = string value ("any")
Num = integer value (0-9)
Opa = open parenthesis ("(")
Epa = close parenthesis (")")
λ   = end statement

>q0 = Db q1 | Opa q0 > push λ
q1  = Lc q2
q2  = Opa q2 > push λ | Str q3 | Db q4 | Num q4 | Var q4
q3  = Epa q3 > pop λ | Lo q0 | λ
q4  = Epa q4 > pop λ | Ar q5 | Lo q0 | λ
q5  = Opa q5 > push λ | Db q4 | Num q4 | Var q4
"""
from .syntaticTreeGenerator import SyntaticTreeGenerator
from notifications.language.lexical_analysis.lexeme import Lexeme, LexemeTypes, get_lexeme_types
from notifications.utils.db import get_db_field_internal_type
from notifications.utils.string import clean_db_field


class SyntaticAnalysis:
    def __init__(self):
        self.lambdas = 0
        self.result = Result()
        self.module = None

    def __acquire_lambda(self):
        if self.lambdas == 0:
            self.result.unnespected_close_parenthesis = True
            return False
        self.lambdas -= 1
        return True

    def __release_lambda(self):
        self.lambdas += 1
        return True

    def analize(self, lexemes, module, check=False):
        self.module = module
        state = 0

        for index, lexeme in enumerate(lexemes):
            state = self.__check_lexeme(lexeme, state)
            if state < 0:
                self.result.index = index
                self.result.field = lexeme.value
                return self.result

        # check if it ended correctly
        if self.lambdas > 0:
            self.result.missing_a_parenthesis = True
        else:
            last_check = self.__last_check(state)
            if last_check == True:
                self.result.is_correct = True

                # generate tree only if it's not a check consumption
                if not check:
                    generator = SyntaticTreeGenerator()
                    tree = generator.generate(lexemes)

                    self.result.syntatic_tree = tree.syntatic_tree
                    self.result.dict_tree = tree.dict_tree

        self.__get_allowed_lexemes_by_state(state, lexemes)

        return self.result

    def __last_check(self, state):
        check_lexeme = Lexeme(LexemeTypes.EOS)
        return self.__check_lexeme(check_lexeme, state)

    def __check_lexeme(self, lexeme, state):
        if state == 0:  # Db q1 | Opa q0 > push λ
            if lexeme.type == LexemeTypes.OPA:
                self.__release_lambda()
                return 0
            elif lexeme.type == LexemeTypes.DB:
                return 1
        elif state == 1:  # Lc q2
            if lexeme.type == LexemeTypes.LC:
                return 2
        elif state == 2:  # Opa q2 > push λ | Str q3 | Db q4 | Num q4 | Var q4
            if lexeme.type == LexemeTypes.OPA:
                self.__release_lambda()
                return 2
            elif lexeme.type == LexemeTypes.STR:
                return 3
            elif lexeme.type in [LexemeTypes.DB, LexemeTypes.NUM, LexemeTypes.VAR]:
                return 4
        elif state == 3:  # Epa q3 > pop λ | Lo q0 | λ
            if lexeme.type == LexemeTypes.EPA:
                if self.__acquire_lambda():
                    return 3
            elif lexeme.type == LexemeTypes.LO:
                return 0
            elif lexeme.type == LexemeTypes.EOS:
                return True
        elif state == 4:  # Epa q4 > pop λ | Ar q5 | Lo q0 | λ
            if lexeme.type == LexemeTypes.EPA:
                if self.__acquire_lambda():
                    return 4
            elif lexeme.type == LexemeTypes.AR:
                return 5
            elif lexeme.type == LexemeTypes.LO:
                return 0
            elif lexeme.type == LexemeTypes.EOS:
                return True
        elif state == 5:  # Opa q5 > push λ | Db q4 | Num q4 | Var q4
            if lexeme.type == LexemeTypes.OPA:
                self.__release_lambda()
                return 5
            elif lexeme.type in [LexemeTypes.DB, LexemeTypes.NUM, LexemeTypes.VAR]:
                return 4
        return -1

    def __get_allowed_lexemes_by_state(self, state, lexemes):
        self.result.allowed_to_complete = self.__get_allowed_lexemes(state, lexemes)

    def __get_allowed_lexemes(self, state, lexemes):
        lexeme_types = get_lexeme_types()
        # lexemes as readable objects
        lo = lexeme_types["LO"]
        lc = lexeme_types["LC"]
        ar = lexeme_types["AR"]
        var = lexeme_types["VAR"]
        db = lexeme_types["DB"]
        str = lexeme_types["STR"]
        num = lexeme_types["NUM"]
        opa = lexeme_types["OPA"]
        epa = lexeme_types["EPA"]
        eos = lexeme_types["EOS"]

        if state == 0:
            return [db, opa]
        if state == 1:
            return [lc]
        if state == 2:
            last_lexeme = lexemes[len(lexemes) - 2 : len(lexemes) - 1][0]

            # check db type
            field_internal_type = get_db_field_internal_type(
                clean_db_field(last_lexeme.value), self.module
            )

            # is different for date and datetime
            if field_internal_type in ["DateField", "DateTimeField"]:
                return [opa, db, var]

            return [opa, str, db, num, var]
        if state == 3:
            return [epa, lo]
        if state == 4:
            return [epa, ar, lo]
        if state == 5:
            return [opa, db, num, var]

        return None


class Result:
    def __init__(self):
        self.is_correct = False
