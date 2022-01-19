from typing import List, Callable
from calendar import month_name, different_locale, datetime, monthrange
from core.views import get_peek_time_logic
import json
import requests


from usage_contract.models import UsageContract, TaxModality, ContractCycles
from gauge_point.models import GaugeData
from asset_items.models import AssetItems
from SmartEnergy.auth import get_user_companies
from company.models import Company

class IntegrationService:

    def get_hour_month(self, year: int):
        english_month_names = []
        with different_locale('C.UTF-8'):
            english_month_names = list(map(lambda s: s.lower(), month_name))

        peak = {}
        offpeak = {}

        for month in range(1, 13):
            peek_time_data = get_peek_time_logic(year, month, 'BR')

            peak[english_month_names[month]] = peek_time_data['peek_time']
            offpeak[english_month_names[month]
                    ] = peek_time_data['off_peek_time']

        return peak, offpeak

    def __get_parent_company_id(self, company):
        asset_item: AssetItems = AssetItems.objects.select_related(
            "id_assets").filter(id_company=company).first()
        if asset_item:
            return asset_item.id_assets.id_company.id_company
        return None

    def __get_usage_contracts(self, company: int, year: int, factor: float, return_peak: bool):
        tax_modalities = []
        contract_cycles = []
        if self.can_split_contract(company):
            company = self.__get_parent_company_id(company) or company
            factor = factor if factor <= 1 else 1
            factor = factor if factor >= 0 else 0
        else:
            factor = 1

        tax_modalities = list(TaxModality.objects.filter(
            id_usage_contract__id_usage_contract__company=company, begin_date__year__lte=year, end_date__year__gte=year).order_by('begin_date'))
        contract_cycles = list(ContractCycles.objects.filter(
            id_usage_contract_id__id_usage_contract__company=company, begin_date__year__lte=year, end_date__year__gte=year).order_by('begin_date'))

        if len(tax_modalities) == 0 or (tax_modalities[0].begin_date.year == year and tax_modalities[0].begin_date.month > 1):
            tax_modalities = list(TaxModality.objects.filter(
                id_usage_contract__id_usage_contract__company=company, end_date__year__lt=year).order_by('-end_date')[:1]) + tax_modalities

        if len(contract_cycles) == 0 or (contract_cycles[0].begin_date.year == year and contract_cycles[0].begin_date.month > 1):
            contract_cycles = list(ContractCycles.objects.filter(
                id_usage_contract_id__id_usage_contract__company=company, end_date__year__lt=year).order_by('-end_date')[:1]) + contract_cycles

        tax_modalities: List[TaxModality] = list(tax_modalities)
        contract_cycles: List[ContractCycles] = list(contract_cycles)

        ret = {}

        english_month_names = []
        with different_locale('C.UTF-8'):
            english_month_names = list(map(lambda s: s.lower(), month_name))

        for month in range(1, 13):
            ret[english_month_names[month]] = None
            tax_modality: TaxModality = None
            contract_cicle: ContractCycles = None

            if len(tax_modalities) == 1 and len(contract_cycles) == 0:
                tax_modality = tax_modalities[0]
            elif len(tax_modalities) == 0 and len(contract_cycles) == 1:
                contract_cicle = contract_cycles[0]
            else:
                month_last_day = monthrange(year, month)[1]
                for tm in tax_modalities:
                    if tm.end_date >= datetime.date(year, month, month_last_day) and tm.begin_date <= datetime.date(year, month, 1):
                        tax_modality = tm
                        break
                for cc in contract_cycles:
                    if cc.end_date >= datetime.date(year, month, month_last_day) and cc.begin_date <= datetime.date(year, month, 1):
                        contract_cicle = cc
                        break
            if not tax_modality and not contract_cicle and (len(tax_modalities) > 0 or len(contract_cycles) > 0):
                for tm in reversed(tax_modalities):
                    if tm.end_date.replace(day=1) < datetime.date(year, month, 1):
                        tax_modality = tm
                        break
                for cc in reversed(contract_cycles):
                    if cc.end_date.replace(day=1) < datetime.date(year, month, 1):
                        contract_cicle = cc
                        break

                if tax_modality and contract_cicle:
                    if tax_modality.end_date > contract_cicle.end_date:
                        contract_cicle = None
                    else:
                        tax_modality = None

            if contract_cicle:
                ret[english_month_names[month]] = float(
                    contract_cicle.peak_must if return_peak else contract_cicle.off_peak_must) * factor
            elif tax_modality:
                if(tax_modality.id_usage_contract.hourly_tax_modality == "Azul"):
                    ret[english_month_names[month]] = float(
                        tax_modality.peak_musd if return_peak else tax_modality.off_peak_musd) * factor
                else:
                    ret[english_month_names[month]] = float(
                        tax_modality.unique_musd) * factor

        return ret

    def get_contracted_peak_power_demand(self, company: int, year: int, factor: float):
        return self.__get_usage_contracts(company, year, factor, True)

    def get_contracted_offpeak_power_demand(self, company: int, year: int, factor: float):
        return self.__get_usage_contracts(company, year, factor, False)

    def get_production(self, company: int, year: int):
        month_production = {}

        english_month_names = []
        with different_locale('C.UTF-8'):
            english_month_names = list(map(lambda s: s.lower(), month_name))

        data: List[GaugeData] = GaugeData.objects.filter(
            id_measurements=15, id_gauge__id_company=company, utc_gauge__year=year)

        for month in range(1, 13):
            month_data = list(
                filter(lambda g: g.utc_gauge.month == month, data))
            if len(month_data):
                month_production[english_month_names[month]] = float(sum(
                    map(lambda g: g.value, month_data)))
            else:
                month_production[english_month_names[month]] = None

        return month_production

    def can_split_contract(self, company: int) -> bool:
        parent_company_id = self.__get_parent_company_id(company)
        return (parent_company_id is not None and parent_company_id != company)

    def has_registered_contract(self, company: int, year: int) -> bool:
        def find_query_in_effect(id):
            return (TaxModality.objects.filter(id_usage_contract__id_usage_contract__company=id, begin_date__year__lte=year, end_date__year__gte=year).count() > 0 or
                    ContractCycles.objects.filter(
                    id_usage_contract_id__id_usage_contract__company=id, begin_date__year__lte=year, end_date__year__gte=year).count() > 0)

        def find_query_out_of_effect(id):
            return (TaxModality.objects.filter(id_usage_contract__id_usage_contract__company=id, begin_date__year__lte=year, end_date__year__lte=year).count() > 0 or
                    ContractCycles.objects.filter(
                    id_usage_contract_id__id_usage_contract__company=id, begin_date__year__lte=year, end_date__year__lte=year).count() > 0)

        if find_query_in_effect(company):
            return {"has_contract": True, "in_effect": True}
        if find_query_out_of_effect(company):
            return {"has_contract": True, "in_effect": False}

        parent_company_id = self.__get_parent_company_id(company)
        if parent_company_id:
            if find_query_in_effect(parent_company_id):
                return {"has_contract": True, "in_effect": True}
            if find_query_out_of_effect(parent_company_id):
                return {"has_contract": True, "in_effect": False}

        return {"has_contract": False, "in_effect": False}

    def user_allowed_companies(self, user):
        user_companies = get_user_companies(user)
        return Company.objects.filter(id_sap__in=user_companies).values_list('id_company', flat=True)
        
    def user_allowed_company(self, user: dict, company_id):
        return company_id in self.user_allowed_companies(user)