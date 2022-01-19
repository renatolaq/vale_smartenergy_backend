from datetime import date
from unittest import mock

from dateutil.relativedelta import relativedelta
from django.http import HttpRequest
from rest_framework import status

from usage_contract.models import (
    UsageContract,
    EnergyTransmitter,
    EnergyDistributor,
    TaxModality,
)
from django.test import SimpleTestCase

from usage_contract.serializers import (
    UsageContractDistributorSerializer,
    UsageContractTransmitterSerializer,
)
from usage_contract.tests.lib import (
    HttpRequestMock,
    gauge_dealers,
    gauge_points,
    check_module_mock,
    serializer_data_mock,
    order_by_possibilities,
    upload_file_usage_contract,
    upload_file_usage_contract_incomplete,
    usage_contract_mock,
    logs_filter_mock,
    usage_contract_enabled_mock,
    source_pme_mock,
    MockData,
    rpe_list_mock,
    tax_list_mock,
    cc_list_mock,
    cct_list_mock,
)

mock.patch("SmartEnergy.auth.check_module", check_module_mock).start()
from usage_contract import views as usage_contract_views


@mock.patch(
    "rest_framework.permissions.IsAuthenticated.has_permission",
    mock.MagicMock(return_value=True),
)
@mock.patch("SmartEnergy.auth.get_user", mock.Mock())
class TestUsageContractViews(SimpleTestCase):
    @mock.patch(
        "usage_contract.models.UsageContract.objects.filter", return_value=mock.Mock(),
    )
    def test_get_contract_number_should_filter_by_company_id_and_status_S(
        self, usage_contract_filter_mock
    ):
        request = HttpRequest()
        request.method = "GET"
        usage_contract_views.get_contract_number(request, 1)
        usage_contract_filter_mock.assert_called_with(company_id=1, status="S")

    @mock.patch(
        "usage_contract.models.UsageContract.objects.filter", return_value=mock.Mock(),
    )
    def test_get_contract_number_should_return_response_data_if_contract_exist(
        self, usage_contract_filter_mock
    ):
        request = HttpRequest()
        request.method = "GET"
        response = usage_contract_views.get_contract_number(request, 1)
        self.assertTrue(
            list(response.data.keys()) == ["id_usage_contract", "contract_number"]
        )

    @mock.patch("usage_contract.models.UsageContract.objects.filter",)
    def test_get_contract_number_should_return_error_message_if_contract_doesnt_exist(
        self, usage_contract_filter_mock
    ):
        last_mock = mock.Mock()
        last_mock.last = mock.Mock(return_value=None)

        order_by_mock = mock.Mock()
        order_by_mock.order_by.return_value = last_mock

        usage_contract_filter_mock.return_value = order_by_mock
        request = HttpRequest()
        request.method = "GET"
        response = usage_contract_views.get_contract_number(request, 1)
        self.assertTrue(response.status_code == status.HTTP_204_NO_CONTENT)
        self.assertTrue(response.data[0] == "Não há contrato valido para esta empresa")

    def test_get_contract_number_accepts_get_method_only(self):
        request = HttpRequest()
        request.method = "POST"
        response = usage_contract_views.get_contract_number(request, 1)
        self.assertTrue(response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED)

        request.method = "DELETE"
        response = usage_contract_views.get_contract_number(request, 1)
        self.assertTrue(response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED)

        request.method = "PATCH"
        response = usage_contract_views.get_contract_number(request, 1)
        self.assertTrue(response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED)

        request.method = "PUT"
        response = usage_contract_views.get_contract_number(request, 1)
        self.assertTrue(response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_check_ctu_number_accepts_get_method_only(self):
        request = HttpRequest()
        request.method = "POST"
        response = usage_contract_views.get_contract_number(request, 1)
        self.assertTrue(response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED)

        request.method = "DELETE"
        response = usage_contract_views.get_contract_number(request, 1)
        self.assertTrue(response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED)

        request.method = "PATCH"
        response = usage_contract_views.get_contract_number(request, 1)
        self.assertTrue(response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED)

        request.method = "PUT"
        response = usage_contract_views.get_contract_number(request, 1)
        self.assertTrue(response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED)

    @mock.patch("usage_contract.models.UsageContract.objects.extra",)
    def test_check_ctu_number_remove_spaces_from_parameter_and_calls_extra_with_lower_and_replace_commands(
        self, objects_extra_mock
    ):
        request = HttpRequest()
        request.method = "GET"
        _number = "1   2"
        usage_contract_views.check_ctu_number(request, _number)

        objects_extra_mock.assert_called_with(
            where=[f"LOWER(REPLACE(contract_number,' ','')) = '{'12'}'"]
        )

    @mock.patch("usage_contract.views.get_object_or_404")
    @mock.patch("usage_contract.models.UsageContract.objects.extra",)
    def test_check_ctu_number_get_by_ctu_id_if_has_it_as_parameter(
        self, objects_extra_mock, get_object_or_404_mock
    ):
        exclude_mock = mock.Mock()
        exclude_mock.exclude = mock.Mock()
        objects_extra_mock.return_value = exclude_mock

        request = HttpRequest()
        request.method = "GET"
        _number = "1   2"
        ctu_id = 1
        usage_contract_views.check_ctu_number(request, _number, ctu_id)

        self.assertTrue(get_object_or_404_mock.called)
        self.assertTrue(exclude_mock.exclude.called)

    @mock.patch("usage_contract.models.UsageContract.objects.extra",)
    def test_check_ctu_number_should_return_ctu_number_exist_false_if_ctu_not_exist(
        self, objects_extra_mock
    ):
        objects_extra_mock.return_value = None

        request = HttpRequest()
        request.method = "GET"
        _number = "1   2"
        response = usage_contract_views.check_ctu_number(request, _number)

        self.assertTrue(response.data == {"ctu_number_exist": False})
        self.assertTrue(response.status_code == status.HTTP_200_OK)

    @mock.patch("usage_contract.models.UsageContract.objects.extra", mock.Mock())
    def test_check_ctu_number_should_return_ctu_number_exist_true_and_active_false_if_exist_and_status_not_S(
        self,
    ):
        request = HttpRequest()
        request.method = "GET"
        _number = "12"
        response = usage_contract_views.check_ctu_number(request, _number)

        self.assertTrue(response.data == {"ctu_number_exist": True, "active": False})
        self.assertTrue(response.status_code == status.HTTP_200_OK)

    @mock.patch("usage_contract.models.UsageContract.objects.extra",)
    def test_check_ctu_number_should_return_ctu_number_exist_true_and_active_true_if_exists_and_status_S(
        self, objects_extra_mock
    ):
        first_mock = mock.Mock()
        first_mock.first.return_value = mock.Mock(status="S")
        objects_extra_mock.return_value = first_mock
        request = HttpRequest()
        request.method = "GET"
        _number = "12"
        response = usage_contract_views.check_ctu_number(request, _number)

        self.assertTrue(response.data == {"ctu_number_exist": True, "active": True})
        self.assertTrue(response.status_code == status.HTTP_200_OK)

    @mock.patch(
        "usage_contract.models.UsageContract.objects.filter", mock.Mock(return_value=[])
    )
    def test_renovacao_should_return_status_invalid_if_usage_contract_doesnt_exist(
        self,
    ):
        request = HttpRequest()
        request.method = "GET"
        pk = 666
        response = usage_contract_views.renovacao(request, pk)
        self.assertTrue(response.data == {"usage_contract": pk, "status": "invalid"})
        self.assertTrue(response.status_code == status.HTTP_200_OK)

    @mock.patch("usage_contract.models.UsageContract.objects.filter")
    def test_renovacao_should_call_filter_by_pk(self, usage_contract_filter_mock):
        request = HttpRequest()
        request.method = "GET"
        pk = 666
        usage_contract_filter_mock.return_value = []
        usage_contract_views.renovacao(request, pk)
        usage_contract_filter_mock.assert_called_with(pk=pk)

    @mock.patch("usage_contract.models.UsageContract.objects.filter")
    def test_renovacao_should_return_invalid_if_energy_contract_is_transmitter(
        self, usage_contract_filter_mock
    ):
        request = HttpRequest()
        request.method = "GET"
        pk = 666

        usage_contract_mock = UsageContract()
        usage_contract_mock.energy_transmitter = EnergyTransmitter()

        usage_contract_filter_mock.return_value = [usage_contract_mock]
        response = usage_contract_views.renovacao(request, pk)
        self.assertTrue(response.data == {"usage_contract": pk, "status": "invalid"})
        self.assertTrue(response.status_code == status.HTTP_200_OK)

    @mock.patch("usage_contract.models.UsageContract.objects.filter")
    def test_renovacao_should_return_invalid_if_energy_contract_is_not_transmitter_and_audit_renovation_is_status_N(
        self, usage_contract_filter_mock
    ):
        request = HttpRequest()
        request.method = "GET"
        pk = 666
        energy_distributor_mock = EnergyDistributor()
        energy_distributor_mock.audit_renovation = "N"
        usage_contract_mock = UsageContract()
        usage_contract_mock.energy_distributor = energy_distributor_mock
        usage_contract_filter_mock.return_value = [usage_contract_mock]

        response = usage_contract_views.renovacao(request, pk)
        self.assertTrue(
            response.data == {"usage_contract": pk, "status": "not_renovable"}
        )
        self.assertTrue(response.status_code == status.HTTP_200_OK)

    @mock.patch("usage_contract.models.UsageContract.objects.filter")
    def test_renovacao_should_return_doesnt_need_to_update_if_interval_of_renovation_is_lower_than_zero(
        self, usage_contract_filter_mock
    ):
        request = HttpRequest()
        request.method = "GET"
        pk = 666
        energy_distributor_mock = EnergyDistributor()
        energy_distributor_mock.audit_renovation = "S"

        usage_contract_mock = UsageContract()
        usage_contract_mock.end_date = date.today() + relativedelta(days=+181)
        usage_contract_mock.energy_distributor = energy_distributor_mock

        usage_contract_filter_mock.return_value = [usage_contract_mock]

        response = usage_contract_views.renovacao(request, pk)
        self.assertTrue(
            response.data
            == {
                "usage_contract": pk,
                "status": "same_date",
                "date": usage_contract_mock.end_date.strftime("%d/%m/%Y"),
            }
        )
        self.assertTrue(response.status_code == status.HTTP_200_OK)

    def test_renovacao_accepts_get_method_only(self):
        request = HttpRequest()
        request.method = "POST"
        response = usage_contract_views.renovacao(request, 1)
        self.assertTrue(response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED)

        request.method = "DELETE"
        response = usage_contract_views.renovacao(request, 1)
        self.assertTrue(response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED)

        request.method = "PATCH"
        response = usage_contract_views.renovacao(request, 1)
        self.assertTrue(response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED)

        request.method = "PUT"
        response = usage_contract_views.renovacao(request, 1)
        self.assertTrue(response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED)

    @mock.patch("usage_contract.models.TaxModality.objects.filter", mock.MagicMock())
    @mock.patch("usage_contract.models.UsageContract.save")
    @mock.patch("usage_contract.models.UsageContract.objects.filter")
    def test_renovacao_should_update_contract_if_interval_of_renovation_is_greater_or_equal_than_zero(
        self, usage_contract_filter_mock, usage_contract_save_mock
    ):
        request = HttpRequest()
        request.method = "GET"
        pk = 666
        renovation_period = 10
        energy_distributor_mock = EnergyDistributor()
        energy_distributor_mock.audit_renovation = "S"
        energy_distributor_mock.renovation_period = renovation_period

        usage_contract_mock = UsageContract()
        usage_contract_mock.end_date = date.today() + relativedelta(days=+180)
        usage_contract_mock.energy_distributor = energy_distributor_mock

        usage_contract_filter_mock.return_value = [usage_contract_mock]
        result_date = usage_contract_mock.end_date + relativedelta(
            months=+int(renovation_period)
        )
        response = usage_contract_views.renovacao(request, pk)

        self.assertDictEqual(
            response.data,
            {
                "usage_contract": pk,
                "status": "new_date",
                "date": result_date.strftime("%d/%m/%Y"),
            },
        )
        self.assertTrue(response.status_code == status.HTTP_200_OK)
        self.assertTrue(usage_contract_save_mock.called)

    @mock.patch(
        "usage_contract.views.UsageContractViewSet.filter_queryset", mock.Mock(),
    )
    @mock.patch(
        "usage_contract.views.UsageContractViewSet.get_queryset", mock.Mock(),
    )
    @mock.patch(
        "usage_contract.views.UsageContractViewSet.get_serializer", mock.Mock(),
    )
    @mock.patch(
        "usage_contract.uteis.csv_parser.CTUParser.generate_data_frame",
        return_value=mock.Mock(),
    )
    def test_export_file_should_call_xlsx_generator(
        self, generate_data_frame_mock,
    ):
        request = HttpRequestMock({"type_file": "xlsx"})
        request.method = "GET"

        usage_contract_view_set = usage_contract_views.UsageContractViewSet()
        try:
            usage_contract_view_set.export_file(request)
        except StopIteration:
            pass
        self.assertTrue(generate_data_frame_mock.called)

    @mock.patch(
        "usage_contract.views.UsageContractViewSet.filter_queryset",
        return_value=mock.Mock(),
    )
    @mock.patch(
        "usage_contract.views.UsageContractViewSet.get_queryset",
        return_value=mock.Mock(),
    )
    @mock.patch(
        "usage_contract.views.UsageContractViewSet.get_serializer",
        return_value=mock.Mock(),
    )
    @mock.patch(
        "usage_contract.uteis.csv_parser.CTUParser.generate_pdf",
        return_value=mock.Mock(),
    )
    @mock.patch(
        "django.core.files.storage.FileSystemStorage.open",
        mock.mock_open(read_data="data"),
    )
    def test_export_file_should_call_pdf_generator(
        self,
        filter_queryset_mock,
        get_queryset_mock,
        get_serializer_mock,
        generate_pdf_mock,
    ):
        request = HttpRequestMock({"type_file": "pdf"})
        request.method = "GET"

        usage_contract_view_set = usage_contract_views.UsageContractViewSet()
        usage_contract_view_set.export_file(request)
        self.assertTrue(generate_pdf_mock.called)

    @mock.patch(
        "company.models.Company.objects.filter", return_value=mock.Mock(),
    )
    def test_get_queryset_should_filter_company(self, company_filter_mock):
        energy_dealer_view_set = usage_contract_views.EnergyDealerViewSet()

        energy_dealer_view_set.request = HttpRequestMock({"data": "data"})

        energy_dealer_view_set.get_queryset()

        company_filter_mock.assert_called_with(
            company_dealership__id_gauge_point__id_company__isnull=False
        )

    @mock.patch(
        "company.models.Company.objects.filter", return_value=mock.Mock(),
    )
    @mock.patch(
        "company.models.Company.objects.get", return_value=mock.Mock(),
    )
    @mock.patch(
        "gauge_point.models.GaugePoint.objects.filter", return_value=gauge_points,
    )
    @mock.patch(
        "gauge_point.models.GaugeEnergyDealership.objects.filter",
        return_value=gauge_dealers,
    )
    def test_get_queryset_should_filter_company_gauge_gauge_dealership(
        self,
        company_filter_mock,
        company_get_mock,
        gauge_point_mock,
        gauge_energy_dealership_mock,
    ):
        energy_dealer_view_set = usage_contract_views.EnergyDealerViewSet()

        energy_dealer_view_set.request = HttpRequestMock({"id": "1"})

        energy_dealer_view_set.get_queryset()

        self.assertTrue(company_filter_mock.called)
        self.assertTrue(company_get_mock.called)
        self.assertTrue(gauge_point_mock.called)
        self.assertTrue(gauge_energy_dealership_mock.called)

    @mock.patch("usage_contract.models.UsageContract.save", mock.Mock())
    @mock.patch("usage_contract.models.TaxModality.objects.filter")
    @mock.patch("usage_contract.models.TaxModality.save")
    @mock.patch("usage_contract.models.UsageContract.objects.filter")
    def test_renovacao_should_update_tax_modality_if_has_tax_modality_and_end_date_if_interval_of_renovation_is_greater_or_equal_than_zero(
        self,
        usage_contract_filter_mock,
        tax_modality_save_mock,
        tax_modality_filter_mock,
    ):
        request = HttpRequest()
        request.method = "GET"
        pk = 666
        renovation_period = 10
        energy_distributor_mock = EnergyDistributor()
        energy_distributor_mock.audit_renovation = "S"
        energy_distributor_mock.renovation_period = renovation_period

        usage_contract_mock = UsageContract()
        usage_contract_mock.end_date = date.today() + relativedelta(days=+180)
        usage_contract_mock.energy_distributor = energy_distributor_mock

        usage_contract_filter_mock.return_value = [usage_contract_mock]
        result_date = usage_contract_mock.end_date + relativedelta(
            months=+int(renovation_period)
        )

        order_by_mock = mock.Mock()
        order_by_mock.order_by.return_value = [TaxModality()]
        tax_modality_filter_mock.return_value = order_by_mock

        response = usage_contract_views.renovacao(request, pk)

        self.assertDictEqual(
            response.data,
            {
                "usage_contract": pk,
                "status": "new_date",
                "date": result_date.strftime("%d/%m/%Y"),
            },
        )
        self.assertTrue(response.status_code == status.HTTP_200_OK)
        self.assertTrue(tax_modality_save_mock.called)

    @mock.patch(
        "usage_contract.views.UsageContractViewSet.paginate_queryset",
        return_value=mock.Mock(),
    )
    @mock.patch(
        "usage_contract.views.UsageContractViewSet.get_serializer",
        return_value=serializer_data_mock,
    )
    @mock.patch(
        "usage_contract.views.UsageContractViewSet.get_paginated_response",
        return_value=serializer_data_mock,
    )
    def test_list_usage_contract_should_call_serializer_queryset_methods(
        self, paginate_queryset_mock, get_serializer_mock, get_paginated_response_mock
    ):
        usage_contract_view_set = usage_contract_views.UsageContractViewSet()

        for order_by in order_by_possibilities:
            request = HttpRequestMock(
                {
                    "orderBy": order_by,
                    "start_date": "2020-10-20",
                    "end_date": "2020-10-20",
                    "create_date": "2020-10-20",
                }
            )

            usage_contract_view_set.request = request

            usage_contract_view_set.list(request)

            self.assertTrue(paginate_queryset_mock.called)
            self.assertTrue(get_serializer_mock.called)
            self.assertTrue(get_paginated_response_mock.called)

    @mock.patch(
        "usage_contract.views.UsageContractViewSet.paginate_queryset",
        return_value=None,
    )
    @mock.patch(
        "usage_contract.views.UsageContractViewSet.get_serializer",
        return_value=serializer_data_mock,
    )
    def test_list_usage_contract_should_return_with_none_queryset(
        self, paginate_queryset_mock, get_serializer_mock
    ):
        usage_contract_view_set = usage_contract_views.UsageContractViewSet()

        request = HttpRequestMock({})

        usage_contract_view_set.request = request

        response = usage_contract_view_set.list(request)

        self.assertTrue(paginate_queryset_mock.called)
        self.assertTrue(get_serializer_mock.called)
        self.assertEqual(response.status_code, 200)

    def test_list_usage_contract_should_raise_exception(self):
        usage_contract_view_set = usage_contract_views.UsageContractViewSet()

        request = HttpRequestMock({"start_date": "wrong date format"})

        usage_contract_view_set.request = request

        response = usage_contract_view_set.list(request)

        self.assertEqual(response.status_code, 400)

    @mock.patch(
        "usage_contract.models.UploadFileUsageContract.objects.filter",
        return_value=upload_file_usage_contract,
    )
    @mock.patch(
        "os.path.exists", return_value=True,
    )
    @mock.patch(
        "os.path.splitext", return_value=("some_file", ".pdf"),
    )
    @mock.patch(
        "builtins.open", mock.mock_open(read_data="data"),
    )
    def test_download_file_should_return_file_response(
        self,
        splitext_mock,
        os_path_exists_mock,
        upload_file_usage_contract_objects_filter_mock,
    ):
        request = HttpRequestMock({})
        request.method = "GET"

        response = usage_contract_views.download_file(request, 1)

        self.assertEqual(type(response).__name__, "FileResponse")
        self.assertTrue(splitext_mock)
        self.assertTrue(os_path_exists_mock)
        self.assertTrue(upload_file_usage_contract_objects_filter_mock)

    @mock.patch(
        "usage_contract.models.UploadFileUsageContract.objects.filter",
        return_value=upload_file_usage_contract,
    )
    def test_download_file_should_return_file_not_found_response(
        self, upload_file_usage_contract_objects_filter_mock
    ):
        request = HttpRequestMock({})
        request.method = "GET"

        response = usage_contract_views.download_file(request, 1)
        self.assertEqual(response.status_code, 400)

    @mock.patch(
        "usage_contract.models.UploadFileUsageContract.objects.filter",
        return_value=upload_file_usage_contract_incomplete,
    )
    def test_download_file_should_return_exception(
        self, upload_file_usage_contract_objects_filter_mock
    ):
        request = HttpRequestMock({})
        request.method = "GET"

        response = usage_contract_views.download_file(request, 1)
        self.assertEqual(response.status_code, 400)

    @mock.patch("usage_contract.models.TypeUsageContract.objects.filter")
    def test_if_contract_type_is_1_return_distributor_serializer(
        self, type_usage_contract_filter_mock
    ):
        usage_contract_view_set = usage_contract_views.UsageContractViewSet()
        pk = 666
        request = HttpRequest()
        request.data = {"usage_contract_type": pk}
        type_usage_contract_filter_mock.return_value = [
            mock.Mock(id_usage_contract_type=1)
        ]
        returned_serializer = usage_contract_view_set.choose_serialize(request)
        type_usage_contract_filter_mock.assert_called_with(pk=pk)
        self.assertIs(returned_serializer, UsageContractDistributorSerializer)

    @mock.patch("usage_contract.models.TypeUsageContract.objects.filter")
    def test_if_contract_type_is_2_return_transmitter_serializer(
        self, type_usage_contract_filter_mock
    ):
        usage_contract_view_set = usage_contract_views.UsageContractViewSet()
        pk = 666
        request = HttpRequest()
        request.data = {"usage_contract_type": pk}
        type_usage_contract_filter_mock.return_value = [
            mock.Mock(id_usage_contract_type=2)
        ]
        returned_serializer = usage_contract_view_set.choose_serialize(request)
        type_usage_contract_filter_mock.assert_called_with(pk=pk)
        self.assertIs(returned_serializer, UsageContractTransmitterSerializer)

    def test_usage_filters_should_contain_company_and_basics_contract_info(self):
        usage_contract_filter = usage_contract_views.UsageContractFilter()
        required_filters = [
            "usage_contract_type",
            "create_date",
            "company_name",
            "company_city",
            "company_state",
            "company_cnpj",
            "energy_dealer",
            "agent_cnpj",
            "connection_point",
            "contract_number",
            "rated_voltage",
            "bought_voltage",
            "group",
            "subgroup",
            "start_date",
            "end_date",
            "status",
        ]
        self.assertListEqual(
            list(usage_contract_filter.filters.keys()), required_filters
        )

    @mock.patch(
        "usage_contract.views.UsageContractViewSet.perform_create",
        return_value=mock.Mock(),
    )
    @mock.patch(
        "usage_contract.views.UsageContractViewSet.choose_serialize",
        return_value=mock.Mock(),
    )
    def test_create_usage_contract_should_call_perform_create(
        self, perform_create_mock, choose_serialize_mock
    ):
        usage_contract_view_set = usage_contract_views.UsageContractViewSet()

        request = HttpRequestMock({})
        request.data = {
            "peak_end_time": "",
            "peak_begin_time": "",
            "energy_distributor": {
                "pk": 1,
                "aneel_publication": "",
                "audit_renovation": None,
            },
            "energy_transmitter": {
                "pk": 1,
                "aneel_publication": "",
                "audit_renovation": "",
            },
            "rate_post_exception": None,
            "upload_file": [{"id_upload_file_usage_contract": 1}],
        }

        usage_contract_view_set.request = request

        response = usage_contract_view_set.create(request)

        self.assertTrue(perform_create_mock.called)
        self.assertTrue(choose_serialize_mock.called)
        self.assertEqual(response.status_code, 201)

    def test_create_usage_contract_should_raise_exception(self):
        usage_contract_view_set = usage_contract_views.UsageContractViewSet()

        request = HttpRequestMock({})
        request.data = {
            "peak_end_time": "",
            "peak_begin_time": "",
            "energy_distributor": {
                "pk": 1,
                "aneel_publication": "",
                "audit_renovation": "",
            },
            "energy_transmitter": {
                "pk": 1,
                "aneel_publication": "",
                "audit_renovation": "",
            },
            "rate_post_exception": None,
            "upload_file": [{"id_upload_file_usage_contract": 1}],
        }
        request.auth = None

        usage_contract_view_set.request = request

        response = usage_contract_view_set.create(request)

        self.assertEqual(response.status_code, 400)

    @mock.patch(
        "usage_contract.models.UsageContract.objects.get",
        return_value=usage_contract_mock,
    )
    @mock.patch(
        "usage_contract.models.UploadFileUsageContract.objects.get",
        return_value=mock.Mock(),
    )
    @mock.patch(
        "usage_contract.models.UploadFileUsageContract.objects.filter",
        return_value=mock.Mock(),
    )
    @mock.patch(
        "usage_contract.serializers.UploadFileUsageContractSerializer",
        return_value=mock.Mock(),
    )
    @mock.patch(
        "usage_contract.serializers.UploadFileUsageContractSerializer.save",
        return_value=mock.Mock(),
    )
    @mock.patch(
        "usage_contract.models.UsageContract.upload_file", return_value=mock.Mock(),
    )
    @mock.patch(
        "usage_contract.models.UsageContract.save", return_value=mock.Mock(),
    )
    @mock.patch(
        "gauge_point.models.GaugePoint.objects.filter", return_value=gauge_points,
    )
    @mock.patch(
        "core.models.Log.objects.filter", return_value=logs_filter_mock,
    )
    @mock.patch(
        "core.models.Log.save", return_value=logs_filter_mock,
    )
    def test_update_usage_contract_should_inactivate_and_save_logs(
        self,
        log_save_mock,
        log_objects_filter_mock,
        gauge_point_objects_filter_mock,
        usage_contract_save_mock,
        usage_contract_upload_file_set_mock,
        upload_file_usage_contract_serializer_save_mock,
        upload_file_usage_contract_serializer_mock,
        upload_file_usage_contract_objects_filter_mock,
        upload_file_usage_contract_objects_get_mock,
        usage_contract_objects_get_mock,
    ):
        usage_contract_view_set = usage_contract_views.UsageContractViewSet()

        request = HttpRequestMock({})
        request.data = {
            "peak_end_time": "",
            "peak_begin_time": "",
            "energy_distributor": {
                "pk": 1,
                "aneel_publication": "",
                "audit_renovation": None,
            },
            "energy_transmitter": {
                "pk": 1,
                "aneel_publication": "",
                "audit_renovation": "",
                "cct": [{"end_date": ""}],
            },
            "rate_post_exception": None,
            "upload_file": [{"id_upload_file_usage_contract": 1, "file_path": "path"}],
            "justification": "some justification",
            "status": "S",
        }

        usage_contract_view_set.request = request

        response = usage_contract_view_set.update(request, pk=1)

        self.assertTrue(log_save_mock.called)
        self.assertTrue(usage_contract_save_mock.called)
        self.assertTrue(upload_file_usage_contract_serializer_save_mock.called)
        self.assertTrue(usage_contract_objects_get_mock.called)
        self.assertEqual(response.status_code, 200)

    @mock.patch(
        "usage_contract.models.UsageContract.objects.get",
        return_value=usage_contract_enabled_mock,
    )
    @mock.patch(
        "usage_contract.models.UploadFileUsageContract.objects.get",
        return_value=mock.Mock(),
    )
    @mock.patch(
        "usage_contract.models.UploadFileUsageContract.objects.filter",
        return_value=mock.Mock(),
    )
    @mock.patch(
        "usage_contract.serializers.UploadFileUsageContractSerializer",
        return_value=mock.Mock(),
    )
    @mock.patch(
        "usage_contract.serializers.UploadFileUsageContractSerializer.save",
        return_value=mock.Mock(),
    )
    @mock.patch(
        "usage_contract.models.UsageContract.upload_file", return_value=mock.Mock(),
    )
    @mock.patch(
        "usage_contract.models.UsageContract.save", return_value=mock.Mock(),
    )
    @mock.patch(
        "gauge_point.models.GaugePoint.objects.filter", return_value=gauge_points,
    )
    @mock.patch(
        "core.models.Log.objects.filter", return_value=logs_filter_mock,
    )
    @mock.patch(
        "core.models.Log.save", return_value=logs_filter_mock,
    )
    @mock.patch(
        "gauge_point.models.SourcePme.objects.filter", return_value=source_pme_mock,
    )
    def test_update_usage_contract_should_activate_and_save_logs(
        self,
        source_pme_objects_filter_mock,
        log_save_mock,
        log_objects_filter_mock,
        gauge_point_objects_filter_mock,
        usage_contract_save_mock,
        usage_contract_upload_file_set_mock,
        upload_file_usage_contract_serializer_save_mock,
        upload_file_usage_contract_serializer_mock,
        upload_file_usage_contract_objects_filter_mock,
        upload_file_usage_contract_objects_get_mock,
        usage_contract_objects_get_mock,
    ):
        usage_contract_view_set = usage_contract_views.UsageContractViewSet()

        request = HttpRequestMock({})
        request.data = {
            "peak_end_time": "",
            "peak_begin_time": "",
            "energy_distributor": {
                "pk": 1,
                "aneel_publication": "",
                "audit_renovation": None,
            },
            "energy_transmitter": {
                "pk": 1,
                "aneel_publication": "",
                "audit_renovation": "",
                "cct": [{"end_date": ""}],
            },
            "rate_post_exception": None,
            "upload_file": [{"id_upload_file_usage_contract": 1, "file_path": "path"}],
            "justification": "some justification",
            "status": "S",
        }

        usage_contract_view_set.request = request

        response = usage_contract_view_set.update(request, pk=1)

        self.assertTrue(log_save_mock.called)
        self.assertTrue(usage_contract_save_mock.called)
        self.assertTrue(upload_file_usage_contract_serializer_save_mock.called)
        self.assertTrue(usage_contract_objects_get_mock.called)
        self.assertEqual(response.status_code, 200)

    @mock.patch(
        "usage_contract.models.UsageContract.objects.get",
        return_value=usage_contract_mock,
    )
    def test_update_usage_contract_should_return_continue(
        self, usage_contract_objects_get_mock
    ):
        usage_contract_view_set = usage_contract_views.UsageContractViewSet()

        request = HttpRequestMock({})
        request.data = {}

        usage_contract_view_set.request = request

        response = usage_contract_view_set.update(request, pk=1)

        self.assertTrue(response.status_code, 100)

    @mock.patch(
        "usage_contract.models.UsageContract.objects.get",
        return_value=usage_contract_mock,
    )
    @mock.patch(
        "usage_contract.views.UsageContractViewSet.perform_update",
        return_value=mock.Mock(),
    )
    @mock.patch(
        "usage_contract.views.UsageContractViewSet.choose_serialize",
        return_value=mock.Mock(),
    )
    @mock.patch(
        "usage_contract.views.UsageContractViewSet.get_object",
        return_value=mock.Mock(),
    )
    def test_update_usage_contract_should_perform_update(
        self,
        get_object_mock,
        choose_serialize_mock,
        perform_update_mock,
        usage_contract_objects_get_mock,
    ):
        usage_contract_view_set = usage_contract_views.UsageContractViewSet()

        request = HttpRequestMock({})
        request.data = {
            "peak_end_time": "",
            "peak_begin_time": "",
            "energy_distributor": {
                "pk": 1,
                "aneel_publication": "",
                "audit_renovation": None,
            },
            "energy_transmitter": {
                "pk": 1,
                "aneel_publication": "",
                "audit_renovation": "",
                "cct": [{"end_date": ""}],
            },
            "rate_post_exception": None,
            "status": "S",
            "teste": "dorime",
        }

        usage_contract_view_set.request = request
        response = usage_contract_view_set.update(request, pk=1)

        self.assertTrue(get_object_mock.called)
        self.assertTrue(choose_serialize_mock)
        self.assertTrue(perform_update_mock)
        self.assertTrue(usage_contract_objects_get_mock)
        self.assertEqual(response.status_code, 200)

    @mock.patch(
        "usage_contract.views.UploadFileUsageContractViewSet.get_serializer",
        return_value=mock.Mock(),
    )
    @mock.patch(
        "usage_contract.views.UploadFileUsageContractViewSet.perform_create",
        return_value=mock.Mock(),
    )
    @mock.patch(
        "usage_contract.views.UploadFileUsageContractViewSet.get_success_headers",
        return_value=mock.Mock(),
    )
    def test_upload_file_usage_contract_view_set_create_should_return_exception(
        self, get_success_headers_mock, perform_create_mock, get_serializer_mock
    ):

        request = HttpRequestMock({})
        request.data = MockData()
        request.data.file_path = "some/path"

        upload_file_usage_contract_view_set = (
            usage_contract_views.UploadFileUsageContractViewSet()
        )
        upload_file_usage_contract_view_set.request = request

        result = upload_file_usage_contract_view_set.create(request)

        self.assertEqual(result.status_code, 400)

    @mock.patch(
        "core.models.Log.objects.filter", return_value=None,
    )
    def test_session_log_should_return_exception(self, log_objects_filter):
        request = HttpRequestMock({})
        request.method = "GET"

        result = usage_contract_views.session_log(request, 1)

        self.assertEqual(result.status_code, 400)

    @mock.patch(
        "usage_contract.views.UploadFileUsageContractViewSet.get_serializer",
        return_value=mock.Mock(),
    )
    @mock.patch(
        "usage_contract.views.UploadFileUsageContractViewSet.perform_create",
        return_value=mock.Mock(),
    )
    @mock.patch(
        "usage_contract.views.UploadFileUsageContractViewSet.get_success_headers",
        return_value=[],
    )
    def test_upload_file_usage_contract_view_set_create_should_perform_create(
        self, get_success_headers_mock, perform_create_mock, get_serializer_mock
    ):

        request = HttpRequestMock({})
        request.data = MockData()
        request.data.file_path = "some/path"

        upload_file_usage_contract_view_set = (
            usage_contract_views.UploadFileUsageContractViewSet()
        )
        upload_file_usage_contract_view_set.request = request

        result = upload_file_usage_contract_view_set.create(request)

        self.assertEqual(result.status_code, 201)
        self.assertTrue(get_success_headers_mock.called)
        self.assertTrue(perform_create_mock.called)
        self.assertTrue(get_serializer_mock.called)

    @mock.patch(
        "usage_contract.views.UploadFileUsageContractViewSet.filter_queryset",
        return_value=mock.Mock(),
    )
    @mock.patch(
        "usage_contract.views.UploadFileUsageContractViewSet.paginate_queryset",
        return_value=mock.Mock(),
    )
    @mock.patch(
        "usage_contract.views.UploadFileUsageContractViewSet.get_paginated_response",
        return_value=mock.Mock(),
    )
    @mock.patch(
        "usage_contract.views.UploadFileUsageContractViewSet.get_serializer",
        return_value=mock.Mock(),
    )
    def test_upload_file_usage_contract_view_set_list_paginated(
        self,
        filter_queryset_mock,
        paginate_queryset_mock,
        get_paginated_response_mock,
        get_serializer_mock,
    ):
        request = HttpRequestMock({})

        upload_file_usage_contract_view_set = (
            usage_contract_views.UploadFileUsageContractViewSet()
        )
        upload_file_usage_contract_view_set.request = request

        result = upload_file_usage_contract_view_set.list(request)

        self.assertTrue(filter_queryset_mock.called)
        self.assertTrue(paginate_queryset_mock.called)
        self.assertTrue(get_paginated_response_mock.called)
        self.assertTrue(get_serializer_mock.called)

    @mock.patch(
        "usage_contract.views.UploadFileUsageContractViewSet.filter_queryset",
        return_value=mock.Mock(),
    )
    @mock.patch(
        "usage_contract.views.UploadFileUsageContractViewSet.paginate_queryset",
        return_value=None,
    )
    @mock.patch(
        "usage_contract.views.UploadFileUsageContractViewSet.get_serializer",
        return_value=mock.Mock(),
    )
    def test_upload_file_usage_contract_view_set_list_not_paginated(
        self, filter_queryset_mock, paginate_queryset_mock, get_serializer_mock,
    ):
        request = HttpRequestMock({})

        upload_file_usage_contract_view_set = (
            usage_contract_views.UploadFileUsageContractViewSet()
        )
        upload_file_usage_contract_view_set.request = request

        result = upload_file_usage_contract_view_set.list(request)

        self.assertTrue(filter_queryset_mock.called)
        self.assertTrue(paginate_queryset_mock.called)
        self.assertTrue(get_serializer_mock.called)

    @mock.patch(
        "core.models.Log.objects.filter", return_value=logs_filter_mock,
    )
    @mock.patch("usage_contract.uteis.ctu_json.CTUJson.get_dic_log", return_value={})
    @mock.patch(
        "usage_contract.models.RatePostException.objects.filter",
        return_value=rpe_list_mock,
    )
    @mock.patch(
        "usage_contract.models.TaxModality.objects.filter", return_value=tax_list_mock,
    )
    @mock.patch(
        "usage_contract.models.ContractCycles.objects.filter",
        return_value=cc_list_mock,
    )
    @mock.patch(
        "usage_contract.models.Cct.objects.filter", return_value=cct_list_mock,
    )
    def test_session_log_should_return_correctly(
        self,
        cct_objects_filter,
        contract_cycles_objects_filter,
        tax_modality_objects_filter,
        rate_post_exception_objects_filter,
        get_dic_log_mock,
        log_objects_filter,
    ):
        request = HttpRequestMock({})
        request.method = "GET"

        result = usage_contract_views.session_log(request, 1)

        self.assertEqual(result.status_code, 200)
        self.assertTrue(cct_objects_filter)
        self.assertTrue(contract_cycles_objects_filter)
        self.assertTrue(tax_modality_objects_filter)
        self.assertTrue(rate_post_exception_objects_filter)
        self.assertTrue(get_dic_log_mock)
        self.assertTrue(log_objects_filter)
