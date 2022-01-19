from unittest import mock

# mock transaction.atomic decorators before import modules
from notifications.utils.date import transform_django_datetime

mock.patch("django.db.transaction.atomic", lambda func: func).start()
from django.test import SimpleTestCase
from django.db.models.query_utils import Q

from notifications.business.notifiable_modules import Modules
from notifications.business.notifications_business import NotifiableModulesFactory
from notifications.language.lexical_analysis.lexicalAnalysis import LexicalAnalysis
from notifications.language.syntatic_analysis.syntaticAnalysis import SyntaticAnalysis
from notifications.language.parser.parser import get_string_validation
from notifications.language.parser.lib import ExpressionTypes
from notifications.language.parser.generator import generate_filter

from notifications.tests.lib import (
    language_strings_module,
    incorrect_language_strings_module,
    logical_operation_dict,
    logical_comparison_dict,
    aritimetical_operation_dict,
)


class TestNotifiableModule(SimpleTestCase):
    def setUp(self):
        pass

    # Language tests
    def test_lexical_analysis_supports_language(self):

        for string_module in language_strings_module:
            lexical_analizer = LexicalAnalysis()
            result = lexical_analizer.analyze(string_module["string"])
            lexemes = lexical_analizer.lexemes

            self.assertTrue(result.is_correct)
            self.assertEqual(len(lexemes), string_module["lexeme_length"])

    def test_syntatic_analysis_supports_language(self):

        for string_module in language_strings_module:
            lexical_analizer = LexicalAnalysis()
            syntatic_analizer = SyntaticAnalysis()
            module = NotifiableModulesFactory.create_notifiable_module(
                Modules[string_module["module"]]
            )
            lexical_result = lexical_analizer.analyze(string_module["string"])
            lexemes = lexical_analizer.lexemes
            syntatic_result = syntatic_analizer.analize(lexemes, module, False)

            self.assertTrue(syntatic_result.is_correct)

    def test_syntatic_tree_generation_supports_language(self):

        for string_module in language_strings_module:
            lexical_analizer = LexicalAnalysis()
            syntatic_analizer = SyntaticAnalysis()
            string = string_module["string"]
            module = NotifiableModulesFactory.create_notifiable_module(
                Modules[string_module["module"]]
            )
            lexical_result = lexical_analizer.analyze(string)
            lexemes = lexical_analizer.lexemes
            syntatic_result = syntatic_analizer.analize(lexemes, module)

            self.assertTrue(syntatic_result.is_correct)
            self.assertIsInstance(syntatic_result.dict_tree, dict)

    def test_string_validations_should_validate_correct_result(self):
        for string_module in language_strings_module:
            module = NotifiableModulesFactory.create_notifiable_module(
                Modules[string_module["module"]]
            )
            result = get_string_validation(string_module["string"], module)

            self.assertTrue(result["is_correct"])

    def test_string_validations_should_validate_incorrect_result(self):
        for string_module in incorrect_language_strings_module:
            module = NotifiableModulesFactory.create_notifiable_module(
                Modules[string_module["module"]]
            )
            result = get_string_validation(string_module["string"], module)

            self.assertFalse(result["is_correct"])

    @mock.patch("notifications.language.parser.generator.generate_logical_operation")
    def test_generate_filter_should_run_logical_operation(
        self, generate_logical_operation
    ):
        module = NotifiableModulesFactory.create_notifiable_module(
            Modules["USAGE_CONTRACT"]
        )
        dict_query = logical_operation_dict

        generate_filter(dict_query, module, ExpressionTypes)

        self.assertTrue(generate_logical_operation.called)

    @mock.patch("notifications.language.parser.generator.generate_logical_comparison")
    def test_generate_filter_should_run_logical_comparison(
        self, generate_logical_comparison
    ):
        module = NotifiableModulesFactory.create_notifiable_module(
            Modules["USAGE_CONTRACT"]
        )
        dict_query = logical_comparison_dict

        generate_filter(dict_query, module, ExpressionTypes)

        self.assertTrue(generate_logical_comparison.called)

    @mock.patch(
        "notifications.language.parser.generator.generate_aritimetical_operation"
    )
    def test_generate_filter_should_run_aritimetical_operation(
        self, generate_aritimetical_operation
    ):
        module = NotifiableModulesFactory.create_notifiable_module(
            Modules["USAGE_CONTRACT"]
        )
        dict_query = aritimetical_operation_dict

        generate_filter(dict_query, module, ExpressionTypes)

        self.assertTrue(generate_aritimetical_operation.called)

    @mock.patch("notifications.language.parser.generator.get_value")
    def test_generate_filter_should_run_value(self, get_value):
        module = NotifiableModulesFactory.create_notifiable_module(
            Modules["USAGE_CONTRACT"]
        )
        dict_query = {"value": "N", "type": "String"}

        generate_filter(dict_query, module, ExpressionTypes)

        self.assertTrue(get_value.called)

    @mock.patch("notifications.language.parser.generator.get_value")
    def test_generate_filter_should_supports_language(self, get_value):
        for string_module in language_strings_module:
            lexical_analizer = LexicalAnalysis()
            syntatic_analizer = SyntaticAnalysis()
            string = string_module["string"]
            module = NotifiableModulesFactory.create_notifiable_module(
                Modules[string_module["module"]]
            )
            module.add_field_options = mock.Mock()
            lexical_result = lexical_analizer.analyze(string)
            lexemes = lexical_analizer.lexemes
            syntatic_result = syntatic_analizer.analize(lexemes, module)

            filter = generate_filter(syntatic_result.dict_tree, module, ExpressionTypes)

            self.assertIsInstance(filter, Q)

    def test_transform_django_datetime_should_fail_parsing_not_formatted_date(self):
        value = "date:2020/02/02"
        try:
            transform_django_datetime(value)
        except Exception:
            return
        self.fail("transform_django_datetime accepting wrong date formats")

    def test_transform_django_datetime_shouldnt_fail_parsing_correct_formatted_date(self):
        value = "date:02/02/2002"
        try:
            transform_django_datetime(value)
        except Exception:
            self.fail("transform_django_datetime accepting wrong date formats")
