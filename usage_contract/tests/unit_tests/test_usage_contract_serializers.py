from datetime import date, timedelta
from unittest import mock
from unittest.mock import ANY
from rest_framework.exceptions import ValidationError
from django.test import SimpleTestCase
from usage_contract import serializers as usage_contract_serializers
from usage_contract.tests.lib import (
    tax_list_mock,
    tax_list_2_mock,
    tax_list_dict_mock,
    tax_list_dict_2_mock,
    energy_distributor_mock,
    usage_contract_queryset_mock,
    QuerysetMock,
    rate_post_exception_list_mock,
    rate_post_exception_list_dict_mock,
    rate_post_exception_list_dict_2_mock,
    cct_list_mock,
    cct_list_2_mock,
    cct_list_dict_mock,
    cct_list_dict_2_mock,
    usage_contract_mock,
    cc_list_mock,
    cc_list_2_mock,
    cc_list_dict_2_mock,
    MockFile,
)
from usage_contract.models import (
    EnergyDistributor,
    TaxModality,
    UsageContract,
    EnergyTransmitter,
)


class TestUsageContractViews(SimpleTestCase):
    def test_detach_values_should_return_rate_post_and_tax_modality_if_energy_distributor(
        self,
    ):
        tm_response = "tm_response"
        rpe_response = "rpe_response"
        response = usage_contract_serializers.detach_values(
            validated_data={
                "energy_distributor": {"tax_modality": tm_response},
                "rate_post_exception": rpe_response,
            },
            contract_type="energy_distributor",
        )

        self.assertTrue(response == ({}, rpe_response, tm_response))

    def test_detach_values_should_return_rate_post_cct_and_contract_cyles_if_not_energy_distributor(
        self,
    ):
        cct_response = "cct_response"
        cc_response = "cc_response"
        rpe_response = "rpe_response"
        response = usage_contract_serializers.detach_values(
            validated_data={
                "energy_transmitter": {
                    "cct": cct_response,
                    "contract_cycles": cc_response,
                },
                "rate_post_exception": rpe_response,
            },
            contract_type="energy_transmitter",
        )

        self.assertTrue(response == ({}, rpe_response, "cct_response", "cc_response"))

    def test_cct_serializer_fields(self):
        cct_serializer = usage_contract_serializers.CctSerializer()
        fields = [
            "id_cct",
            "cct_number",
            "length",
            "destination",
            "begin_date",
            "end_date",
            "contract_value",
        ]

        self.assertTrue(set(fields).issubset(set(cct_serializer.fields.keys())))

    def test_contract_cycles_serializer_fields(self):
        cc_serializer = usage_contract_serializers.ContractCyclesSerializer()
        fields = [
            "id_contract_cycles",
            "begin_date",
            "end_date",
            "peak_must",
            "peak_tax",
            "off_peak_must",
            "off_peak_tax",
        ]

        self.assertTrue(set(fields).issubset(set(cc_serializer.fields.keys())))

    def test_tax_modality_serializer_fields(self):
        tm_serializer = usage_contract_serializers.TaxModalitySerializer()
        fields = [
            "id_tax_modality",
            "begin_date",
            "end_date",
            "peak_musd",
            "peak_tax",
            "off_peak_musd",
            "off_peak_tax",
            "unique_musd",
            "unique_tax",
        ]

        self.assertTrue(set(fields).issubset(set(tm_serializer.fields.keys())))

    def test_company_serializer_fields(self):
        company_serializer = usage_contract_serializers.CompanySerializer()
        fields = ["id_company", "company_name", "state_number", "id_address"]

        self.assertTrue(set(fields).issubset(set(company_serializer.fields.keys())))

    def test_energy_dealer_serializer_fields(self):
        energy_dealer_serializer = usage_contract_serializers.EnergyDealerSerializer()
        fields = [
            "id_company",
            "company_name",
            "state_number",
            "id_address",
            "connection_points",
        ]

        self.assertTrue(
            set(fields).issubset(set(energy_dealer_serializer.fields.keys()))
        )

    def test_energy_distributor_serializer_fields(self):
        energy_distributor_serializer = (
            usage_contract_serializers.EnergyDistributorSerializer()
        )
        fields = [
            "pn",
            "installation",
            "renovation_period",
            "audit_renovation",
            "aneel_resolution",
            "aneel_publication",
            "tax_modality",
            "hourly_tax_modality",
        ]

        self.assertTrue(
            set(fields).issubset(set(energy_distributor_serializer.fields.keys()))
        )

    def test_energy_transmitter_serializer_fields(self):
        energy_transmitter_serializer = (
            usage_contract_serializers.EnergyTransmitterSerializer()
        )
        fields = [
            "ons_code",
            "aneel_resolution",
            "aneel_publication",
            "cct",
            "contract_cycles",
            "renovation_period",
            "audit_renovation",
        ]

        self.assertTrue(
            set(fields).issubset(set(energy_transmitter_serializer.fields.keys()))
        )

    def test_rated_voltage_serializer_fields(self):
        rated_voltage_serializer = usage_contract_serializers.RatedVoltageSerializer()
        fields = ["id_rated_voltage", "voltages", "group", "subgroup"]

        self.assertTrue(
            set(fields).issubset(set(rated_voltage_serializer.fields.keys()))
        )

    def test_rate_post_exception_serializer_fields(self):
        rate_post_serializer = usage_contract_serializers.RatePostExceptionSerializer()
        fields = [
            "id_rate_post_exception",
            "begin_hour_clock",
            "end_hour_clock",
            "begin_date",
            "end_date",
        ]

        self.assertTrue(set(fields).issubset(set(rate_post_serializer.fields.keys())))

    def test_type_usage_serializer_fields(self):
        type_usage_serializer = usage_contract_serializers.TypeUsageContractSerializer()
        fields = ["id_usage_contract_type", "description"]

        self.assertTrue(set(fields).issubset(set(type_usage_serializer.fields.keys())))

    def test_usage_contract_simple_serializer_fields(self):
        usage_contract_simple = (
            usage_contract_serializers.UsageContractSimpleSerializer()
        )
        fields = [
            "id_usage_contract",
            "usage_contract_type",
            "companys",
            "energy_dealers",
            "contract_number",
            "rated_voltage",
            "bought_voltage",
            "tolerance_range",
            "power_factor",
            "peak_begin_time",
            "peak_end_time",
            "contract_value",
            "start_date",
            "end_date",
            "create_date",
            "status",
            "connection_point",
        ]

        self.assertTrue(set(fields).issubset(set(usage_contract_simple.fields.keys())))

    def test_upload_file_usage_contract_serializer_fields(self):
        upload_file_usage_contract = (
            usage_contract_serializers.UploadFileUsageContractSerializer()
        )
        fields = [
            "id_upload_file_usage_contract",
            "file_name",
            "file_path",
            "file_version",
            "observation",
            "date_upload",
            "id_usage_contract",
        ]

        self.assertTrue(
            set(fields).issubset(set(upload_file_usage_contract.fields.keys()))
        )

    def test_usage_contract_complete_serializer_fields(self):
        usage_contract_complete = (
            usage_contract_serializers.UsageContractCompleteSerializer()
        )
        fields = [
            "id_usage_contract",
            "usage_contract_type",
            "companys",
            "energy_dealers",
            "contract_number",
            "rated_voltage",
            "bought_voltage",
            "tolerance_range",
            "power_factor",
            "peak_begin_time",
            "peak_end_time",
            "contract_value",
            "rate_post_exception",
            "energy_distributor",
            "energy_transmitter",
            "start_date",
            "end_date",
            "observation",
            "create_date",
            "status",
            "upload_file",
            "connection_point",
        ]

        self.assertTrue(
            set(fields).issubset(set(usage_contract_complete.fields.keys()))
        )

    def test_usage_contract_distributor_serializer_fields(self):
        usage_contract_distributor = (
            usage_contract_serializers.UsageContractDistributorSerializer()
        )
        fields = [
            "id_usage_contract",
            "usage_contract_type",
            "company",
            "energy_dealer",
            "contract_number",
            "rated_voltage",
            "bought_voltage",
            "tolerance_range",
            "power_factor",
            "peak_begin_time",
            "peak_end_time",
            "contract_value",
            "rate_post_exception",
            "energy_distributor",
            "start_date",
            "end_date",
            "observation",
            "create_date",
            "status",
            "upload_file",
            "connection_point",
        ]

        self.assertTrue(
            set(fields).issubset(set(usage_contract_distributor.fields.keys()))
        )

    def test_usage_contract_transmitter_serializer_fields(self):
        usage_contract_transmitter = (
            usage_contract_serializers.UsageContractTransmitterSerializer()
        )
        fields = (
            "id_usage_contract",
            "usage_contract_type",
            "company",
            "energy_dealer",
            "contract_number",
            "rated_voltage",
            "bought_voltage",
            "tolerance_range",
            "power_factor",
            "peak_begin_time",
            "peak_end_time",
            "contract_value",
            "rate_post_exception",
            "energy_transmitter",
            "start_date",
            "end_date",
            "observation",
            "create_date",
            "status",
            "upload_file",
            "connection_point",
        )

        self.assertTrue(
            set(fields).issubset(set(usage_contract_transmitter.fields.keys()))
        )

    def test_energy_distributor_serializer_validate_should_raise_validation_error_if_unique_msd_or_unique_tax_doesnt_exist_and_is_verde(
        self,
    ):
        energy_distributor_serializer = (
            usage_contract_serializers.EnergyDistributorSerializer()
        )
        try:
            energy_distributor_serializer.validate(
                attrs={"tax_modality": [{}], "hourly_tax_modality": "Verde"}
            )
        except ValidationError as e:
            return
        self.fail("Validate function didn't validate unique msd or unique tax")

    def test_energy_distributor_serializer_validate_should_raise_validation_error_if_peak_and_off_musd_or_tax_doesnt_exist_and_isnt_verde(
        self,
    ):
        energy_distributor_serializer = (
            usage_contract_serializers.EnergyDistributorSerializer()
        )
        try:
            energy_distributor_serializer.validate(
                attrs={"tax_modality": [{}], "hourly_tax_modality": "Verde"}
            )
        except ValidationError as e:
            return
        self.fail("Validate function didn't validate unique msd or unique tax")

    def test_energy_distributor_serializer_validate_should_update_peak_and_off_peak_musd_and_tax_to_none_if_is_verde(
        self,
    ):
        energy_distributor_serializer = (
            usage_contract_serializers.EnergyDistributorSerializer()
        )

        response = energy_distributor_serializer.validate(
            attrs={
                "tax_modality": [
                    {
                        "unique_musd": 1,
                        "unique_tax": 2,
                        "peak_musd": "asdf",
                        "peak_tax": "asdf",
                        "off_peak_musd": "asdf",
                        "off_peak_tax": "asdf",
                    }
                ],
                "hourly_tax_modality": "Verde",
            }
        )

        self.assertDictEqual(
            response,
            {
                "tax_modality": [
                    {
                        "unique_musd": 1,
                        "unique_tax": 2,
                        "peak_musd": None,
                        "peak_tax": None,
                        "off_peak_musd": None,
                        "off_peak_tax": None,
                    }
                ],
                "hourly_tax_modality": "Verde",
            },
        )

    def test_energy_distributor_serializer_validate_should_update_unique_musd_and_peak_if_isnt_verde(
        self,
    ):
        energy_distributor_serializer = (
            usage_contract_serializers.EnergyDistributorSerializer()
        )

        response = energy_distributor_serializer.validate(
            attrs={
                "tax_modality": [
                    {
                        "unique_musd": 1,
                        "unique_tax": 2,
                        "peak_musd": "asdf",
                        "peak_tax": "asdf",
                        "off_peak_musd": "asdf",
                        "off_peak_tax": "asdf",
                    }
                ],
                "hourly_tax_modality": "Azul",
            }
        )

        self.assertDictEqual(
            response,
            {
                "tax_modality": [
                    {
                        "unique_musd": None,
                        "unique_tax": None,
                        "peak_musd": "asdf",
                        "peak_tax": "asdf",
                        "off_peak_musd": "asdf",
                        "off_peak_tax": "asdf",
                    }
                ],
                "hourly_tax_modality": "Azul",
            },
        )

    def test_rate_post_exception_should_raise_validation_error_if_begin_date_greater_than_end_date(
        self,
    ):
        rate_post_serializer = usage_contract_serializers.RatePostExceptionSerializer()

        try:
            rate_post_serializer.validate(
                attrs={
                    "begin_date": date.today(),
                    "end_date": date(day=1, month=1, year=1600),
                    "begin_hour_clock": 14,
                    "end_hour_clock": 13,
                }
            )
        except ValidationError:
            return
        self.fail(
            "Validate rate post exception should raise validation error if begin date > end date"
        )

    def test_rate_post_exception_should_raise_validation_error_if_begin_hour_greater_than_end_hour(
        self,
    ):
        rate_post_serializer = usage_contract_serializers.RatePostExceptionSerializer()

        try:
            rate_post_serializer.validate(
                attrs={
                    "begin_date": date.today(),
                    "end_date": date.today() + timedelta(days=1),
                    "begin_hour_clock": 14,
                    "end_hour_clock": 13,
                }
            )
        except ValidationError:
            return
        self.fail(
            "Validate rate post exception should raise validation error if begin hour > end hour"
        )

    def test_rate_post_exception_should_raise_key_error_error_if_begin_date_or_end_date_is_empty(
        self,
    ):
        rate_post_serializer = usage_contract_serializers.RatePostExceptionSerializer()

        try:
            rate_post_serializer.validate(
                attrs={"begin_hour_clock": 14, "end_hour_clock": 13}
            )
        except KeyError:
            return
        self.fail(
            "Validate rate post exception should raise validation error if begin hour > end hour"
        )

    def test_rate_post_exception_should_raise_key_error_error_if_begin_hour_or_end_hour_is_empty(
        self,
    ):
        rate_post_serializer = usage_contract_serializers.RatePostExceptionSerializer()

        try:
            rate_post_serializer.validate(
                attrs={
                    "begin_date": date.today(),
                    "end_date": date.today() + timedelta(days=1),
                }
            )
        except KeyError:
            return
        self.fail(
            "Validate rate post exception should raise validation error if begin hour > end hour"
        )

    def test_usage_contract_distributor_should_raise_validation_error_if_start_date_greater_than_end_date(
        self,
    ):
        usage_contract_distributor = (
            usage_contract_serializers.UsageContractDistributorSerializer()
        )

        try:
            usage_contract_distributor.validate(
                attrs={
                    "start_date": date.today(),
                    "end_date": date(day=1, month=1, year=1600),
                    "peak_begin_time": 13,
                    "peak_end_time": 14,
                }
            )
        except ValidationError:
            return
        self.fail(
            "Validate usage contract distributor should raise validation error if begin date > end date"
        )

    def test_usage_contract_distributor_should_raise_validation_error_if_begin_hour_greater_than_end_hour(
        self,
    ):
        usage_contract_distributor = (
            usage_contract_serializers.UsageContractDistributorSerializer()
        )

        try:
            usage_contract_distributor.validate(
                attrs={
                    "start_date": date.today(),
                    "end_date": date.today() + timedelta(days=1),
                    "peak_begin_time": 14,
                    "peak_end_time": 13,
                }
            )
        except ValidationError:
            return
        self.fail(
            "Validate usage contract distributor should raise validation error if peak begin time > peak end time"
        )

    def test_usage_contract_distributor_should_raise_key_error_error_if_start_date_or_end_date_is_empty(
        self,
    ):
        usage_contract_distributor = (
            usage_contract_serializers.UsageContractDistributorSerializer()
        )

        try:
            usage_contract_distributor.validate(
                attrs={"peak_begin_time": 14, "peak_end_time": 13}
            )
        except KeyError:
            return
        self.fail(
            "Validate usage contract distributor should raise validation error if begin hour > end hour"
        )

    def test_usage_contract_distributor_should_raise_key_error_error_if_begin_hour_or_end_hour_is_empty(
        self,
    ):
        usage_contract_distributor = (
            usage_contract_serializers.UsageContractDistributorSerializer()
        )

        try:
            usage_contract_distributor.validate(
                attrs={
                    "start_date": date.today(),
                    "end_date": date.today() + timedelta(days=1),
                }
            )
        except KeyError:
            return
        self.fail(
            "Validate usage contract distributor should raise validation error if begin hour > end hour"
        )

    def test_usage_contract_transmitter_should_raise_validation_error_if_start_date_greater_than_end_date(
        self,
    ):
        usage_contract_transmitter = (
            usage_contract_serializers.UsageContractTransmitterSerializer()
        )

        try:
            usage_contract_transmitter.validate(
                attrs={
                    "start_date": date.today(),
                    "end_date": date(day=1, month=1, year=1600),
                    "peak_begin_time": 13,
                    "peak_end_time": 14,
                }
            )
        except ValidationError:
            return
        self.fail(
            "Validate usage contract transmitter should raise validation error if begin date > end date"
        )

    def test_usage_contract_transmitter_should_raise_validation_error_if_begin_hour_greater_than_end_hour(
        self,
    ):
        usage_contract_transmitter = (
            usage_contract_serializers.UsageContractTransmitterSerializer()
        )

        try:
            usage_contract_transmitter.validate(
                attrs={
                    "start_date": date.today(),
                    "end_date": date.today() + timedelta(days=1),
                    "peak_begin_time": 14,
                    "peak_end_time": 13,
                }
            )
        except ValidationError:
            return
        self.fail(
            "Validate usage contract transmitter should raise validation error if peak begin time > peak end time"
        )

    def test_usage_contract_transmitter_should_raise_key_error_error_if_start_date_or_end_date_is_empty(
        self,
    ):
        usage_contract_transmitter = (
            usage_contract_serializers.UsageContractTransmitterSerializer()
        )

        try:
            usage_contract_transmitter.validate(
                attrs={"peak_begin_time": 14, "peak_end_time": 13}
            )
        except KeyError:
            return
        self.fail(
            "Validate usage contract transmitter should raise validation error if begin hour > end hour"
        )

    def test_usage_contract_transmitter_should_raise_key_error_error_if_begin_hour_or_end_hour_is_empty(
        self,
    ):
        usage_contract_transmitter = (
            usage_contract_serializers.UsageContractTransmitterSerializer()
        )

        try:
            usage_contract_transmitter.validate(
                attrs={
                    "start_date": date.today(),
                    "end_date": date.today() + timedelta(days=1),
                }
            )
        except KeyError:
            return
        self.fail(
            "Validate usage contract transmitter should raise validation error if begin hour > end hour"
        )

    @mock.patch("usage_contract.models.UploadFileUsageContract.objects.filter")
    @mock.patch("usage_contract.serializers.UploadFileUsageContractSerializer")
    def test_assign_uploaded_files_should_set_files_in_ctu_and_save_and_update_list_uf(
        self, upload_file_serializer_mock, upload_file_object_filter_mock
    ):
        usage_contract_distributor_serializer = (
            usage_contract_serializers.UsageContractDistributorSerializer()
        )

        upload_file_object_filter_mock.return_value = ["file1", "file2"]
        upload_file_serializer_mock.data = mock.Mock(return_value="log from serializer")

        context = {"upload_file_usage_contract_ids": "any"}
        ctu = mock.Mock()
        ctu.upload_file.set = mock.Mock()
        ctu.save = mock.Mock()
        _list_uf = []
        usage_contract_serializers.assign_uploaded_files(context, ctu, _list_uf)
        upload_file_object_filter_mock.assert_called_with(
            id_upload_file_usage_contract__in=context["upload_file_usage_contract_ids"]
        )
        self.assertTrue(upload_file_serializer_mock.called)
        self.assertTrue(ctu.upload_file.set)
        self.assertTrue(ctu.save.called)

    @mock.patch("usage_contract.models.TaxModality.id_usage_contract", mock.Mock())
    @mock.patch("usage_contract.models.TaxModality.save")
    def test_save_tax_modality_values_should_get_info_from_data_and_save_tax_modality_log_and_list_tax(
        self, tax_modality_save_mock
    ):
        usage_contract_distributor_serializer = (
            usage_contract_serializers.UsageContractDistributorSerializer()
        )

        energy_distributor_mock = mock.Mock()
        energy_distributor_mock.tax_modality.add = mock.Mock()

        _ctu_json = mock.Mock()
        _ctu_json.get_json_tax_modality = mock.Mock(return_value="get_json_return")
        _ctu_json.set_model_object = mock.Mock()

        _list_tax = []
        _log = mock.Mock()
        _log.save_log = mock.Mock()
        tax_modality_data = [
            {
                "begin_date": "begin_date",
                "end_date": "end_date",
                "unique_musd": "unique_musd",
                "unique_tax": "unique_tax",
                "peak_musd": "peak_musd",
                "peak_tax": "peak_tax",
                "off_peak_musd": "off_peak_musd",
                "off_peak_tax": "off_peak_tax",
            }
        ]

        usage_contract_distributor_serializer.save_tax_modality_values(
            tax_modality_data,
            energy_distributor_mock,
            date.today(),
            _ctu_json,
            _list_tax,
            _log,
        )
        self.assertTrue(tax_modality_save_mock.called)
        self.assertTrue(energy_distributor_mock.tax_modality.add.called)
        _ctu_json.set_model_object.assert_called_with("TAX_MODALITY", ANY)
        self.assertTrue(_ctu_json.get_json_tax_modality.called)
        self.assertTrue(len(_list_tax) == 1)
        self.assertTrue(_log.save_log.called)

    @mock.patch(
        "usage_contract.models.RatePostException.id_usage_contract",
        mock.Mock(return_value="id_usage_contract_mock"),
    )
    @mock.patch("usage_contract.models.RatePostException.save")
    def test_save_rate_post_exception_values_should_get_info_from_data_and_save_rate_post_log_and_list_rpe(
        self, rate_post_exception_save_mock
    ):

        ctu = mock.Mock()
        ctu.upload_file.set = mock.Mock()
        ctu.save = mock.Mock()

        _ctu_json = mock.Mock()
        _ctu_json.get_json_rate_post_exception = mock.Mock(
            return_value="get_json_return"
        )
        _ctu_json.set_model_object = mock.Mock()

        _list_rpe = []
        _log = mock.Mock()
        _log.save_log = mock.Mock()
        rate_post_exception_data = [
            {
                "begin_date": "begin_date",
                "end_date": "end_date",
                "begin_hour_clock": "unique_musd",
                "end_hour_clock": "unique_tax",
            }
        ]

        usage_contract_serializers.save_rate_post_exception_values(
            rate_post_exception_data, ctu, date.today(), _ctu_json, _list_rpe, _log
        )

        self.assertTrue(rate_post_exception_save_mock.called)
        _ctu_json.set_model_object.assert_called_with("RATE_POST_EXCEPTION", ANY)
        self.assertTrue(_ctu_json.get_json_rate_post_exception.called)
        self.assertTrue(len(_list_rpe) == 1)
        self.assertTrue(_log.save_log.called)

    @mock.patch(
        "usage_contract.models.RatePostException.id_usage_contract",
        mock.Mock(return_value="id_usage_contract_mock"),
    )
    def test_save_log_create_energy_distributor_should_get_info_from_data_and_save_energy_distributor_log_and_return_list_ed_and_et(
        self,
    ):
        usage_contract_distributor_serializer = (
            usage_contract_serializers.UsageContractDistributorSerializer()
        )
        energy_distributor = mock.Mock()
        ctu = mock.Mock()
        ctu.upload_file.set = mock.Mock()
        ctu.save = mock.Mock()

        _ctu_json = mock.Mock()
        _ctu_json.get_json_energy_distributor = mock.Mock(
            return_value="get_json_return"
        )
        _ctu_json.set_model_object = mock.Mock()

        _log = mock.Mock()
        _log.save_log = mock.Mock()
        (
            _json_et,
            _json_ed,
        ) = usage_contract_distributor_serializer.save_log_create_energy_distributor(
            energy_distributor, ctu, _ctu_json, _log, date.today()
        )

        _ctu_json.set_model_object.assert_called_with(
            "ENERGY_DISTRIBUTOR", energy_distributor
        )
        self.assertTrue(_ctu_json.get_json_energy_distributor.called)
        self.assertTrue(_json_et == "{}")
        self.assertTrue(_json_ed == "get_json_return")
        self.assertTrue(_log.save_log.called)

    def test_save_log_create_usage_contract_should_get_info_from_data_and_usage_contract_log(
        self,
    ):
        usage_contract_distributor_serializer = (
            usage_contract_serializers.UsageContractDistributorSerializer()
        )
        ctu = mock.Mock()
        ctu.company = "ctu_company"
        ctu.energy_dealer = "ctu_energy_dealer"
        ctu.rated_voltage = "ctu_rated_voltage"

        ctu.upload_file.set = mock.Mock()
        ctu.save = mock.Mock()

        _ctu_json = mock.Mock()
        _ctu_json.get_json_usage_contract = mock.Mock(return_value="get_json_return")
        _ctu_json.set_model_object = mock.Mock()

        _log = mock.Mock()
        _log.save_log = mock.Mock()

        _json_ed = ["_json_ed"]
        _json_et = ["_json_et"]
        _list_rpe = ["_list_rpe"]
        _list_tax = ["_list_tax"]
        _list_cc = ["_list_cc"]
        _list_cct = ["_list_cct"]
        _list_uf = ["_list_uf"]

        usage_contract_distributor_serializer.save_log_create_usage_contract(
            _ctu_json,
            ctu,
            _json_ed,
            _json_et,
            _list_rpe,
            _list_tax,
            _list_cc,
            _list_cct,
            _list_uf,
            _log,
            date.today(),
        )

        _ctu_json.set_model_object.assert_called_with("USAGE_CONTRACT", ctu)
        _ctu_json.get_json_usage_contract.assert_called_with(
            1,
            ctu.company,
            ctu.energy_dealer,
            ctu.rated_voltage,
            _json_ed,
            _json_et,
            _list_rpe,
            _list_tax,
            _list_cc,
            _list_cct,
            _list_uf,
        )
        self.assertTrue(_log.save_log.called)

    @mock.patch(
        "usage_contract.serializers.UsageContractDistributorSerializer.save_log_create_usage_contract"
    )
    @mock.patch(
        "usage_contract.serializers.UsageContractDistributorSerializer.save_log_create_energy_distributor",
        return_value=("json_et", "_json_ed"),
    )
    @mock.patch("usage_contract.serializers.save_rate_post_exception_values")
    @mock.patch(
        "usage_contract.serializers.UsageContractDistributorSerializer.save_tax_modality_values"
    )
    @mock.patch(
        "usage_contract.serializers.UsageContractDistributorSerializer.assign_usage_contract_and_save_energy_distributor"
    )
    @mock.patch("usage_contract.serializers.assign_uploaded_files")
    @mock.patch("usage_contract.uteis.log_utils.LogUtils.__init__", return_value=None)
    @mock.patch("usage_contract.uteis.ctu_json.CTUJson.__init__", return_value=None)
    @mock.patch("usage_contract.models.UsageContract.objects.create")
    def test_create_method_should_call_create_log_functions(
        self,
        usage_contract_create_mock,
        ctu_json_mock,
        log_utils_mock,
        assign_uploaded_files_mock,
        assign_usage_contract_and_save_energy_distributors_mock,
        save_tax_modality_values_mock,
        save_rate_post_exception_values_mock,
        save_log_create_energy_distributor_mock,
        save_log_create_usage_contract_mock,
    ):
        usage_contract_distributor_serializer = usage_contract_serializers.UsageContractDistributorSerializer(
            context={"username": "teste"}
        )

        validated_data = {
            "energy_distributor": {"tax_modality": "tax_modality_value"},
            "rate_post_exception": "rate_post_exception_value",
        }
        usage_contract_distributor_serializer.create(validated_data)
        usage_contract_create_mock.assert_called_with(**validated_data)
        self.assertTrue(ctu_json_mock.called)
        self.assertTrue(log_utils_mock.called)
        self.assertTrue(assign_uploaded_files_mock.called)
        self.assertTrue(assign_usage_contract_and_save_energy_distributors_mock.called)
        self.assertTrue(save_tax_modality_values_mock.called)
        self.assertTrue(save_rate_post_exception_values_mock.called)
        self.assertTrue(save_log_create_energy_distributor_mock.called)
        self.assertTrue(save_log_create_usage_contract_mock.called)

    @mock.patch("usage_contract.models.EnergyDistributor.objects.create")
    def test_assign_usage_contract_and_save_energy_distributor(
        self, energy_distributor_create_mock
    ):
        usage_contract_distributor_serializer = (
            usage_contract_serializers.UsageContractDistributorSerializer()
        )

        ctu = mock.Mock()
        ctu.save = mock.Mock()
        energy_distributor_create_mock.return_value = "The Energy Object"
        energy_distributor_data = {"id_usage_contract": "any"}
        energy_distributor = usage_contract_distributor_serializer.assign_usage_contract_and_save_energy_distributor(
            ctu, energy_distributor_data
        )
        self.assertTrue(energy_distributor_create_mock.called)
        self.assertTrue(energy_distributor == "The Energy Object")

    @mock.patch("usage_contract.models.EnergyTransmitter.objects.create")
    def test_assign_usage_contract_and_save_energy_transmitter(
        self, energy_transmitter_create_mock
    ):
        usage_contract_transmitter_serializer = (
            usage_contract_serializers.UsageContractTransmitterSerializer()
        )

        ctu = mock.Mock()

        ctu.save = mock.Mock()
        energy_transmitter_create_mock.return_value = "The Energy Object"
        energy_transmitter_data = {"id_usage_contract": "any"}
        energy_distributor = usage_contract_transmitter_serializer.assign_usage_contract_and_save_energy_transmitter(
            ctu, energy_transmitter_data
        )
        self.assertTrue(energy_transmitter_create_mock.called)
        self.assertTrue(energy_distributor == "The Energy Object")

    @mock.patch("usage_contract.models.Cct.id_usage_contract", mock.Mock())
    @mock.patch("usage_contract.models.Cct.save")
    def test_save_cct_energy_transmitter(self, cct_save_mock):
        usage_contract_transmitter_serializer = (
            usage_contract_serializers.UsageContractTransmitterSerializer()
        )

        energy_transmitter_mock = mock.Mock()
        energy_transmitter_mock.cct.add = mock.Mock()

        _ctu_json = mock.Mock()
        _ctu_json.get_json_cct = mock.Mock(return_value="get_json_return")
        _ctu_json.set_model_object = mock.Mock()

        _list_cct = []
        _log = mock.Mock()
        _log.save_log = mock.Mock()
        cct_data = [
            {
                "begin_date": "begin_date",
                "end_date": "end_date",
                "contract_value": "contract_value",
                "cct_number": "cct_number",
                "length": "length",
                "destination": "destination",
            }
        ]

        usage_contract_transmitter_serializer.save_cct(
            cct_data, energy_transmitter_mock, _ctu_json, _log, _list_cct, date.today()
        )
        self.assertTrue(cct_save_mock.called)
        self.assertTrue(energy_transmitter_mock.cct.add.called)
        _ctu_json.set_model_object.assert_called_with("CCT", ANY)
        self.assertTrue(_ctu_json.get_json_cct.called)
        self.assertTrue(len(_list_cct) == 1)
        self.assertTrue(_log.save_log.called)

    @mock.patch("usage_contract.models.ContractCycles.id_usage_contract", mock.Mock())
    @mock.patch("usage_contract.models.ContractCycles.save")
    def test_save_contract_cycles_energy_transmitter(self, contract_cycles_save_mock):
        usage_contract_transmitter_serializer = (
            usage_contract_serializers.UsageContractTransmitterSerializer()
        )

        energy_transmitter_mock = mock.Mock()
        energy_transmitter_mock.contract_cycles.add = mock.Mock()

        _ctu_json = mock.Mock()
        _ctu_json.get_json_cct = mock.Mock(return_value="get_json_return")
        _ctu_json.set_model_object = mock.Mock()

        _list_cc = []
        _log = mock.Mock()
        _log.save_log = mock.Mock()
        cc_data = [
            {
                "begin_date": "begin_date",
                "end_date": "end_date",
                "peak_must": "peak_must",
                "off_peak_must": "off_peak_must",
                "peak_tax": "peak_tax",
                "off_peak_tax": "off_peak_tax",
            }
        ]

        usage_contract_transmitter_serializer.save_contract_cycles(
            cc_data, energy_transmitter_mock, _ctu_json, _log, _list_cc, date.today()
        )
        self.assertTrue(contract_cycles_save_mock.called)
        self.assertTrue(energy_transmitter_mock.contract_cycles.add.called)
        _ctu_json.set_model_object.assert_called_with("CONTRACT_CYCLES", ANY)
        self.assertTrue(_ctu_json.get_json_contract_cycles.called)
        self.assertTrue(len(_list_cc) == 1)
        self.assertTrue(_log.save_log.called)

    @mock.patch("usage_contract.uteis.log_utils.LogUtils.__init__", return_value=None)
    @mock.patch(
        "usage_contract.uteis.log_utils.LogUtils.update_log", return_value=mock.Mock()
    )
    @mock.patch(
        "usage_contract.uteis.log_utils.LogUtils.save_log", return_value=mock.Mock()
    )
    @mock.patch(
        "usage_contract.models.UsageContract.objects.filter",
        return_value=usage_contract_queryset_mock,
    )
    @mock.patch(
        "usage_contract.models.EnergyDistributor.objects.update_or_create",
        return_value=QuerysetMock([mock.Mock()], [1, 2, 3]),
    )
    @mock.patch(
        "usage_contract.models.TaxModality.objects.filter",
        return_value=QuerysetMock(tax_list_mock, [1, 2, 3]),
    )
    @mock.patch(
        "usage_contract.models.RatePostException.objects.filter",
        return_value=QuerysetMock([mock.Mock()], [1, 2, 3]),
    )
    @mock.patch(
        "usage_contract.serializers.UsageContractDistributorSerializer.context",
        return_value=mock.Mock(),
    )
    @mock.patch(
        "usage_contract.uteis.ctu_json.CTUJson", return_value=mock.Mock(),
    )
    @mock.patch(
        "usage_contract.uteis.ctu_json.CTUJson.set_model_object",
        return_value=mock.Mock(),
    )
    @mock.patch(
        "usage_contract.uteis.ctu_json.CTUJson.get_json_tax_modality",
        return_value=mock.Mock(),
    )
    @mock.patch(
        "usage_contract.uteis.ctu_json.CTUJson.get_json_energy_distributor",
        return_value=mock.Mock(),
    )
    @mock.patch(
        "usage_contract.uteis.ctu_json.CTUJson.get_json_usage_contract",
        return_value=mock.Mock(),
    )
    @mock.patch(
        "usage_contract.serializers.UploadFileUsageContractSerializer",
        return_value=mock.Mock(),
    )
    def test_usage_contract_distributor_serializer_update_should_call_update(
        self,
        upload_file_usage_contract_serializer_mock,
        ctu_json_get_json_usage_contract_mock,
        ctu_json_get_json_energy_distributor_mock,
        ctu_json_get_json_tax_modality_mock,
        ctu_json_set_model_object_mock,
        ctu_json_mock,
        usage_contract_distributor_serializer_context_mock,
        rate_post_exception_objects_filter_mock,
        tax_modality_objects_filter_mock,
        energy_distributor_objects_update_or_create_mock,
        usage_contract_objects_filter_mock,
        log_utils_save_mock,
        log_utils_update_mock,
        log_utils_init_mock,
    ):
        usage_contract_distributor_serializer = (
            usage_contract_serializers.UsageContractDistributorSerializer()
        )

        validated_data = {
            "energy_distributor": {"tax_modality": tax_list_dict_mock},
            "rate_post_exception": [],
        }

        result = usage_contract_distributor_serializer.update(
            energy_distributor_mock, validated_data
        )

        self.assertTrue(log_utils_update_mock.called)
        self.assertEqual(type(result).__name__, "EnergyDistributor")

    @mock.patch("usage_contract.uteis.log_utils.LogUtils.__init__", return_value=None)
    @mock.patch(
        "usage_contract.uteis.log_utils.LogUtils.update_log", return_value=mock.Mock()
    )
    @mock.patch(
        "usage_contract.uteis.log_utils.LogUtils.save_log", return_value=mock.Mock()
    )
    @mock.patch(
        "usage_contract.models.UsageContract.rate_post_exception",
        return_value=mock.Mock(),
    )
    @mock.patch(
        "usage_contract.models.UsageContract.objects.filter",
        return_value=usage_contract_queryset_mock,
    )
    @mock.patch(
        "usage_contract.models.EnergyDistributor.objects.update_or_create",
        return_value=QuerysetMock([EnergyDistributor(1)], [1, 2, 3]),
    )
    @mock.patch(
        "usage_contract.models.EnergyDistributor.save",
        return_value=QuerysetMock([EnergyDistributor(1)], [1, 2, 3]),
    )
    @mock.patch(
        "usage_contract.models.EnergyDistributor.tax_modality",
        return_value=mock.Mock(),
    )
    @mock.patch(
        "usage_contract.models.TaxModality.objects.filter",
        return_value=QuerysetMock(tax_list_2_mock, [1]),
    )
    @mock.patch(
        "usage_contract.models.TaxModality.save", return_value=TaxModality(),
    )
    @mock.patch(
        "usage_contract.models.RatePostException.save", return_value=mock.Mock(),
    )
    @mock.patch(
        "usage_contract.models.RatePostException.objects.filter",
        return_value=QuerysetMock(rate_post_exception_list_mock, [1]),
    )
    @mock.patch(
        "usage_contract.serializers.UsageContractDistributorSerializer.context",
        return_value=mock.Mock(),
    )
    @mock.patch(
        "usage_contract.uteis.ctu_json.CTUJson", return_value=mock.Mock(),
    )
    @mock.patch(
        "usage_contract.uteis.ctu_json.CTUJson.set_model_object",
        return_value=mock.Mock(),
    )
    @mock.patch(
        "usage_contract.uteis.ctu_json.CTUJson.get_json_tax_modality",
        return_value=mock.Mock(),
    )
    @mock.patch(
        "usage_contract.uteis.ctu_json.CTUJson.get_json_energy_distributor",
        return_value=mock.Mock(),
    )
    @mock.patch(
        "usage_contract.uteis.ctu_json.CTUJson.get_json_usage_contract",
        return_value=mock.Mock(),
    )
    @mock.patch(
        "usage_contract.uteis.ctu_json.CTUJson.get_json_rate_post_exception",
        return_value=mock.Mock(),
    )
    @mock.patch(
        "usage_contract.serializers.UploadFileUsageContractSerializer",
        return_value=mock.Mock(),
    )
    def test_usage_contract_distributor_serializer_update_should_call_save(
        self,
        upload_file_usage_contract_serializer_mock,
        ctu_json_get_json_rate_post_exception_mock,
        ctu_json_get_json_usage_contract_mock,
        ctu_json_get_json_energy_distributor_mock,
        ctu_json_get_json_tax_modality_mock,
        ctu_json_set_model_object_mock,
        ctu_json_mock,
        usage_contract_distributor_serializer_context_mock,
        rate_post_exception_save_mock,
        rate_post_exception_objects_filter_mock,
        tax_modality_save_mock,
        tax_modality_objects_filter_mock,
        energy_distributor_tax_modality_mock,
        energy_distributor_save_mock,
        energy_distributor_objects_update_or_create_mock,
        usage_contract_rate_post_exception_mock,
        usage_contract_objects_filter_mock,
        log_utils_save_mock,
        log_utils_update_mock,
        log_utils_init_mock,
    ):
        usage_contract_distributor_serializer = (
            usage_contract_serializers.UsageContractDistributorSerializer()
        )

        validated_data = {
            "energy_distributor": {"tax_modality": tax_list_dict_2_mock},
            "rate_post_exception": rate_post_exception_list_dict_mock,
        }

        result = usage_contract_distributor_serializer.update(
            energy_distributor_mock, validated_data
        )

        self.assertTrue(rate_post_exception_save_mock.called)
        self.assertTrue(tax_modality_save_mock.called)
        self.assertTrue(log_utils_save_mock.called)
        self.assertTrue(log_utils_update_mock.called)
        self.assertTrue(log_utils_save_mock.called)
        self.assertEqual(type(result).__name__, "EnergyDistributor")

    @mock.patch(
        "usage_contract.serializers.UsageContractTransmitterSerializer.context",
        return_value=mock.Mock(),
    )
    @mock.patch(
        "usage_contract.serializers.UsageContractTransmitterSerializer.save_cct",
        return_value=mock.Mock(),
    )
    @mock.patch(
        "usage_contract.serializers.UsageContractTransmitterSerializer.save_contract_cycles",
        return_value=mock.Mock(),
    )
    @mock.patch(
        "usage_contract.serializers.UsageContractTransmitterSerializer.assign_usage_contract_and_save_energy_transmitter",
        return_value=mock.Mock(),
    )
    @mock.patch(
        "usage_contract.models.UsageContract.objects.create",
        return_value=usage_contract_mock,
    )
    @mock.patch(
        "usage_contract.uteis.ctu_json.CTUJson", return_value=mock.Mock(),
    )
    @mock.patch(
        "usage_contract.uteis.ctu_json.CTUJson.set_model_object",
        return_value=mock.Mock(),
    )
    @mock.patch(
        "usage_contract.uteis.ctu_json.CTUJson.get_json_energy_transmitter",
        return_value=mock.Mock(),
    )
    @mock.patch(
        "usage_contract.uteis.ctu_json.CTUJson.get_json_usage_contract",
        return_value=mock.Mock(),
    )
    @mock.patch(
        "usage_contract.uteis.ctu_json.CTUJson.get_table_model",
        return_value=mock.Mock(),
    )
    @mock.patch(
        "usage_contract.serializers.assign_uploaded_files", return_value=mock.Mock(),
    )
    @mock.patch(
        "usage_contract.serializers.save_rate_post_exception_values",
        return_value=mock.Mock(),
    )
    @mock.patch("usage_contract.uteis.log_utils.LogUtils.__init__", return_value=None)
    @mock.patch(
        "usage_contract.uteis.log_utils.LogUtils.update_log", return_value=mock.Mock()
    )
    @mock.patch(
        "usage_contract.uteis.log_utils.LogUtils.save_log", return_value=mock.Mock()
    )
    def test_usage_contract_transmitter_serializer_save_should_perform_save(
        self,
        log_utils_save_log_mock,
        log_utils_update_log_mock,
        log_utils_init_mock,
        save_rate_post_exception_values_mock,
        assign_uploaded_files_mock,
        get_table_model_mock,
        get_json_usage_contract_mock,
        get_json_energy_transmitter_mock,
        set_model_object_mock,
        ctu_json_mock,
        usage_contract_objects_create_mock,
        assign_usage_contract_and_save_energy_transmitter_mock,
        save_contract_cycles_mock,
        save_cct_mock,
        usage_contract_transmitter_serializer_context_mock,
    ):
        usage_contract_transmitter_serializer = (
            usage_contract_serializers.UsageContractTransmitterSerializer()
        )

        validated_data = {
            "energy_transmitter": {"cct": cct_list_mock, "contract_cycles": []},
            "rate_post_exception": rate_post_exception_list_dict_mock,
        }

        result = usage_contract_transmitter_serializer.create(validated_data)

        self.assertTrue(log_utils_save_log_mock.called)
        self.assertTrue(save_rate_post_exception_values_mock.called)
        self.assertTrue(assign_usage_contract_and_save_energy_transmitter_mock.called)
        self.assertTrue(save_contract_cycles_mock.called)
        self.assertTrue(save_cct_mock.called)
        self.assertEqual(type(result).__name__, "UsageContract")

    @mock.patch(
        "usage_contract.serializers.UsageContractTransmitterSerializer.context",
        return_value=mock.Mock(),
    )
    @mock.patch(
        "usage_contract.serializers.UsageContractTransmitterSerializer.save_cct",
        return_value=mock.Mock(),
    )
    @mock.patch(
        "usage_contract.serializers.UsageContractTransmitterSerializer.save_contract_cycles",
        return_value=mock.Mock(),
    )
    @mock.patch(
        "usage_contract.serializers.UsageContractTransmitterSerializer.assign_usage_contract_and_save_energy_transmitter",
        return_value=mock.Mock(),
    )
    @mock.patch(
        "usage_contract.models.UsageContract.objects.filter",
        return_value=QuerysetMock([usage_contract_mock]),
    )
    @mock.patch(
        "usage_contract.uteis.ctu_json.CTUJson", return_value=mock.Mock(),
    )
    @mock.patch(
        "usage_contract.uteis.ctu_json.CTUJson.set_model_object",
        return_value=mock.Mock(),
    )
    @mock.patch(
        "usage_contract.uteis.ctu_json.CTUJson.get_json_energy_transmitter",
        return_value=mock.Mock(),
    )
    @mock.patch(
        "usage_contract.uteis.ctu_json.CTUJson.get_json_usage_contract",
        return_value=mock.Mock(),
    )
    @mock.patch(
        "usage_contract.uteis.ctu_json.CTUJson.get_table_model",
        return_value=mock.Mock(),
    )
    @mock.patch(
        "usage_contract.uteis.ctu_json.CTUJson.get_json_cct", return_value=mock.Mock(),
    )
    @mock.patch(
        "usage_contract.uteis.ctu_json.CTUJson.get_json_rate_post_exception",
        return_value=mock.Mock(),
    )
    @mock.patch(
        "usage_contract.serializers.assign_uploaded_files", return_value=mock.Mock(),
    )
    @mock.patch(
        "usage_contract.serializers.save_rate_post_exception_values",
        return_value=mock.Mock(),
    )
    @mock.patch("usage_contract.uteis.log_utils.LogUtils.__init__", return_value=None)
    @mock.patch(
        "usage_contract.uteis.log_utils.LogUtils.update_log", return_value=mock.Mock()
    )
    @mock.patch(
        "usage_contract.uteis.log_utils.LogUtils.save_log", return_value=mock.Mock()
    )
    @mock.patch(
        "usage_contract.serializers.UploadFileUsageContractSerializer",
        return_value=mock.Mock(),
    )
    @mock.patch(
        "usage_contract.models.EnergyTransmitter.objects.update_or_create",
        return_value=QuerysetMock([mock.Mock()], [1, 2, 3]),
    )
    @mock.patch(
        "usage_contract.models.Cct.objects.filter",
        return_value=QuerysetMock(cct_list_mock, [1, 2, 3]),
    )
    @mock.patch(
        "usage_contract.models.ContractCycles.objects.filter",
        return_value=QuerysetMock(cc_list_mock, [1, 2, 3]),
    )
    @mock.patch(
        "usage_contract.models.ContractCycles.save",
        return_value=QuerysetMock(cc_list_mock, [1, 2, 3]),
    )
    @mock.patch(
        "usage_contract.models.RatePostException.objects.filter",
        return_value=QuerysetMock(
            QuerysetMock(rate_post_exception_list_mock), [1, 2, 3]
        ),
    )
    def test_usage_contract_transmitter_serializer_update_should_perform_update(
        self,
        rate_post_exception_objects_filter_mock,
        contract_cycles_save_mock,
        contract_cycles_objects_filter_mock,
        cct_objects_filter_mock,
        energy_transmitter_objects_update_or_create_mock,
        upload_file_usage_contract_serializer_mock,
        log_utils_save_log_mock,
        log_utils_update_log_mock,
        log_utils_init_mock,
        save_rate_post_exception_values_mock,
        assign_uploaded_files_mock,
        get_json_rate_post_exception_mock,
        get_json_cct_mock,
        get_table_model_mock,
        get_json_usage_contract_mock,
        get_json_energy_transmitter_mock,
        set_model_object_mock,
        ctu_json_mock,
        usage_contract_objects_filter_mock,
        assign_usage_contract_and_save_energy_transmitter_mock,
        save_contract_cycles_mock,
        save_cct_mock,
        usage_contract_transmitter_serializer_context_mock,
    ):
        usage_contract_transmitter_serializer = (
            usage_contract_serializers.UsageContractTransmitterSerializer()
        )

        validated_data = {
            "energy_transmitter": {"cct": cct_list_dict_mock, "contract_cycles": []},
            "rate_post_exception": rate_post_exception_list_dict_mock,
        }

        result = usage_contract_transmitter_serializer.update(
            EnergyTransmitter(), validated_data
        )

        self.assertTrue(energy_transmitter_objects_update_or_create_mock.called)
        self.assertTrue(log_utils_update_log_mock.called)

        self.assertEqual(type(result).__name__, "EnergyTransmitter")

    @mock.patch(
        "usage_contract.serializers.UsageContractTransmitterSerializer.context",
        return_value=mock.Mock(),
    )
    @mock.patch(
        "usage_contract.serializers.UsageContractTransmitterSerializer.save_cct",
        return_value=mock.Mock(),
    )
    @mock.patch(
        "usage_contract.serializers.UsageContractTransmitterSerializer.save_contract_cycles",
        return_value=mock.Mock(),
    )
    @mock.patch(
        "usage_contract.serializers.UsageContractTransmitterSerializer.assign_usage_contract_and_save_energy_transmitter",
        return_value=mock.Mock(),
    )
    @mock.patch(
        "usage_contract.models.UsageContract.objects.filter",
        return_value=QuerysetMock([usage_contract_mock]),
    )
    @mock.patch(
        "usage_contract.uteis.ctu_json.CTUJson", return_value=mock.Mock(),
    )
    @mock.patch(
        "usage_contract.uteis.ctu_json.CTUJson.set_model_object",
        return_value=mock.Mock(),
    )
    @mock.patch(
        "usage_contract.uteis.ctu_json.CTUJson.get_json_energy_transmitter",
        return_value=mock.Mock(),
    )
    @mock.patch(
        "usage_contract.uteis.ctu_json.CTUJson.get_json_usage_contract",
        return_value=mock.Mock(),
    )
    @mock.patch(
        "usage_contract.uteis.ctu_json.CTUJson.get_table_model",
        return_value=mock.Mock(),
    )
    @mock.patch(
        "usage_contract.uteis.ctu_json.CTUJson.get_json_cct", return_value=mock.Mock(),
    )
    @mock.patch(
        "usage_contract.uteis.ctu_json.CTUJson.get_json_rate_post_exception",
        return_value=mock.Mock(),
    )
    @mock.patch(
        "usage_contract.uteis.ctu_json.CTUJson.get_json_contract_cycles",
        return_value=mock.Mock(),
    )
    @mock.patch(
        "usage_contract.serializers.assign_uploaded_files", return_value=mock.Mock(),
    )
    @mock.patch(
        "usage_contract.serializers.save_rate_post_exception_values",
        return_value=mock.Mock(),
    )
    @mock.patch("usage_contract.uteis.log_utils.LogUtils.__init__", return_value=None)
    @mock.patch(
        "usage_contract.uteis.log_utils.LogUtils.update_log", return_value=mock.Mock()
    )
    @mock.patch(
        "usage_contract.uteis.log_utils.LogUtils.save_log", return_value=mock.Mock()
    )
    @mock.patch(
        "usage_contract.serializers.UploadFileUsageContractSerializer",
        return_value=mock.Mock(),
    )
    @mock.patch(
        "usage_contract.models.EnergyTransmitter.objects.update_or_create",
        return_value=QuerysetMock([EnergyTransmitter(1)], [1]),
    )
    @mock.patch(
        "usage_contract.models.Cct.objects.filter",
        return_value=QuerysetMock(cct_list_2_mock, [1]),
    )
    @mock.patch(
        "usage_contract.models.ContractCycles.objects.filter",
        return_value=QuerysetMock(cc_list_2_mock, [1]),
    )
    @mock.patch(
        "usage_contract.models.ContractCycles.save",
        return_value=QuerysetMock(cc_list_2_mock, [1]),
    )
    @mock.patch(
        "usage_contract.models.RatePostException.objects.filter",
        return_value=QuerysetMock(QuerysetMock(rate_post_exception_list_mock), [1]),
    )
    @mock.patch(
        "usage_contract.models.Cct.save",
        return_value=QuerysetMock(cct_list_2_mock, [1]),
    )
    @mock.patch(
        "usage_contract.models.EnergyTransmitter.cct", return_value=mock.Mock(),
    )
    @mock.patch(
        "usage_contract.models.EnergyTransmitter.contract_cycles",
        return_value=mock.Mock(),
    )
    @mock.patch(
        "usage_contract.models.RatePostException.save", return_value=mock.Mock(),
    )
    @mock.patch(
        "usage_contract.models.UsageContract.rate_post_exception",
        return_value=mock.Mock(),
    )
    def test_usage_contract_transmitter_serializer_update_should_perform_create(
        self,
        usage_contract_rate_post_exception_mock,
        rate_post_exception_save_mock,
        energy_transmitter_contract_cycles_mock,
        energy_transmitter_cct_mock,
        cct_save_mock,
        rate_post_exception_objects_filter_mock,
        contract_cycles_save_mock,
        contract_cycles_objects_filter_mock,
        cct_objects_filter_mock,
        energy_transmitter_objects_update_or_create_mock,
        upload_file_usage_contract_serializer_mock,
        log_utils_save_log_mock,
        log_utils_update_log_mock,
        log_utils_init_mock,
        save_rate_post_exception_values_mock,
        assign_uploaded_files_mock,
        get_json_contract_cycles_mock,
        get_json_rate_post_exception_mock,
        get_json_cct_mock,
        get_table_model_mock,
        get_json_usage_contract_mock,
        get_json_energy_transmitter_mock,
        set_model_object_mock,
        ctu_json_mock,
        usage_contract_objects_filter_mock,
        assign_usage_contract_and_save_energy_transmitter_mock,
        save_contract_cycles_mock,
        save_cct_mock,
        usage_contract_transmitter_serializer_context_mock,
    ):
        usage_contract_transmitter_serializer = (
            usage_contract_serializers.UsageContractTransmitterSerializer()
        )

        validated_data = {
            "energy_transmitter": {
                "cct": cct_list_dict_2_mock,
                "contract_cycles": cc_list_dict_2_mock,
            },
            "rate_post_exception": rate_post_exception_list_dict_2_mock,
        }

        result = usage_contract_transmitter_serializer.update(
            EnergyTransmitter(), validated_data
        )

        self.assertTrue(cct_save_mock.called)
        self.assertTrue(contract_cycles_save_mock.called)
        self.assertTrue(log_utils_save_log_mock.called)
        self.assertTrue(energy_transmitter_objects_update_or_create_mock.called)
        self.assertTrue(log_utils_update_log_mock.called)
        self.assertTrue(cct_save_mock.called)

        self.assertEqual(type(result).__name__, "EnergyTransmitter")

    @mock.patch(
        "usage_contract.models.UploadFileUsageContract.objects.create",
        return_value=mock.Mock(),
    )
    @mock.patch(
        "usage_contract.uteis.log_utils.LogUtils.__init__", return_value=None
    )
    @mock.patch(
        "usage_contract.uteis.log_utils.LogUtils.save_log", return_value=mock.Mock()
    )
    @mock.patch(
        "usage_contract.serializers.UploadFileUsageContractSerializer.context",
        return_value=mock.Mock(),
    )
    def test_upload_file_usage_contract_serializer_create_should_perform_create(
        self,
        upload_file_usage_contract_serializer_context_mock,
        log_utils_save_log_mock,
        log_utils_init_mock,
        upload_file_usage_contract_objects_create_mock,
    ):
        upload_file_usage_contract_serializer = (
            usage_contract_serializers.UploadFileUsageContractSerializer()
        )

        validated_data = {"file_path": MockFile(), "id_usage_contract": 1}

        result = upload_file_usage_contract_serializer.create(validated_data)

        self.assertTrue(upload_file_usage_contract_objects_create_mock.called)
        self.assertTrue(log_utils_save_log_mock.called)
