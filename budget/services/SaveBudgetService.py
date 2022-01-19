from datetime import datetime, timezone
from django.db import transaction
from copy import copy
from calendar import month_name, different_locale

from SmartEnergy.auth import groups, permissions, is_administrator, has_permission

from .BudgetCalculateService import BudgetCalculateService
from .IntegrationService import IntegrationService
from SmartEnergy.utils.exception.ErroWithCode import ErrorWithCode
from ..models.CompanyBudget import CompanyBudget, CompanyBudgetCalculationMode
from ..models.CompanyBudgetRevision import CompanyBudgetRevision, CompanyBudgetRevisionState
from ..models.BudgetChangeTrack import BudgetChangeTrack
from ..models.MonthlyBudget import MonthlyBudget
from ..models.Budget import Budget


class SaveBudgetService:
    def __init__(self, budget_calculate_service: BudgetCalculateService, integration_service: IntegrationService):
        self.__budget_calculate_service = budget_calculate_service
        self.__integration_service = integration_service

    @transaction.atomic
    def create_budget(self, create_data, user, create_state) -> CompanyBudget:
        trans_savepoint = transaction.savepoint()

        company_budget = CompanyBudget()
        company_budget.company_id = create_data["company_id"]
        company_budget.year = create_data["year"]

        calculation_mode = None
        for v in CompanyBudgetCalculationMode:
            if create_data["calculation_mode"] == v.verbose_name:
                calculation_mode = v
                break

        company_budget.calculation_mode = calculation_mode

        revision = CompanyBudgetRevision()
        revision.revision = 1
        revision.state = create_state
        revision.consumption_limit = create_data["budget"]["consumption_limit"]
        revision.contract_usage_factor_offpeak = create_data[
            "budget"]["contract_usage_factor_offpeak"]
        revision.contract_usage_factor_peak = create_data["budget"]["contract_usage_factor_peak"]

        peak_hour_month_data, offpeak_hour_month_data = self.__integration_service.get_hour_month(
            company_budget.year)

        if(company_budget.calculation_mode == CompanyBudgetCalculationMode.flat):
            self.__budget_calculate_service.unflat_monthly_budget_data(create_data["budget"]["firstyear_budget"],
                                                                       peak_hour_month_data, offpeak_hour_month_data)
        monthly_budget = self.__generate_empty_monthly_budget()
        self.__update_monthly_budget(
            monthly_budget,
            create_data["budget"]["firstyear_budget"],
            company_budget.company_id,
            company_budget.year,
            revision.consumption_limit,
            revision.contract_usage_factor_offpeak,
            revision.contract_usage_factor_peak,
            peak_hour_month_data, offpeak_hour_month_data)
        revision.firstyear_budget = monthly_budget

        peak_hour_month_data, offpeak_hour_month_data = self.__integration_service.get_hour_month(
            company_budget.year+1)
        if(company_budget.calculation_mode == CompanyBudgetCalculationMode.flat):
            self.__budget_calculate_service.unflat_monthly_budget_data(create_data["budget"]["secondyear_budget"],
                                                                       peak_hour_month_data, offpeak_hour_month_data)
        monthly_budget = self.__generate_empty_monthly_budget()
        self.__update_monthly_budget(
            monthly_budget,
            create_data["budget"]["secondyear_budget"],
            company_budget.company_id,
            company_budget.year+1,
            revision.consumption_limit,
            revision.contract_usage_factor_offpeak,
            revision.contract_usage_factor_peak,
            peak_hour_month_data, offpeak_hour_month_data)
        revision.secondyear_budget = monthly_budget

        peak_hour_month_data, offpeak_hour_month_data = self.__integration_service.get_hour_month(
            company_budget.year+2)
        monthly_budget_data = self.__budget_calculate_service.distribute_amoung_months(
            create_data["budget"]["thirdyear_budget"], company_budget.year+2)
        if(company_budget.calculation_mode == CompanyBudgetCalculationMode.flat):
            self.__budget_calculate_service.unflat_monthly_budget_data(monthly_budget_data,
                                                                       peak_hour_month_data, offpeak_hour_month_data)
        monthly_budget = self.__generate_empty_monthly_budget()
        self.__update_monthly_budget(
            monthly_budget, monthly_budget_data,
            company_budget.company_id,
            company_budget.year+2,
            revision.consumption_limit,
            revision.contract_usage_factor_offpeak,
            revision.contract_usage_factor_peak,
            peak_hour_month_data, offpeak_hour_month_data)
        revision.thirdyear_budget = monthly_budget

        peak_hour_month_data, offpeak_hour_month_data = self.__integration_service.get_hour_month(
            company_budget.year+3)
        monthly_budget_data = self.__budget_calculate_service.distribute_amoung_months(
            create_data["budget"]["fourthyear_budget"], company_budget.year+3)
        if(company_budget.calculation_mode == CompanyBudgetCalculationMode.flat):
            self.__budget_calculate_service.unflat_monthly_budget_data(monthly_budget_data,
                                                                       peak_hour_month_data, offpeak_hour_month_data)
        monthly_budget = self.__generate_empty_monthly_budget()
        self.__update_monthly_budget(
            monthly_budget, monthly_budget_data,
            company_budget.company_id,
            company_budget.year+3,
            revision.consumption_limit,
            revision.contract_usage_factor_offpeak,
            revision.contract_usage_factor_peak,
            peak_hour_month_data, offpeak_hour_month_data)
        revision.fourthyear_budget = monthly_budget

        peak_hour_month_data, offpeak_hour_month_data = self.__integration_service.get_hour_month(
            company_budget.year+4)
        monthly_budget_data = self.__budget_calculate_service.distribute_amoung_months(
            create_data["budget"]["fifthyear_budget"], company_budget.year+4)
        if(company_budget.calculation_mode == CompanyBudgetCalculationMode.flat):
            self.__budget_calculate_service.unflat_monthly_budget_data(monthly_budget_data,
                                                                       peak_hour_month_data, offpeak_hour_month_data)
        monthly_budget = self.__generate_empty_monthly_budget()
        self.__update_monthly_budget(
            monthly_budget, monthly_budget_data,
            company_budget.company_id,
            company_budget.year+4,
            revision.consumption_limit,
            revision.contract_usage_factor_offpeak,
            revision.contract_usage_factor_peak,
            peak_hour_month_data, offpeak_hour_month_data)
        revision.fifthyear_budget = monthly_budget

        company_budget.save()
        revision.company_budget = company_budget
        revision.save()

        BudgetChangeTrack.objects.create(
            company_budget=company_budget,
            budget_revision=1,
            comment="-",
            user=user,
            change_at=datetime.now(tz=timezone.utc),
            state=create_state
        )

        transaction.savepoint_commit(trans_savepoint)

        return company_budget

    @transaction.atomic
    def update_budget(self, company_budget, update_data, user) -> CompanyBudget:
        trans_savepoint = transaction.savepoint()

        revision = company_budget.companybudgetrevision_set.order_by(
            "-revision")[0]

        if(not self.__is_allowed_change_state(revision.state)):
            raise ErrorWithCode.from_error(
                "BUDGET_CHANGE_NOT_ALLOWED",
                "Changes in budget with state different from budgeting or releasedToAnalysis",
                f"/budgets/{revision.revision}/state")

        new_revision = self.duplicate_revision(revision)

        new_revision.consumption_limit = update_data["budget"]["consumption_limit"]
        new_revision.contract_usage_factor_offpeak = update_data[
            "budget"]["contract_usage_factor_offpeak"]
        new_revision.contract_usage_factor_peak = update_data["budget"]["contract_usage_factor_peak"]
        new_revision.revision += 1

        peak_hour_month_data, offpeak_hour_month_data = self.__integration_service.get_hour_month(
            company_budget.year)
        if(company_budget.calculation_mode == CompanyBudgetCalculationMode.flat):
            self.__budget_calculate_service.unflat_monthly_budget_data(update_data["budget"]["firstyear_budget"],
                                                                       peak_hour_month_data, offpeak_hour_month_data)
        self.__update_monthly_budget(
            new_revision.firstyear_budget,
            update_data["budget"]["firstyear_budget"],
            company_budget.company_id,
            company_budget.year,
            new_revision.consumption_limit,
            new_revision.contract_usage_factor_offpeak,
            new_revision.contract_usage_factor_peak,
            peak_hour_month_data, offpeak_hour_month_data)

        peak_hour_month_data, offpeak_hour_month_data = self.__integration_service.get_hour_month(
            company_budget.year+1)
        if(company_budget.calculation_mode == CompanyBudgetCalculationMode.flat):
            self.__budget_calculate_service.unflat_monthly_budget_data(update_data["budget"]["secondyear_budget"],
                                                                       peak_hour_month_data, offpeak_hour_month_data)
        self.__update_monthly_budget(
            new_revision.secondyear_budget,
            update_data["budget"]["secondyear_budget"],
            company_budget.company_id,
            company_budget.year+1,
            new_revision.consumption_limit,
            new_revision.contract_usage_factor_offpeak,
            new_revision.contract_usage_factor_peak,
            peak_hour_month_data, offpeak_hour_month_data)

        peak_hour_month_data, offpeak_hour_month_data = self.__integration_service.get_hour_month(
            company_budget.year+2)
        monthly_budget_data = self.__budget_calculate_service.distribute_amoung_months(
            update_data["budget"]["thirdyear_budget"], company_budget.year+2)
        if(company_budget.calculation_mode == CompanyBudgetCalculationMode.flat):
            self.__budget_calculate_service.unflat_monthly_budget_data(monthly_budget_data,
                                                                       peak_hour_month_data, offpeak_hour_month_data)
        self.__update_monthly_budget(
            new_revision.thirdyear_budget, monthly_budget_data,
            company_budget.company_id,
            company_budget.year+2,
            new_revision.consumption_limit,
            new_revision.contract_usage_factor_offpeak,
            new_revision.contract_usage_factor_peak,
            peak_hour_month_data, offpeak_hour_month_data)

        peak_hour_month_data, offpeak_hour_month_data = self.__integration_service.get_hour_month(
            company_budget.year+3)
        monthly_budget_data = self.__budget_calculate_service.distribute_amoung_months(
            update_data["budget"]["fourthyear_budget"], company_budget.year+3)
        if(company_budget.calculation_mode == CompanyBudgetCalculationMode.flat):
            self.__budget_calculate_service.unflat_monthly_budget_data(monthly_budget_data,
                                                                       peak_hour_month_data, offpeak_hour_month_data)
        self.__update_monthly_budget(
            new_revision.fourthyear_budget, monthly_budget_data,
            company_budget.company_id,
            company_budget.year+3,
            new_revision.consumption_limit,
            new_revision.contract_usage_factor_offpeak,
            new_revision.contract_usage_factor_peak,
            peak_hour_month_data, offpeak_hour_month_data)

        peak_hour_month_data, offpeak_hour_month_data = self.__integration_service.get_hour_month(
            company_budget.year+4)
        monthly_budget_data = self.__budget_calculate_service.distribute_amoung_months(
            update_data["budget"]["fifthyear_budget"], company_budget.year+4)
        if(company_budget.calculation_mode == CompanyBudgetCalculationMode.flat):
            self.__budget_calculate_service.unflat_monthly_budget_data(monthly_budget_data,
                                                                       peak_hour_month_data, offpeak_hour_month_data)
        self.__update_monthly_budget(
            new_revision.fifthyear_budget, monthly_budget_data,
            company_budget.company_id,
            company_budget.year+4,
            new_revision.consumption_limit,
            new_revision.contract_usage_factor_offpeak,
            new_revision.contract_usage_factor_peak,
            peak_hour_month_data, offpeak_hour_month_data)

        new_revision.save()

        BudgetChangeTrack.objects.create(
            company_budget=company_budget,
            budget_revision=new_revision.revision,
            comment="-",
            user=user,
            change_at=datetime.now(tz=timezone.utc),
            state=new_revision.state
        )

        transaction.savepoint_commit(trans_savepoint)

        return company_budget

    @transaction.atomic
    def duplicate_revision(self, source_revision: CompanyBudgetRevision) -> CompanyBudgetRevision:
        def duplicate_budget(budget):
            budget = copy(budget)
            budget.pk = None
            budget.save(force_insert=True)
            return budget

        def duplicate_monthly(source_monthly: MonthlyBudget):
            source_monthly.january = duplicate_budget(
                source_monthly.january)
            source_monthly.february = duplicate_budget(
                source_monthly.february)
            source_monthly.march = duplicate_budget(
                source_monthly.march)
            source_monthly.april = duplicate_budget(
                source_monthly.april)
            source_monthly.may = duplicate_budget(
                source_monthly.may)
            source_monthly.june = duplicate_budget(
                source_monthly.june)
            source_monthly.july = duplicate_budget(
                source_monthly.july)
            source_monthly.august = duplicate_budget(
                source_monthly.august)
            source_monthly.september = duplicate_budget(
                source_monthly.september)
            source_monthly.october = duplicate_budget(
                source_monthly.october)
            source_monthly.november = duplicate_budget(
                source_monthly.november)
            source_monthly.december = duplicate_budget(
                source_monthly.december)

            source_monthly.pk = None
            source_monthly.save(force_insert=True)
            return source_monthly

        new_revision: CompanyBudgetRevision = copy(source_revision)
        new_revision.firstyear_budget = duplicate_monthly(
            copy(new_revision.firstyear_budget))
        new_revision.secondyear_budget = duplicate_monthly(
            copy(new_revision.secondyear_budget))
        new_revision.thirdyear_budget = duplicate_monthly(
            copy(new_revision.thirdyear_budget))
        new_revision.fourthyear_budget = duplicate_monthly(
            copy(new_revision.fourthyear_budget))
        new_revision.fifthyear_budget = duplicate_monthly(
            copy(new_revision.fifthyear_budget))

        new_revision.pk = None
        new_revision.save(force_insert=True)
        return new_revision

    def __generate_empty_monthly_budget(self):
        def gen():
            b = Budget()
            b.save()
            return b

        ret = MonthlyBudget(
            january=gen(),
            february=gen(),
            march=gen(),
            april=gen(),
            may=gen(),
            june=gen(),
            july=gen(),
            august=gen(),
            september=gen(),
            october=gen(),
            november=gen(),
            december=gen())
        ret.save()
        return ret

    def __update_monthly_budget(self, monthly_budget, monthly_data, company: int, year: int, consumption_limit: float, contract_usage_factor_offpeak: float, contract_usage_factor_peak: float, peak_hour_month_data, offpeak_hour_month_data):
        contracted_peak_power_demand = self.__integration_service.get_contracted_peak_power_demand(
            company, year, contract_usage_factor_peak)
        contracted_offpeak_power_demand = self.__integration_service.get_contracted_offpeak_power_demand(
            company, year, contract_usage_factor_offpeak)
        production = self.__integration_service.get_production(company, year)

        def update(month):
            monthly_data[month]["contracted_peak_power_demand"] = contracted_peak_power_demand.get(
                month) if contracted_peak_power_demand.get(month) is not None else monthly_data[month]["contracted_peak_power_demand"]
            monthly_data[month]["contracted_offpeak_power_demand"] = contracted_offpeak_power_demand.get(
                month) if contracted_offpeak_power_demand.get(month) is not None else monthly_data[month]["contracted_offpeak_power_demand"]
            monthly_data[month]["production"] = production.get(month) if production.get(
                month) is not None else monthly_data[month]["production"]
            monthly_data[month]["production_readonly"] = production.get(
                month) is not None
            self.__update_budget(
                getattr(monthly_budget, month), monthly_data[month], consumption_limit, peak_hour_month_data[month], offpeak_hour_month_data[month])

        english_month_names = []
        with different_locale('C.UTF-8'):
            english_month_names = list(
                map(lambda s: s.lower(), month_name[1:]))

        for month in english_month_names:
            update(month)

        monthly_budget.save()

    def __update_budget(self, budget: Budget, budget_data, consumption_limit: float, peak_hour_month, offpeak_hour_month):
        budget.contracted_peak_power_demand = budget_data.get(
            "contracted_peak_power_demand")
        budget.contracted_offpeak_power_demand = budget_data.get(
            "contracted_offpeak_power_demand")
        budget.estimated_peak_power_demand = budget_data.get(
            "estimated_peak_power_demand")
        budget.estimated_offpeak_power_demand = budget_data.get(
            "estimated_offpeak_power_demand")
        budget.consumption_peak_power_demand = budget_data.get(
            "consumption_peak_power_demand")
        budget.consumption_offpeak_power_demand = budget_data.get(
            "consumption_offpeak_power_demand")
        budget.production = budget_data.get("production")
        budget.production_readonly = budget_data.get("production_readonly")
        budget.productive_stops = budget_data.get("productive_stops")

        self.__budget_calculate_service.calc_budget_update_object(
            budget, budget_data, consumption_limit, peak_hour_month, offpeak_hour_month)

        budget.save()

    def is_allowed_year(self, year):
        next_year = datetime.now().year + 1
        return year == next_year or year == 2019 or year == 2020

    def __is_allowed_change_state(self, state: CompanyBudgetRevisionState):
        return state in [CompanyBudgetRevisionState.budgeting, 
            CompanyBudgetRevisionState.releasedto_analysis, 
            CompanyBudgetRevisionState.disapproved, CompanyBudgetRevisionState.in_creation_by_analyst]

    def allow_update(self, company_budget: CompanyBudget, user: dict):
        last_revision: CompanyBudgetRevision = company_budget.companybudgetrevision_set.order_by(
            "-revision")[0]

        if is_administrator(user):
            return True

        if last_revision.state == CompanyBudgetRevisionState.releasedto_analysis:
            return has_permission(user, groups.budget_projections, [permissions.EDITN2])

        if last_revision.state == CompanyBudgetRevisionState.in_creation_by_analyst:
            return has_permission(user, groups.budget_projections, [permissions.EDITN2])

        if last_revision.state in [CompanyBudgetRevisionState.budgeting, CompanyBudgetRevisionState.disapproved]:
            return self.__integration_service.user_allowed_company(user, company_budget.company_id) and \
                has_permission(user, groups.budget_projections,
                               [permissions.EDITN1])

        return False
