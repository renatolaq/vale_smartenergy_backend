from company.models import Company
from core.models import Log
from usage_contract.models import Cct, TaxModality, RatePostException, ContractCycles, UsageContract
from usage_contract.models import TypeUsageContract, RatedVoltage, EnergyTransmitter, EnergyDistributor


class CTUJson(object):

    __json = ''
    __user = ''

    def __init__(self, _id_ctu, _user='AnonymousUser'):

        self.__json = '{}'
        self._table_model = ''
        self._id_ctu = _id_ctu

        self._cct = Cct
        self._dealer = Company
        self._company = Company

        self._tax = TaxModality
        self._ctu = UsageContract
        self._cc = ContractCycles
        self._rated = RatedVoltage

        self._et = EnergyTransmitter
        self._ed = EnergyDistributor

        self._rate = RatePostException
        self._type = TypeUsageContract
        self._log = Log

    def get_table_model(self):
        return self._table_model

    def set_model_object(self, model, obj):

        self._table_model = model
        
        if model is "CCT":
            self._cct = obj
        if model is "TAX_MODALITY":
            self._tax = obj
        if model is "USAGE_CONTRACT":
            self._ctu = obj
        if model is "CONTRACT_CYCLES":
            self._cc = obj
        if model is "RATED_VOLTAGE":
            self._rated = obj
        if model is "ENERGY_TRANSMITTER":
            self._et = obj
        if model is "ENERGY_DISTRIBUTOR":
            self._ed = obj
        if model is "RATE_POST_EXCEPTION":
            self._rate = obj
        if model is "TYPE_USAGE_CONTRACT":
            self._type = obj
        if model is "COMPANY":
            self._company = obj
        if model is "DEALER":
            self._dealer = obj
        if model is "LOG":
            self._log = obj

    def get_json_cct(self):

        begin_date = self._cct.begin_date
        _begin_date = begin_date.strftime("%d/%m/%Y")

        if self._cct.end_date:
            end_date = self._cct.end_date
            _end_date = end_date.strftime("%d/%m/%Y")
        else:
            _end_date = None

        dic = {'id_cct': self._cct.id_cct,
               'id_usage_contract': self._id_ctu,
               'cct_number': self._cct.cct_number,
               'lenght': self._cct.length,
               'destination': self._cct.destination,
               'begin_date': _begin_date,
               'end_date': _end_date,
               'contract_value': self._cct.contract_value
               }
        return dic

    def get_json_tax_modality(self):

        begin_date = self._tax.begin_date
        _begin_date = begin_date.strftime("%d/%m/%Y")

        end_date = self._tax.end_date
        _end_date = end_date.strftime("%d/%m/%Y")

        dic = {'id_usage_contract': self._id_ctu,
               'id_tax_modality': self._tax.id_tax_modality,
               'begin_date': _begin_date,
               'end_date': _end_date,
               'peak_musd': self._tax.peak_musd,
               'peak_tax': self._tax.peak_tax,
               'off_peak_musd': self._tax.off_peak_musd,
               'off_peak_tax': self._tax.off_peak_tax,
               'unique_musd': self._tax.unique_musd,
               'unique_tax': self._tax.unique_tax
               }
        return dic

    def get_json_rate_post_exception(self):

        begin_date = self._rate.begin_date
        _begin_date = begin_date.strftime("%d/%m/%Y")

        end_date = self._rate.end_date
        _end_date = end_date.strftime("%d/%m/%Y")

        dic = {'id_usage_contract': self._id_ctu,
               'begin_date': _begin_date,
               'end_date': _end_date
               }

        if self._rate.begin_hour_clock:
            if self._rate.begin_hour_clock is not '':
                dic['begin_hour_clock'] = self._rate.begin_hour_clock.isoformat()

        if self._rate.end_hour_clock:
            if self._rate.end_hour_clock is not '':
                dic['end_hour_clock'] = self._rate.end_hour_clock.isoformat()

        return dic

    def get_json_contract_cycles(self):

        begin_date = self._cc.begin_date
        _begin_date = begin_date.strftime("%d/%m/%Y")

        end_date = self._cc.end_date
        _end_date = end_date.strftime("%d/%m/%Y")

        dic = {'id_usage_contract': self._id_ctu,
               'id_contract_cycles': self._cc.id_contract_cycles,
               'begin_date': _begin_date,
               'end_date': _end_date,
               'peak_must': self._cc.peak_must,
               'peak_tax': self._cc.peak_tax,
               'off_peak_must': self._cc.off_peak_must,
               'off_peak_tax': self._cc.off_peak_tax
               }

        return dic

    def get_json_type_usage_contract(self):
        dic = {'id_usage_contract_type': self._type.id_usage_contract_type, 'description': self._type.description}
        return dic

    def get_json_company(self, _company):
        self._company = _company
        dic = {'id_company': self._company.id_company, 'company_name': self._company.company_name}
        return dic

    def get_json_dealer(self, _dealer):
        self._dealer = _dealer
        dic = {'id_company': self._dealer.id_company, 'company_name': self._dealer.company_name}
        return dic

    def get_json_rated_voltage(self, _rated):
        self._rated = _rated
        dic = {'id_rated_voltage': self._rated.id_rated_voltage,
               'voltages': self._rated.voltages,
               'group': self._rated.group,
               'subgroup': self._rated.subgroup
               }
        return dic

    def get_json_energy_transmitter(self):
        dic = {'id_usage_contract': self._id_ctu,
               'ons_code': self._et.ons_code,
               'aneel_resolution': self._et.aneel_resolution,
               'renovation_period': self._et.renovation_period,
               'audit_renovation': self._et.audit_renovation,
               }

        if self._et.aneel_publication:
            dic['aneel_publication'] = self._et.aneel_publication.strftime("%d/%m/%Y")
        else:
            dic['aneel_publication'] = None

        return dic

    def get_json_energy_distributor(self):

        dic = {'id_usage_contract': self._id_ctu,
               'pn': self._ed.pn,
               'installation': self._ed.installation,
               'renovation_period': self._ed.renovation_period,
               'audit_renovation': self._ed.audit_renovation,
               'aneel_resolution': self._ed.aneel_resolution,
               'hourly_tax_modality': self._ed.hourly_tax_modality
               }

        if self._ed.aneel_publication:
            dic['aneel_publication'] = self._ed.aneel_publication.strftime("%d/%m/%Y")
        else:
            dic['aneel_publication'] = None
        return dic

    def get_json_usage_contract(self, _type, _company, _deader, _rated_voltage, _json_ed, _json_et, _list_rpe, _list_tax, _list_cc, _list_cct, _list_uf):

        start_date = self._ctu.start_date
        _start_date = start_date.strftime("%d/%m/%Y")

        end_date = self._ctu.end_date
        _end_date = end_date.strftime("%d/%m/%Y")

        dic = {'id_usage_contract': self._id_ctu,
               'connection_point': self._ctu.connection_point,
               'company': self.get_json_company(_company),
               'energy_dealer': self.get_json_dealer(_deader),
               'rated_voltage': self.get_json_rated_voltage(_rated_voltage),
               'energy_distributor': _json_ed,
               'energy_transmitter': _json_et,
               'bought_voltage': self._ctu.bought_voltage,
               'power_factor': self._ctu.power_factor,
               'tolerance_range': self._ctu.tolerance_range,
               'contract_value': self._ctu.contract_value,
               'observation': self._ctu.observation,
               'start_date': _start_date,
               'end_date': _end_date,
               'status': self._ctu.status,
               'contract_number': self._ctu.contract_number
               }

        if _type == 1:
            dic['use_contract_type'] = self.get_type_distributor()
        else:
            dic['use_contract_type'] = self.get_type_transmitter()

        if self._ctu.peak_begin_time:
            dic['peak_begin_time'] = self._ctu.peak_begin_time.isoformat()
        else:
            dic['peak_begin_time'] = None

        if self._ctu.peak_end_time:
            dic['peak_end_time'] = self._ctu.peak_end_time.isoformat()
        else:
            dic['peak_end_time'] = None

        if len(_list_rpe) > 0:
            dic['rate_post_exception'] = _list_rpe

        if len(_list_tax) > 0:
            dic['tax_modality'] = _list_tax

        if len(_list_cc) > 0:
            dic['contract_cycles'] = _list_cc

        if len(_list_cct) > 0:
            dic['cct'] = _list_cct
        
        if len(_list_uf) > 0:
            dic['upload_file'] = _list_uf

        return dic

    @staticmethod
    def get_type_distributor():
        dic = {'id_usage_contract_type': 1, 'description': u"Distribuição"}
        return dic

    @staticmethod
    def get_type_transmitter():
        dic = {'id_usage_contract_type': 2, 'description': u"Transmissão"}
        return dic

    def get_dic_log(self):

        dic = {'id_log': str(self._log.id_log),
               'field_pk': self._log.field_pk,
               'table_name': self._log.table_name,
               'action_type': self._log.action_type,
               'old_value': str(self._log.old_value),
               'new_value': str(self._log.new_value),
               'date': self._log.date.strftime("%d/%m/%Y %H:%M:%S"),
               'user': self._log.user
               }

        if self._log.observation is None:
            dic['observation'] = ''
        else:
            dic['observation'] = self._log.observation

        return dic
