from .lib import ExpressionTypes
from .generator import generate_filter
from notifications.language.lexical_analysis.lexicalAnalysis import LexicalAnalysis
from notifications.language.syntatic_analysis.syntaticAnalysis import SyntaticAnalysis

from usage_contract.models import UsageContract

# consume with syntatic tree dictionary to get values
def get_entity_result(dict_query, module, **kwargs):
    module_main_model = module.main_model

    # create filter object
    filter = generate_filter(dict_query, module, ExpressionTypes)
    result = module_main_model.objects.filter(filter)

    if "pk" in kwargs.keys():
        result = result.filter(pk=kwargs["pk"])

    return result


def get_result(dict_query, module, **kwargs):
    result = get_entity_result(dict_query, module, **kwargs)

    return list(result.values())


# consume to generate the syntatic tree and dictionary
def get_dict_tree(query_string, module):
    lexical_result = get_lexical_result(query_string)

    if not lexical_result.is_correct:
        raise Exception("String format is invalid!", lexical_result.__dict__)
    lexemes = lexical_result.lexemes

    # make syntatic analysis
    syntatic_analizer = SyntaticAnalysis()
    syntatic_result = syntatic_analizer.analize(lexemes, module)
    if not syntatic_result.is_correct:
        raise Exception("Operations are in incorrect format!", syntatic_result.__dict__)

    return syntatic_result.dict_tree


# consume to check if string is correct
def get_string_validation(query_string, module):
    lexical_result = get_lexical_result(query_string)

    if not lexical_result.is_correct and query_string != "":
        raise Exception("String format is invalid!", lexical_result.__dict__)
    lexemes = [] if query_string == "" else lexical_result.lexemes

    # make syntatic analysis
    syntatic_analizer = SyntaticAnalysis()
    syntatic_result = syntatic_analizer.analize(lexemes, module, True)

    return syntatic_result.__dict__


def get_lexical_result(query_string):
    # make lexical analysis
    lexical_analizer = LexicalAnalysis()
    lexical_result = lexical_analizer.analyze(query_string)

    return lexical_result
