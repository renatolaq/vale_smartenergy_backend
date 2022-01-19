from unittest import mock

from django.test import SimpleTestCase

from usage_contract.uteis.list import queryset_name_to_string
from usage_contract.tests.lib import QuerysetMock, usage_contract_enabled_mock


class TestUsageContractUteisList(SimpleTestCase):
    def test_queryset_name_to_string_should_return_correctly(self):
        custom_queryset = QuerysetMock(usage_contract_enabled_mock)
        result = queryset_name_to_string(custom_queryset)
        self.assertEqual(result, "a, b, c")
