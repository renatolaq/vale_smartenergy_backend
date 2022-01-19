from unittest import mock
from django.test import SimpleTestCase
from usage_contract.models import (
    Cct,
    TaxModality,
    RatePostException,
    ContractCycles,
    UsageContract,
)
from usage_contract.models import (
    TypeUsageContract,
    RatedVoltage,
    EnergyTransmitter,
    EnergyDistributor,
)
from company.models import Company
from core.models import Log


from usage_contract.uteis import ctu_json
from datetime import datetime, date


class TestUsageContractUteis(SimpleTestCase):
    # @mock.patch(
    #     "usage_contract.models.UsageContract.objects.filter", return_value=mock.Mock(),
    # )
    def test_ctu_json_constructor(self):
        id = 1
        json_attribute = "{}"
        ctu_json_object = ctu_json.CTUJson(id)
        self.assertEqual(ctu_json_object._id_ctu, id)
        self.assertEqual(ctu_json_object._CTUJson__json, json_attribute)

    def test_get_table_model(self):
        id = 1
        ctu_json_object = ctu_json.CTUJson(id)
        table_model = ctu_json_object.get_table_model()
        self.assertEqual(table_model, "")

        cct_object = Cct()
        ctu_json_object.set_model_object("CCT", cct_object)
        table_model = ctu_json_object.get_table_model()
        self.assertEqual(table_model, "CCT")
        self.assertIs(ctu_json_object._cct, cct_object)

    def test_set_model_object(self):
        id = 1
        ctu_json_object = ctu_json.CTUJson(id)
        obj = object()
        model_dict = {
            "CCT": "_cct",
            "TAX_MODALITY": "_tax",
            "USAGE_CONTRACT": "_ctu",
            "CONTRACT_CYCLES": "_cc",
            "RATED_VOLTAGE": "_rated",
            "ENERGY_TRANSMITTER": "_et",
            "ENERGY_DISTRIBUTOR": "_ed",
            "RATE_POST_EXCEPTION": "_rate",
            "TYPE_USAGE_CONTRACT": "_type",
            "COMPANY": "_company",
            "DEALER": "_dealer",
            "LOG": "_log",
        }

        for key, value in model_dict.items():
            ctu_json_object.set_model_object(key, obj)
            self.assertIs(getattr(ctu_json_object, value), obj)

    def test_get_json_cct(self):
        id = 2
        ctu_json_object = ctu_json.CTUJson(id)
        date_string = "21 June, 2018"
        date_object = datetime.strptime(date_string, "%d %B, %Y")

        dic = {
            "id_cct": 1,
            "id_usage_contract": EnergyTransmitter(id),
            "cct_number": 3,
            "length": 4,
            "destination": "test",
            "begin_date": date_object,
            "end_date": date_object,
            "contract_value": 10,
        }
        cct_object = Cct(**dic)
        ctu_json_object.set_model_object("CCT", cct_object)
        json_cct_dict = ctu_json_object.get_json_cct()

        self.assertEqual(json_cct_dict["id_cct"], 1)
        self.assertEqual(json_cct_dict["id_usage_contract"], id)
        self.assertEqual(json_cct_dict["cct_number"], 3)
        self.assertEqual(json_cct_dict["lenght"], 4)
        self.assertEqual(json_cct_dict["destination"], "test")
        self.assertEqual(json_cct_dict["begin_date"], date_object.strftime("%d/%m/%Y"))
        self.assertEqual(json_cct_dict["end_date"], date_object.strftime("%d/%m/%Y"))
        self.assertEqual(json_cct_dict["contract_value"], 10)

        dic.pop("end_date")

        cct_object = Cct(**dic)
        ctu_json_object.set_model_object("CCT", cct_object)
        json_cct_dict = ctu_json_object.get_json_cct()

        self.assertEqual(json_cct_dict["id_cct"], 1)
        self.assertEqual(json_cct_dict["id_usage_contract"], id)
        self.assertEqual(json_cct_dict["cct_number"], 3)
        self.assertEqual(json_cct_dict["lenght"], 4)
        self.assertEqual(json_cct_dict["destination"], "test")
        self.assertEqual(json_cct_dict["begin_date"], date_object.strftime("%d/%m/%Y"))
        self.assertEqual(json_cct_dict["end_date"], None)
        self.assertEqual(json_cct_dict["contract_value"], 10)

    def test_get_json_tax_modality(self):
        id = 2
        ctu_json_object = ctu_json.CTUJson(id)
        date_string = "21 June, 2018"
        date_object = datetime.strptime(date_string, "%d %B, %Y")

        dic = {
            "id_usage_contract": EnergyDistributor(1),
            "id_tax_modality": 1,
            "begin_date": date_object,
            "end_date": date_object,
            "peak_musd": 2,
            "peak_tax": 2,
            "off_peak_musd": 2,
            "off_peak_tax": 2,
            "unique_musd": 2,
            "unique_tax": 2,
        }

        tax_object = TaxModality(**dic)
        ctu_json_object.set_model_object("TAX_MODALITY", tax_object)
        json_tax_dict = ctu_json_object.get_json_tax_modality()

        for key in json_tax_dict:
            if key == "id_usage_contract":
                self.assertEqual(json_tax_dict[key], id)
            else:
                self.assertEqual(
                    json_tax_dict[key],
                    dic[key].strftime("%d/%m/%Y")
                    if isinstance(dic[key], date)
                    else dic[key],
                )

    def test_get_json_rate_post_exception(self):
        id = 2
        ctu_json_object = ctu_json.CTUJson(id)
        date_string = "21 June, 2018"
        date_object = datetime.strptime(date_string, "%d %B, %Y")

        dic = {
            "id_usage_contract": UsageContract(1),
            "begin_date": date_object,
            "end_date": date_object,
            "begin_hour_clock": date_object,
            "end_hour_clock": date_object,
        }

        rate_object = RatePostException(**dic)
        ctu_json_object.set_model_object("RATE_POST_EXCEPTION", rate_object)
        json_tax_dict = ctu_json_object.get_json_rate_post_exception()

        self.assertEqual(json_tax_dict["id_usage_contract"], id)
        self.assertEqual(json_tax_dict["begin_date"], date_object.strftime("%d/%m/%Y"))
        self.assertEqual(json_tax_dict["end_date"], date_object.strftime("%d/%m/%Y"))
        self.assertEqual(json_tax_dict["begin_hour_clock"], date_object.isoformat())
        self.assertEqual(json_tax_dict["end_hour_clock"], date_object.isoformat())

    def test_get_json_contract_cycles(self):
        id = 2
        ctu_json_object = ctu_json.CTUJson(id)
        date_string = "21 June, 2018"
        date_object = datetime.strptime(date_string, "%d %B, %Y")

        dic = {
            "id_usage_contract": EnergyTransmitter(1),
            "id_contract_cycles": 1,
            "begin_date": date_object,
            "end_date": date_object,
            "peak_must": 1,
            "peak_tax": 1,
            "off_peak_must": 1,
            "off_peak_tax": 1,
        }

        cc_object = ContractCycles(**dic)
        ctu_json_object.set_model_object("CONTRACT_CYCLES", cc_object)
        json_cc_dict = ctu_json_object.get_json_contract_cycles()

        self.assertEqual(json_cc_dict["id_usage_contract"], id)
        self.assertEqual(json_cc_dict["id_contract_cycles"], 1)
        self.assertEqual(json_cc_dict["begin_date"], date_object.strftime("%d/%m/%Y"))
        self.assertEqual(json_cc_dict["end_date"], date_object.strftime("%d/%m/%Y"))
        self.assertEqual(json_cc_dict["peak_must"], 1)
        self.assertEqual(json_cc_dict["peak_tax"], 1)
        self.assertEqual(json_cc_dict["off_peak_must"], 1)
        self.assertEqual(json_cc_dict["off_peak_tax"], 1)

    def test_get_json_type_usage_contract(self):
        id = 2
        ctu_json_object = ctu_json.CTUJson(id)

        dic = {"id_usage_contract_type": 1, "description": "test"}

        type_uc_object = TypeUsageContract(**dic)
        ctu_json_object.set_model_object("TYPE_USAGE_CONTRACT", type_uc_object)
        json_type_uc_dict = ctu_json_object.get_json_type_usage_contract()

        self.assertEqual(json_type_uc_dict["id_usage_contract_type"], 1)
        self.assertEqual(json_type_uc_dict["description"], "test")

    def test_get_json_company(self):
        id = 2
        ctu_json_object = ctu_json.CTUJson(id)

        dic = {"id_company": 1, "company_name": "test"}

        company_object = Company(**dic)
        json_company_dict = ctu_json_object.get_json_company(company_object)

        self.assertEqual(json_company_dict["id_company"], 1)
        self.assertEqual(json_company_dict["company_name"], "test")

    def test_get_json_dealer(self):
        id = 2
        ctu_json_object = ctu_json.CTUJson(id)

        dic = {"id_company": 1, "company_name": "test"}

        company_object = Company(**dic)
        json_company_dict = ctu_json_object.get_json_dealer(company_object)

        self.assertEqual(json_company_dict["id_company"], 1)
        self.assertEqual(json_company_dict["company_name"], "test")

    def test_get_json_rated_voltage(self):
        id = 2
        ctu_json_object = ctu_json.CTUJson(id)

        dic = {
            "id_rated_voltage": 1,
            "voltages": 1,
            "group": "group",
            "subgroup": "subgroup",
        }

        rv_object = RatedVoltage(**dic)
        json_rv_dict = ctu_json_object.get_json_rated_voltage(rv_object)

        for key in dic:
            self.assertEqual(json_rv_dict[key], dic[key])

    def test_get_json_energy_transmitter(self):
        id = 2
        ctu_json_object = ctu_json.CTUJson(id)
        date_string = "21 June, 2018"
        date_object = datetime.strptime(date_string, "%d %B, %Y")

        dic = {
            "id_usage_contract": UsageContract(1),
            "ons_code": "ons",
            "aneel_resolution": "resolution",
            "renovation_period": 10,
            "audit_renovation": "audit",
            "aneel_publication": date_object,
        }

        et_object = EnergyTransmitter(**dic)
        ctu_json_object.set_model_object("ENERGY_TRANSMITTER", et_object)
        json_et_dict = ctu_json_object.get_json_energy_transmitter()

        self.assertEqual(json_et_dict["id_usage_contract"], id)
        self.assertEqual(json_et_dict["ons_code"], "ons")
        self.assertEqual(json_et_dict["aneel_resolution"], "resolution")
        self.assertEqual(json_et_dict["renovation_period"], 10)
        self.assertEqual(json_et_dict["audit_renovation"], "audit")
        self.assertEqual(
            json_et_dict["aneel_publication"], date_object.strftime("%d/%m/%Y")
        )

        dic.pop("aneel_publication")

        et_object = EnergyTransmitter(**dic)
        ctu_json_object.set_model_object("ENERGY_TRANSMITTER", et_object)
        json_et_dict = ctu_json_object.get_json_energy_transmitter()

        self.assertEqual(json_et_dict["aneel_publication"], None)

    def test_get_json_energy_distributor(self):
        id = 2
        ctu_json_object = ctu_json.CTUJson(id)
        date_string = "21 June, 2018"
        date_object = datetime.strptime(date_string, "%d %B, %Y")

        dic = {
            "id_usage_contract": UsageContract(1),
            "pn": 1,
            "installation": "inst",
            "hourly_tax_modality": "modality",
            "aneel_resolution": "resolution",
            "renovation_period": 10,
            "audit_renovation": "audit",
            "aneel_publication": date_object,
        }

        ed_object = EnergyDistributor(**dic)
        ctu_json_object.set_model_object("ENERGY_DISTRIBUTOR", ed_object)
        json_ed_dict = ctu_json_object.get_json_energy_distributor()

        self.assertEqual(json_ed_dict["id_usage_contract"], id)
        self.assertEqual(json_ed_dict["pn"], 1)
        self.assertEqual(json_ed_dict["installation"], "inst")
        self.assertEqual(json_ed_dict["aneel_resolution"], "resolution")
        self.assertEqual(json_ed_dict["hourly_tax_modality"], "modality")
        self.assertEqual(json_ed_dict["renovation_period"], 10)
        self.assertEqual(json_ed_dict["audit_renovation"], "audit")
        self.assertEqual(
            json_ed_dict["aneel_publication"], date_object.strftime("%d/%m/%Y")
        )

        dic.pop("aneel_publication")

        ed_object = EnergyDistributor(**dic)
        ctu_json_object.set_model_object("ENERGY_DISTRIBUTOR", ed_object)
        json_ed_dict = ctu_json_object.get_json_energy_distributor()

        self.assertEqual(json_ed_dict["aneel_publication"], None)

    def test_get_type_distributor(self):

        dic = ctu_json.CTUJson.get_type_distributor()

        self.assertEqual(dic["id_usage_contract_type"], 1)
        self.assertEqual(dic["description"], u"Distribuição")

    def test_get_type_transmitterr(self):

        dic = ctu_json.CTUJson.get_type_transmitter()

        self.assertEqual(dic["id_usage_contract_type"], 2)
        self.assertEqual(dic["description"], u"Transmissão")

    def test_get_dic_log(self):
        id = 2
        ctu_json_object = ctu_json.CTUJson(id)
        date_string = "21 June, 2018"
        date_object = datetime.strptime(date_string, "%d %B, %Y")

        dic = {
            "id_log": 1,
            "field_pk": 2,
            "table_name": "table",
            "action_type": "action",
            "old_value": "old",
            "new_value": "new",
            "date": date_object,
            "user": "user",
            "observation": "obs",
        }

        log_object = Log(**dic)
        ctu_json_object.set_model_object("LOG", log_object)
        json_log_dict = ctu_json_object.get_dic_log()

        self.assertEqual(json_log_dict["id_log"], str(1))
        self.assertEqual(json_log_dict["field_pk"], 2)
        self.assertEqual(json_log_dict["table_name"], "table")
        self.assertEqual(json_log_dict["action_type"], "action")
        self.assertEqual(json_log_dict["old_value"], "old")
        self.assertEqual(json_log_dict["new_value"], "new")
        self.assertEqual(
            json_log_dict["date"], date_object.strftime("%d/%m/%Y %H:%M:%S")
        )
        self.assertEqual(json_log_dict["user"], "user")
        self.assertEqual(json_log_dict["observation"], "obs")

        dic["observation"] = None

        log_object = Log(**dic)
        ctu_json_object.set_model_object("LOG", log_object)
        json_log_dict = ctu_json_object.get_dic_log()

        self.assertEqual(json_log_dict["observation"], "")

    def test_get_json_usage_contract(self):

        id = 2
        ctu_json_object = ctu_json.CTUJson(id)
        date_string = "21 June, 2018"
        date_object = datetime.strptime(date_string, "%d %B, %Y")

        dic_rv = {
            "id_rated_voltage": 1,
            "voltages": 1,
            "group": "group",
            "subgroup": "subgroup",
        }

        dic_company = {"id_company": 1, "company_name": "test"}

        dic_usage_contract = {
            "id_usage_contract": 1,
            "connection_point": "connection",
            "bought_voltage": 10,
            "power_factor": 10,
            "tolerance_range": 10,
            "contract_value": 10,
            "observation": "obs",
            "start_date": date_object,
            "end_date": date_object,
            "status": "S",
            "contract_number": "123",
            "peak_begin_time": date_object,
            "peak_end_time": date_object
        }

        company_object = Company(**dic_company)
        dealer_object = Company(**dic_company)
        rv_object = RatedVoltage(**dic_rv)
        usage_contract_object = UsageContract(**dic_usage_contract)

        ctu_json_object.set_model_object("USAGE_CONTRACT", usage_contract_object)
        json_ctu_dict = ctu_json_object.get_json_usage_contract(
            1,
            company_object,
            dealer_object,
            rv_object,
            "json_ed",
            "json_et",
            ["mock"],
            ["mock"],
            ["mock"],
            ["mock"],
            ["mock"],
        )

        self.assertEqual(json_ctu_dict["id_usage_contract"], id)
        self.assertEqual(json_ctu_dict["connection_point"], "connection")
        self.assertEqual(json_ctu_dict["bought_voltage"], 10)
        self.assertEqual(json_ctu_dict["power_factor"], 10)
        self.assertEqual(json_ctu_dict["tolerance_range"], 10)
        self.assertEqual(json_ctu_dict["contract_value"], 10)
        self.assertEqual(json_ctu_dict["observation"], "obs")
        self.assertEqual(json_ctu_dict["start_date"], date_object.strftime("%d/%m/%Y"))
        self.assertEqual(json_ctu_dict["end_date"], date_object.strftime("%d/%m/%Y"))
        self.assertEqual(json_ctu_dict["status"], "S")
        self.assertEqual(json_ctu_dict["contract_number"], "123")
        self.assertEqual(json_ctu_dict["peak_begin_time"], date_object.isoformat())
        self.assertEqual(json_ctu_dict["peak_end_time"], date_object.isoformat())
        self.assertEqual(json_ctu_dict['company'], ctu_json_object.get_json_company(company_object))
        self.assertEqual(json_ctu_dict['energy_dealer'], ctu_json_object.get_json_dealer(dealer_object))
        self.assertEqual(json_ctu_dict['rated_voltage'], ctu_json_object.get_json_rated_voltage(rv_object))
        self.assertEqual(json_ctu_dict["energy_distributor"], 'json_ed')
        self.assertEqual(json_ctu_dict["energy_transmitter"], 'json_et')
        self.assertEqual(json_ctu_dict["rate_post_exception"], ["mock"])
        self.assertEqual(json_ctu_dict["tax_modality"], ["mock"])
        self.assertEqual(json_ctu_dict["contract_cycles"], ["mock"])
        self.assertEqual(json_ctu_dict["cct"], ["mock"])
        self.assertEqual(json_ctu_dict["upload_file"], ["mock"])
        self.assertEqual(json_ctu_dict["use_contract_type"], ctu_json.CTUJson.get_type_distributor())

        dic_usage_contract.pop('peak_begin_time')
        dic_usage_contract.pop('peak_end_time')
        usage_contract_object = UsageContract(**dic_usage_contract)
        ctu_json_object.set_model_object("USAGE_CONTRACT", usage_contract_object)
        json_ctu_dict = ctu_json_object.get_json_usage_contract(
            2,
            company_object,
            dealer_object,
            rv_object,
            "json_ed",
            "json_et",
            ["mock"],
            ["mock"],
            ["mock"],
            ["mock"],
            ["mock"],
        )

        self.assertEqual(json_ctu_dict["use_contract_type"], ctu_json.CTUJson.get_type_transmitter())




