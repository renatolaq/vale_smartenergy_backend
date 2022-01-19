from unittest import mock
from django.test import SimpleTestCase
from usage_contract.uteis import csv_parser
from ..lib import usage_contract_export_dict, HttpRequestMock
import copy

class TestUteisCsvParser(SimpleTestCase):
    @mock.patch(
        "usage_contract.uteis.csv_parser.CTUParser.generate_data_frame", return_value=mock.MagicMock()
    )
    @mock.patch(
        "usage_contract.uteis.csv_parser.generate_pdf_from_df", return_value=mock.Mock()
    )
    def test_generate_pdf_from_df_should_call_get_pt(
        self, generate_pdf_from_df_mock, generate_data_frame
    ):
        request = HttpRequestMock({})
        request.META["HTTP_ACCEPT_LANGUAGE"] = "pt"

        dict_values = copy.deepcopy(usage_contract_export_dict)

        ctu_parser = csv_parser.CTUParser()
        result = ctu_parser.generate_pdf(dict_values, request)

        self.assertTrue(generate_data_frame.called)
        self.assertTrue(generate_pdf_from_df_mock.called)

    @mock.patch(
        "usage_contract.uteis.csv_parser.CTUParser.generate_data_frame", return_value=mock.MagicMock()
    )
    @mock.patch(
        "usage_contract.uteis.csv_parser.generate_pdf_from_df", return_value=mock.Mock()
    )
    def test_generate_pdf_from_df_should_call_get_en(
        self, generate_pdf_from_df_mock, generate_data_frame
    ):
        request = HttpRequestMock({})
        request.META["HTTP_ACCEPT_LANGUAGE"] = "en"

        dict_values = copy.deepcopy(usage_contract_export_dict)

        ctu_parser = csv_parser.CTUParser()
        result = ctu_parser.generate_pdf(dict_values, request)

        self.assertTrue(generate_data_frame.called)
        self.assertTrue(generate_pdf_from_df_mock.called)
