from datetime import date
from unittest import mock

from django.test import SimpleTestCase

from usage_contract.uteis.error import return_linked_budgets, generate_delete_msg
from usage_contract.tests.lib import usage_contract_mock, DateMock, HttpRequestMock


class TestUsageContractUteisError(SimpleTestCase):
    @mock.patch("company.models.Company.objects.filter", return_value=mock.Mock())
    @mock.patch(
        "budget.models.CompanyBudget.CompanyBudget.objects.filter",
        return_value=mock.Mock(),
    )
    def test_return_linked_budgets_should_validate_end_date_and_return_budgets(
        self, company_budget_objects_filter, company_objects_filter,
    ):
        usage_contract_mock.end_date = date(3000, 2, 2)
        result = return_linked_budgets(usage_contract_mock)

        self.assertTrue(company_budget_objects_filter.called)
        self.assertTrue(company_objects_filter.called)

    def test_generate_delete_msg_should_return_correctly_pt(self):
        request = HttpRequestMock({})
        request.META["HTTP_ACCEPT_LANGUAGE"] = "pt-BR"

        example = "ab"

        result_budget = generate_delete_msg(example, None, request)
        result_gauge = generate_delete_msg(None, example, request)
        result_budget_gauge = generate_delete_msg(example, example, request)

        self.assertEqual(
            result_budget,
            "Não foi possível desativar este Contrato de Uso porque há um link para Orçamento(s): a, b",
        )
        self.assertEqual(
            result_gauge,
            "Não foi possível desativar este Contrato de Uso porque há um link para Ponto de medição: a, b",
        )
        self.assertEqual(
            result_budget_gauge,
            "Não foi possível desativar este Contrato de Uso porque há um link para Orçamento(s): a, b e Ponto de medição: a, b",
        )

    def test_generate_delete_msg_should_return_correctly_en(self):
        request = HttpRequestMock({})
        request.META["HTTP_ACCEPT_LANGUAGE"] = "en"

        example = "ab"

        result_budget = generate_delete_msg(example, None, request)
        result_gauge = generate_delete_msg(None, example, request)
        result_budget_gauge = generate_delete_msg(example, example, request)

        self.assertEqual(
            result_budget,
            "Could not disable this Usage Contract because there is a link to Budget(s): a, b",
        )
        self.assertEqual(
            result_gauge,
            "Could not disable this Usage Contract because there is a link to Measurement point: a, b",
        )
        self.assertEqual(
            result_budget_gauge,
            "Could not disable this Usage Contract because there is a link to Budget(s): a, b and Measurement point: a, b",
        )

