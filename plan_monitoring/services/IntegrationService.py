from typing import List, Callable
from calendar import month_name, different_locale, datetime, monthrange

from django.db.models.aggregates import Max
from django.db.models.expressions import F, Subquery
from django.db.models.fields import IntegerField
from core.views import get_peek_time_logic

from usage_contract.models import TaxModality, ContractCycles
from gauge_point.models import GaugeData
from budget.models.CompanyBudget import CompanyBudget
from budget.models.CompanyBudgetRevision import CompanyBudgetRevision, CompanyBudgetRevisionState
from budget.serializers.CompanyBudgetSerializer import CompanyBudgetSerializer
from SmartEnergy.auth import get_user_companies
from company.models import Company
from asset_items.models import AssetItems
from consumption_metering_reports.models import MeteringReportValue, Report

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

    def __get_gauge_data(self, company: int, year: int, id_measurements: int, factor: float = 1):
        ret = {}

        english_month_names = []
        with different_locale('C.UTF-8'):
            english_month_names = list(map(lambda s: s.lower(), month_name))

        data: List[GaugeData] = list(GaugeData.objects.filter(
            id_measurements=id_measurements, id_gauge__id_company=company, utc_gauge__year=year))

        for month in range(1, 13):
            month_data = list(
                filter(lambda g: g.utc_gauge.month == month, data))
            if len(month_data):
                ret[english_month_names[month]] = float(sum(
                    map(lambda g: g.value, month_data))) * factor
            else:
                ret[english_month_names[month]] = None

        return ret

    def get_realized_production(self, company: int, year: int):  # 5
        return self.__get_gauge_data(company, year, 1)

    def get_realized_offpeak_power_demand(self, company: int, year: int, factor: float):  # 3
        if self.can_split_contract(company):
            company = self.__get_parent_company_id(company) or company
            factor = factor if factor <= 1 else 1
            factor = factor if factor >= 0 else 0
        else:
            factor = 1
        return self.__get_gauge_data(company, year, 24, factor)

    def get_realized_peak_power_demand(self, company: int, year: int, factor: float):  # 4
        if self.can_split_contract(company):
            company = self.__get_parent_company_id(company) or company
            factor = factor if factor <= 1 else 1
            factor = factor if factor >= 0 else 0
        else:
            factor = 1
        return self.__get_gauge_data(company, year, 23, factor)

    def __get_metering_report_value(self, company: int, year: int, value_field: str):
        report_values = MeteringReportValue.objects.filter(
            metering_report_data__id_company=company, 
            metering_report_data__report__status='S',
            metering_report_data__report__id__in=
                Subquery(Report.objects.filter(
                    year=year, report_type=6).values('month').annotate(id=Max('id')).values('id'))) \
            .annotate(
                month=F('metering_report_data__report__month'))
        
        ret = {}

        english_month_names = []
        with different_locale('C.UTF-8'):
            english_month_names = list(map(lambda s: s.lower(), month_name))

        for month in range(1, 13):
            month_data = list(
                filter(lambda g: int(g.month) == month, report_values))
            if len(month_data):
                ret[english_month_names[month]] = float(sum(
                    map(lambda g: getattr(g, value_field), month_data)))
            else:
                ret[english_month_names[month]] = None

        return ret
    
    def get_realized_peak_power_consumption(self, company: int, year: int):  # 6
        return self.__get_metering_report_value(company, year, 'on_peak_consumption_value')   

    def get_realized_offpeak_power_consumption(self, company: int, year: int): # 7
        return self.__get_metering_report_value(company, year, 'off_peak_consumption_value')   

    def get_budget_by_company(self, company_id: int, year: int):
        company_budget = CompanyBudget.objects.filter(
            company_id=company_id, year=year).first()
        revision: CompanyBudgetRevision = company_budget. \
            companybudgetrevision_set.order_by("-revision")[0]

        if(revision.state == CompanyBudgetRevisionState.energy_manager_approved):
            serializer = CompanyBudgetSerializer({
                "id": company_budget.id,
                "year": company_budget.year,
                "company_id": company_id,
                "calculation_mode": company_budget.calculation_mode,
                "companybudgetrevision_set": [revision],
                "budgetchangetrack_set": []
            })
            return serializer.data
        return None

    def get_budgets_by_year(self, year: int):
        company_budgets = CompanyBudget.objects.filter(year=year)
        ret = []
        
        for company_budget in company_budgets:        
            revision: CompanyBudgetRevision = company_budget. \
                companybudgetrevision_set.order_by("-revision")[0]

            if(revision.state == CompanyBudgetRevisionState.energy_manager_approved):
                serializer = CompanyBudgetSerializer({
                    "id": company_budget.id,
                    "year": company_budget.year,
                    "company_id": company_budget.company_id,
                    "calculation_mode": company_budget.calculation_mode,
                    "companybudgetrevision_set": [revision],
                    "budgetchangetrack_set": []
                })
                ret.append(serializer.data)
        return ret

    def user_allowed_companies(self, user):
        user_companies = get_user_companies(user)
        return Company.objects.filter(id_sap__in=user_companies).values_list('id_company', flat=True)
        
    def user_allowed_company(self, user: dict, company_id):
        return company_id in self.user_allowed_companies(user)

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

    def can_split_contract(self, company: int) -> bool:
        parent_company_id = self.__get_parent_company_id(company)
        return (parent_company_id is not None and parent_company_id != company)

    def __get_parent_company_id(self, company):
        asset_item: AssetItems = AssetItems.objects.select_related(
            "id_assets").filter(id_company=company).first()
        if asset_item:
            return asset_item.id_assets.id_company.id_company
        return None

    def get_contracted_peak_power_demand(self, company: int, year: int, factor: float):
        return self.__get_usage_contracts(company, year, factor, True)

    def get_contracted_offpeak_power_demand(self, company: int, year: int, factor: float):
        return self.__get_usage_contracts(company, year, factor, False)