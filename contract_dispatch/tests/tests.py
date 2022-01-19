from unittest import mock
from django.test import SimpleTestCase

from rest_framework.request import Request
from django.http import HttpRequest, QueryDict
from .lib import (
    mock_query_set,
    contract_cliq_list,
    mock_generation_dict,
    MockContractDispatch,
    MockCliqContract,
    MockQuerySet,
)
from rest_framework.exceptions import ValidationError

from datetime import date

from contract_dispatch.business.contract_dispatch_business import (
    ContractDispatchBusiness,
)
from contract_dispatch.generators.pdf_generator import (
    generate_pdf,
    generate_pdf_by_contract,
    generate_pdf_contracts_to_send,
    generate_pdf_contracts_by_ids,
    generate as pdf_generate,
)
from contract_dispatch.generators.xlsx_generator import (
    generate_xlsx,
    generate_xlsx_by_contract,
    generate_xlsx_contracts_to_send,
    generate_xlsx_contracts_by_ids,
    generate as xlsx_generate,
    set_content_style,
    set_header_style,
    adjust_column_cell,
)
from contract_dispatch import views


class NoDbTestRunner(SimpleTestCase):
    def setUp(self,):
        http_request = HttpRequest()

        http_request.method = "POST"
        self.mock_http_request_post = http_request
        self.mock_request = Request(http_request)

        http_request_get = HttpRequest()
        http_request_get.method = "GET"
        self.mock_http_request_get = http_request_get

        http_request_get = HttpRequest()
        http_request_get.GET = QueryDict("operation=register&supplyDate=2020-01")
        self.mock_request_get = Request(http_request_get)

        http_request_sort_only = HttpRequest()
        http_request_sort_only.GET = QueryDict("sort=status")
        self.mock_request_sort_only = Request(http_request_sort_only)

        self.mock_contract_dispatch = MockContractDispatch(**{"pk": 1})
        self.mock_contract_cliq = MockCliqContract(**{"pk": 1})

    # Business tests

    @mock.patch(
        "contract_dispatch.models.ContractDispatch.objects.filter", return_value=[],
    )
    @mock.patch(
        "contract_dispatch.models.CliqContract.objects.filter",
        return_value=mock_query_set,
    )
    def test_retrieve_contracts_dict_list_by_month_should_return_list(
        self, cliq_contract_objects_mock, contract_dispatch_objects_mock,
    ):
        result = ContractDispatchBusiness.retrieve_contracts_dict_list_by_month(
            self.mock_request
        )
        result_get = ContractDispatchBusiness.retrieve_contracts_dict_list_by_month(
            self.mock_request_get
        )
        self.assertTrue(type(result) == list)
        self.assertTrue(type(result_get) == list)

    @mock.patch(
        "contract_dispatch.models.ContractDispatch.objects.filter", return_value=[],
    )
    @mock.patch(
        "contract_dispatch.models.CliqContract.objects.filter",
        return_value=mock_query_set,
    )
    def test_retrieve_contracts_by_contract_dispatch_should_return_queryset(
        self, cliq_contract_objects_mock, contract_dispatch_objects_mock,
    ):
        result = ContractDispatchBusiness.retrieve_contracts_by_contract_dispatch(
            self.mock_request, self.mock_contract_dispatch
        )

        self.assertTrue(type(result) == MockQuerySet)

    @mock.patch(
        "contract_dispatch.models.ContractDispatch.objects.filter", return_value=[],
    )
    @mock.patch(
        "contract_dispatch.models.CliqContract.objects.filter",
        return_value=mock_query_set,
    )
    @mock.patch(
        "contract_dispatch.models.CliqContractCurrentStatus.objects.filter",
        return_value=mock_query_set,
    )
    def test_retrieve_contracts_dict_list_by_contract_dispatch_should_return_queryset(
        self,
        contract_dispatch_objects_mock,
        cliq_contract_objects_mock,
        cliq_contract_current_status_objects_mock,
    ):
        result = ContractDispatchBusiness.retrieve_contracts_dict_list_by_contract_dispatch(
            self.mock_request, self.mock_contract_dispatch
        )

        self.assertTrue(type(result) == list)

    @mock.patch(
        "contract_dispatch.models.ContractDispatch.objects.filter", return_value=[],
    )
    @mock.patch(
        "contract_dispatch.models.CliqContract.objects.filter",
        return_value=mock_query_set,
    )
    def test_retrieve_contracts_to_send_should_return_queryset(
        self, cliq_contract_objects_mock, contract_dispatch_objects_mock,
    ):
        result = ContractDispatchBusiness.retrieve_contracts_to_send(
            self.mock_request, 2020, 7, None
        )

        result_with_balance = ContractDispatchBusiness.retrieve_contracts_to_send(
            self.mock_request, 2020, 7, 1
        )

        self.assertTrue(type(result) == MockQuerySet)
        self.assertTrue(type(result_with_balance) == MockQuerySet)

    @mock.patch(
        "contract_dispatch.models.ContractDispatch.objects.filter", return_value=[],
    )
    @mock.patch(
        "contract_dispatch.models.CliqContract.objects.filter",
        return_value=mock_query_set,
    )
    def test_retrieve_contracts_dict_list_contracts_to_send_should_return_queryset(
        self, cliq_contract_objects_mock, contract_dispatch_objects_mock,
    ):
        result = ContractDispatchBusiness.retrieve_contracts_dict_list_contracts_to_send(
            self.mock_request, 2020, 7
        )

        self.assertTrue(type(result) == list)

    @mock.patch(
        "contract_dispatch.models.ContractDispatch.objects.filter", return_value=[],
    )
    @mock.patch(
        "contract_dispatch.models.CliqContract.objects.filter",
        return_value=mock_query_set,
    )
    def test_retrieve_contracts_dict_list_by_contract_cliq_ids_should_return_queryset(
        self, cliq_contract_objects_mock, contract_dispatch_objects_mock,
    ):
        result = ContractDispatchBusiness.retrieve_contracts_dict_list_by_contract_cliq_ids(
            self.mock_request, 2020, 7, None, [1, 2, 3]
        )
        result_with_balance = ContractDispatchBusiness.retrieve_contracts_dict_list_by_contract_cliq_ids(
            self.mock_request, 2020, 7, 1, [1, 2, 3]
        )

        self.assertTrue(type(result) == list)
        self.assertTrue(type(result_with_balance) == list)

    @mock.patch(
        "contract_dispatch.models.ContractDispatch.objects.filter", return_value=[],
    )
    @mock.patch(
        "contract_dispatch.models.CliqContract.objects.filter",
        return_value=mock_query_set,
    )
    def test_generate_contract_list_dict_should_return_queryset(
        self, cliq_contract_objects_mock, contract_dispatch_objects_mock,
    ):
        result = ContractDispatchBusiness.generate_contract_list_dict(
            mock_query_set, self.mock_request
        )
        result_list = ContractDispatchBusiness.generate_contract_list_dict(
            contract_cliq_list, self.mock_request
        )
        result_empty = ContractDispatchBusiness.generate_contract_list_dict(
            None, self.mock_request
        )

        self.assertTrue(type(result) == list)
        self.assertTrue(type(result_list) == list)
        self.assertTrue(type(result_empty) == list)

    @mock.patch(
        "contract_dispatch.models.ContractDispatch.objects.filter", return_value=[],
    )
    @mock.patch(
        "contract_dispatch.models.CliqContract.objects.filter",
        return_value=mock_query_set,
    )
    def test_generate_contract_to_send_list_dict_should_return_queryset(
        self, cliq_contract_objects_mock, contract_dispatch_objects_mock,
    ):
        result = ContractDispatchBusiness.generate_contract_to_send_list_dict(
            mock_query_set, self.mock_request
        )
        result_list = ContractDispatchBusiness.generate_contract_to_send_list_dict(
            contract_cliq_list, self.mock_request
        )
        result_empty = ContractDispatchBusiness.generate_contract_to_send_list_dict(
            None, self.mock_request
        )

        self.assertTrue(type(result) == list)
        self.assertTrue(type(result_list) == list)
        self.assertTrue(type(result_empty) == list)

    @mock.patch(
        "contract_dispatch.models.ContractDispatch.objects.filter", return_value=[],
    )
    @mock.patch(
        "contract_dispatch.models.CliqContract.objects.filter",
        return_value=mock_query_set,
    )
    def test_get_translated_fields_should_return_queryset(
        self, cliq_contract_objects_mock, contract_dispatch_objects_mock,
    ):
        result = ContractDispatchBusiness.get_translated_fields(self.mock_request)

        self.assertTrue(type(result) == list)

    @mock.patch(
        "contract_dispatch.models.ContractDispatch.objects.filter", return_value=[],
    )
    @mock.patch(
        "contract_dispatch.models.CliqContract.objects.filter",
        return_value=mock_query_set,
    )
    def test_contract_dispatch_annotate_operation_should_return_queryset(
        self, cliq_contract_objects_mock, contract_dispatch_objects_mock,
    ):
        result = ContractDispatchBusiness.contract_dispatch_annotate_operation(
            mock_query_set
        )

        self.assertTrue(type(result) == MockQuerySet)

    @mock.patch(
        "contract_dispatch.models.ContractDispatch.objects.filter", return_value=[],
    )
    @mock.patch(
        "contract_dispatch.models.CliqContract.objects.filter",
        return_value=mock_query_set,
    )
    def test_cliq_contract_annotate_category_should_return_queryset(
        self, cliq_contract_objects_mock, contract_dispatch_objects_mock,
    ):
        result = ContractDispatchBusiness.cliq_contract_annotate_category(
            mock_query_set
        )

        self.assertTrue(type(result) == MockQuerySet)

    @mock.patch(
        "contract_dispatch.models.ContractDispatch.objects.filter", return_value=[],
    )
    @mock.patch(
        "contract_dispatch.models.CliqContract.objects.filter",
        return_value=mock_query_set,
    )
    def test_contract_cliq_annotate_status_val_should_return_queryset(
        self, cliq_contract_objects_mock, contract_dispatch_objects_mock,
    ):
        result = ContractDispatchBusiness.contract_cliq_annotate_status_val(
            mock_query_set, 2020, 7
        )

        self.assertTrue(type(result) == MockQuerySet)

    @mock.patch(
        "contract_dispatch.models.ContractDispatch.objects.filter", return_value=[],
    )
    @mock.patch(
        "contract_dispatch.models.CliqContract.objects.filter",
        return_value=mock_query_set,
    )
    def test_contract_cliq_queryset_set_values_should_return_queryset(
        self, cliq_contract_objects_mock, contract_dispatch_objects_mock,
    ):
        result = ContractDispatchBusiness.contract_cliq_queryset_set_values(
            mock_query_set
        )

        self.assertTrue(type(result) == MockQuerySet)

    @mock.patch(
        "contract_dispatch.models.ContractDispatch.objects.filter", return_value=[],
    )
    @mock.patch(
        "contract_dispatch.models.CliqContract.objects.filter",
        return_value=mock_query_set,
    )
    def test_contract_cliq_queryset_annotate_values_should_return_queryset(
        self, cliq_contract_objects_mock, contract_dispatch_objects_mock,
    ):
        result = ContractDispatchBusiness.contract_cliq_queryset_annotate_values(
            mock_query_set
        )

        self.assertTrue(type(result) == MockQuerySet)

    @mock.patch(
        "contract_dispatch.models.ContractDispatch.objects.filter", return_value=[],
    )
    @mock.patch(
        "contract_dispatch.models.CliqContract.objects.filter",
        return_value=mock_query_set,
    )
    def test_contracts_to_send_queryset_set_values_should_return_queryset(
        self, cliq_contract_objects_mock, contract_dispatch_objects_mock,
    ):
        result = ContractDispatchBusiness.contracts_to_send_queryset_set_values(
            mock_query_set
        )

        self.assertTrue(type(result) == MockQuerySet)

    @mock.patch(
        "contract_dispatch.models.ContractDispatch.objects.filter", return_value=[],
    )
    @mock.patch(
        "contract_dispatch.models.CliqContract.objects.filter",
        return_value=mock_query_set,
    )
    def test_contract_cliq_queryset_annotate_current_status_should_return_queryset(
        self, cliq_contract_objects_mock, contract_dispatch_objects_mock,
    ):
        result = ContractDispatchBusiness.contract_cliq_queryset_annotate_current_status(
            mock_query_set
        )

        self.assertTrue(type(result) == MockQuerySet)

    @mock.patch(
        "contract_dispatch.models.ContractDispatch.objects.filter", return_value=[],
    )
    @mock.patch(
        "contract_dispatch.models.CliqContract.objects.filter",
        return_value=mock_query_set,
    )
    def test_contract_cliq_queryset_annotate_operation_should_return_queryset(
        self, cliq_contract_objects_mock, contract_dispatch_objects_mock,
    ):
        result = ContractDispatchBusiness.contract_cliq_queryset_annotate_operation(
            mock_query_set
        )

        self.assertTrue(type(result) == MockQuerySet)

    @mock.patch(
        "contract_dispatch.models.ContractDispatch.objects.filter", return_value=[],
    )
    @mock.patch(
        "contract_dispatch.models.CliqContract.objects.filter",
        return_value=mock_query_set,
    )
    def test_contract_cliq_queryset_add_order_by_should_return_queryset(
        self, cliq_contract_objects_mock, contract_dispatch_objects_mock,
    ):
        result = ContractDispatchBusiness.contract_cliq_queryset_add_order_by(
            mock_query_set
        )

        self.assertTrue(type(result) == MockQuerySet)

    @mock.patch(
        "contract_dispatch.models.ContractDispatch.objects.filter", return_value=[],
    )
    @mock.patch(
        "contract_dispatch.models.CliqContract.objects.filter",
        return_value=mock_query_set,
    )
    def test_contract_dispatch_set_filter_should_return_queryset(
        self, cliq_contract_objects_mock, contract_dispatch_objects_mock,
    ):
        result = ContractDispatchBusiness.contract_dispatch_set_filter(
            self.mock_request, mock_query_set
        )

        http_request = HttpRequest()
        http_request.GET = QueryDict("sort=user")

        result_sort_only = ContractDispatchBusiness.contract_dispatch_set_filter(
            Request(http_request), mock_query_set
        )

        self.assertTrue(type(result) == MockQuerySet)
        self.assertTrue(type(result_sort_only) == MockQuerySet)

    @mock.patch(
        "contract_dispatch.models.ContractDispatch.objects.filter", return_value=[],
    )
    @mock.patch(
        "contract_dispatch.models.CliqContract.objects.filter",
        return_value=mock_query_set,
    )
    def test_contract_cliq_set_filter_should_return_queryset(
        self, cliq_contract_objects_mock, contract_dispatch_objects_mock,
    ):
        result = ContractDispatchBusiness.contract_cliq_set_filter(
            self.mock_request, mock_query_set
        )
        result_sort = ContractDispatchBusiness.contract_cliq_set_filter(
            self.mock_request_sort_only, mock_query_set
        )

        self.assertTrue(type(result) == MockQuerySet)
        self.assertTrue(type(result_sort) == MockQuerySet)

    @mock.patch(
        "contract_dispatch.models.ContractDispatch.objects.filter", return_value=[],
    )
    @mock.patch(
        "contract_dispatch.models.CliqContract.objects.filter",
        return_value=mock_query_set,
    )
    def test_contracts_to_send_set_filter_should_return_queryset(
        self, cliq_contract_objects_mock, contract_dispatch_objects_mock,
    ):
        result = ContractDispatchBusiness.contracts_to_send_set_filter(
            self.mock_request, mock_query_set
        )
        result_sort = ContractDispatchBusiness.contracts_to_send_set_filter(
            self.mock_request_sort_only, mock_query_set
        )

        self.assertTrue(type(result) == MockQuerySet)
        self.assertTrue(type(result_sort) == MockQuerySet)

    @mock.patch(
        "contract_dispatch.models.ContractDispatch.objects.filter", return_value=[],
    )
    @mock.patch(
        "contract_dispatch.models.CliqContract.objects.filter",
        return_value=mock_query_set,
    )
    def test_contract_cliq_queryset_annotate_availability_should_return_queryset(
        self, cliq_contract_objects_mock, contract_dispatch_objects_mock,
    ):
        result = ContractDispatchBusiness.contract_cliq_queryset_annotate_availability(
            mock_query_set
        )

        self.assertTrue(type(result) == MockQuerySet)

    @mock.patch(
        "contract_dispatch.models.ContractDispatch.objects.filter", return_value=[],
    )
    @mock.patch(
        "contract_dispatch.models.CliqContract.objects.filter",
        return_value=mock_query_set,
    )
    def test_contract_cliq_queryset_annotate_volume_on_register_should_return_queryset(
        self, cliq_contract_objects_mock, contract_dispatch_objects_mock,
    ):
        result = ContractDispatchBusiness.contract_cliq_queryset_annotate_volume_on_register(
            mock_query_set
        )

        self.assertTrue(type(result) == MockQuerySet)

    @mock.patch(
        "contract_dispatch.models.ContractDispatch.objects.filter", return_value=[],
    )
    @mock.patch(
        "contract_dispatch.models.CliqContract.objects.filter",
        return_value=mock_query_set,
    )
    def test_contract_cliq_queryset_annotate_volume_on_seasonality_should_return_queryset(
        self, cliq_contract_objects_mock, contract_dispatch_objects_mock,
    ):
        result = ContractDispatchBusiness.contract_cliq_queryset_annotate_volume_on_seasonality(
            mock_query_set, 7
        )

        self.assertTrue(type(result) == MockQuerySet)

    @mock.patch(
        "contract_dispatch.models.ContractDispatch.objects.filter", return_value=[],
    )
    @mock.patch(
        "contract_dispatch.models.CliqContract.objects.filter",
        return_value=mock_query_set,
    )
    def test_contract_cliq_queryset_annotate_future_contract_volume_should_return_queryset(
        self, cliq_contract_objects_mock, contract_dispatch_objects_mock,
    ):
        result = ContractDispatchBusiness.contract_cliq_queryset_annotate_future_contract_volume(
            mock_query_set, 2020, 7
        )

        self.assertTrue(type(result) == MockQuerySet)

    @mock.patch(
        "contract_dispatch.models.ContractDispatch.objects.filter", return_value=[],
    )
    @mock.patch(
        "contract_dispatch.models.CliqContract.objects.filter",
        return_value=mock_query_set,
    )
    @mock.patch(
        "contract_dispatch.utils.is_future_contract", return_value=True,
    )
    def test_contract_cliq_queryset_annotate_future_contract_volume_for_future_should_return_queryset(
        self,
        contract_dispatch_objects_mock,
        cliq_contract_objects_mock,
        is_future_contract_mock,
    ):
        result = ContractDispatchBusiness.contract_cliq_queryset_annotate_future_contract_volume(
            mock_query_set, 3000, 12
        )

        self.assertTrue(type(result) == MockQuerySet)

    @mock.patch(
        "contract_dispatch.models.ContractDispatch.objects.filter", return_value=[],
    )
    @mock.patch(
        "contract_dispatch.models.CliqContract.objects.filter",
        return_value=mock_query_set,
    )
    def test_contract_cliq_queryset_annotate_volume_on_balance_should_return_queryset(
        self, cliq_contract_objects_mock, contract_dispatch_objects_mock,
    ):
        result = ContractDispatchBusiness.contract_cliq_queryset_annotate_volume_on_balance(
            mock_query_set, None
        )
        result_with_balance = ContractDispatchBusiness.contract_cliq_queryset_annotate_volume_on_balance(
            mock_query_set, 1
        )

        self.assertTrue(type(result) == MockQuerySet)
        self.assertTrue(type(result_with_balance) == MockQuerySet)

    @mock.patch(
        "contract_dispatch.models.ContractDispatch.objects.filter", return_value=[],
    )
    @mock.patch(
        "contract_dispatch.models.CliqContract.objects.filter",
        return_value=mock_query_set,
    )
    def test_contract_dispatch_queryset_annotate_volume_final_should_return_queryset(
        self, cliq_contract_objects_mock, contract_dispatch_objects_mock,
    ):
        result = ContractDispatchBusiness.contract_dispatch_queryset_annotate_volume_final(
            mock_query_set, 1
        )

        self.assertTrue(type(result) == MockQuerySet)

    @mock.patch(
        "contract_dispatch.models.ContractDispatch.objects.filter", return_value=[],
    )
    @mock.patch(
        "contract_dispatch.models.CliqContract.objects.filter",
        return_value=mock_query_set,
    )
    def test_contract_cliq_queryset_annotate_volume_final_should_return_queryset(
        self, cliq_contract_objects_mock, contract_dispatch_objects_mock,
    ):
        result = ContractDispatchBusiness.contract_cliq_queryset_annotate_volume_final(
            mock_query_set, None
        )
        result_with_balance = ContractDispatchBusiness.contract_cliq_queryset_annotate_volume_final(
            mock_query_set, 1
        )

        self.assertTrue(type(result) == MockQuerySet)
        self.assertTrue(type(result_with_balance) == MockQuerySet)

    # Generation tests
    # pdf generator
    @mock.patch(
        "contract_dispatch.models.ContractDispatch.objects.filter", return_value=[],
    )
    @mock.patch(
        "contract_dispatch.models.CliqContract.objects.filter",
        return_value=mock_query_set,
    )
    def test_generate_pdf_should_return_file(
        self, contract_dispatch_mock, cliq_contract_mock
    ):
        result = generate_pdf(self.mock_request)

        self.assertTrue(type(result) == bytes)

    @mock.patch(
        "contract_dispatch.models.ContractDispatch.objects.filter", return_value=[],
    )
    @mock.patch(
        "contract_dispatch.models.CliqContract.objects.filter",
        return_value=mock_query_set,
    )
    def test_generate_pdf_by_contract_should_return_file(
        self, contract_dispatch_mock, cliq_contract_mock
    ):
        result = generate_pdf_by_contract(
            self.mock_request, self.mock_contract_dispatch
        )

        self.assertTrue(type(result) == bytes)

    @mock.patch(
        "contract_dispatch.models.ContractDispatch.objects.filter", return_value=[],
    )
    @mock.patch(
        "contract_dispatch.models.CliqContract.objects.filter",
        return_value=mock_query_set,
    )
    def test_generate_pdf_contracts_to_send_should_return_file(
        self, contract_dispatch_mock, cliq_contract_mock
    ):
        result = generate_pdf_contracts_to_send(self.mock_request, 2020, 7, None)

        self.assertTrue(type(result) == bytes)

    @mock.patch(
        "contract_dispatch.models.ContractDispatch.objects.filter", return_value=[],
    )
    @mock.patch(
        "contract_dispatch.models.CliqContract.objects.filter",
        return_value=mock_query_set,
    )
    def test_generate_pdf_contracts_by_ids_should_return_file(
        self, contract_dispatch_mock, cliq_contract_mock
    ):
        result = generate_pdf_contracts_by_ids(
            self.mock_request, 2020, 7, None, [1, 2, 3]
        )

        self.assertTrue(type(result) == bytes)

    def test_generate_should_return_file(self):
        result = pdf_generate({}, "any")

        self.assertTrue(type(result) == bytes)

    # xlsx generator

    @mock.patch(
        "contract_dispatch.models.ContractDispatch.objects.filter", return_value=[],
    )
    @mock.patch(
        "contract_dispatch.models.CliqContract.objects.filter",
        return_value=mock_query_set,
    )
    @mock.patch("contract_dispatch.generators.xlsx_generator.generate",)
    def test_generate_xlsx_should_return_file(
        self, generate_mock, clic_contract_mock, contract_dispatch_mock
    ):
        result = generate_xlsx(self.mock_request)

        self.assertTrue(generate_mock.called)

    @mock.patch(
        "contract_dispatch.models.ContractDispatch.objects.filter", return_value=[],
    )
    @mock.patch(
        "contract_dispatch.models.CliqContract.objects.filter",
        return_value=mock_query_set,
    )
    @mock.patch("contract_dispatch.generators.xlsx_generator.generate",)
    def test_generate_xlsx_by_contract_should_return_file(
        self, generate_mock, clic_contract_mock, contract_dispatch_mock,
    ):
        result = generate_xlsx_by_contract(
            self.mock_request, self.mock_contract_dispatch
        )

        self.assertTrue(generate_mock.called)

    @mock.patch(
        "contract_dispatch.models.ContractDispatch.objects.filter", return_value=[],
    )
    @mock.patch(
        "contract_dispatch.models.CliqContract.objects.filter",
        return_value=mock_query_set,
    )
    @mock.patch("contract_dispatch.generators.xlsx_generator.generate",)
    def test_generate_xlsx_contracts_to_send_should_return_file(
        self, generate_mock, clic_contract_mock, contract_dispatch_mock,
    ):
        result = generate_xlsx_contracts_to_send(self.mock_request, 2020, 7, None)
        self.assertTrue(generate_mock.called)

    @mock.patch(
        "contract_dispatch.models.ContractDispatch.objects.filter", return_value=[],
    )
    @mock.patch(
        "contract_dispatch.models.CliqContract.objects.filter",
        return_value=mock_query_set,
    )
    @mock.patch("contract_dispatch.generators.xlsx_generator.generate",)
    def test_generate_xlsx_contracts_by_ids_should_return_file(
        self, generate_mock, clic_contract_mock, contract_dispatch_mock,
    ):
        result = generate_xlsx_contracts_by_ids(
            self.mock_request, 2020, 7, None, [1, 2, 3]
        )

        self.assertTrue(generate_mock.called)

    def test_generate_should_return_file(self):
        result = xlsx_generate(mock_generation_dict)

        self.assertTrue(type(result) == bytes)

    def test_empty_generate_should_return_error(self):
        with self.assertRaises(ValidationError):
            xlsx_generate([])