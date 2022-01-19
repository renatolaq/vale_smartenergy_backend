from datetime import datetime, timezone
from copy import copy
from collections import namedtuple
from calendar import month_name, different_locale
from locale import locale_alias
from random import random
from django.db import transaction

from .PlanMonitoringCalculateService import PlanMonitoringCalculateService
from .IntegrationService import IntegrationService
from ..models.PlanMonitoringChangeTrack import CompanyPlanMonitoringChangeAction
from ..models.CompanyPlanMonitoring import CompanyPlanMonitoring, CompanyPlanMonitoringCalculationMode
from ..models.CompanyPlanMonitoringRevision import CompanyPlanMonitoringRevision
from ..models.PlanMonitoringChangeTrack import PlanMonitoringChangeTrack
from ..models.MonthlyPlanMonitoring import MonthlyPlanMonitoring
from ..models.PlanMonitoring import PlanMonitoring


class SavePlanMonitoringService:
    def __init__(self, plan_monitoring_calculate_service: PlanMonitoringCalculateService, integration_service: IntegrationService):
        self.__plan_monitoring_calculate_service = plan_monitoring_calculate_service
        self.__integration_service = integration_service

    @transaction.atomic
    def update_plan_monitoring(self, company_plan_monitoring: CompanyPlanMonitoring, update_data, user, message: str) -> CompanyPlanMonitoring:
        trans_savepoint = transaction.savepoint()

        def select_related(revs, field):
            return revs.select_related(field + "_plan_monitoring") \
                .select_related(field + "_plan_monitoring__january") \
                .select_related(field + "_plan_monitoring__february") \
                .select_related(field + "_plan_monitoring__march") \
                .select_related(field + "_plan_monitoring__april") \
                .select_related(field + "_plan_monitoring__may") \
                .select_related(field + "_plan_monitoring__june") \
                .select_related(field + "_plan_monitoring__july") \
                .select_related(field + "_plan_monitoring__august") \
                .select_related(field + "_plan_monitoring__september") \
                .select_related(field + "_plan_monitoring__october") \
                .select_related(field + "_plan_monitoring__november") \
                .select_related(field + "_plan_monitoring__december")

        revisions = company_plan_monitoring.companyplanmonitoringrevision_set
        revisions = select_related(revisions, "firstyear")
        revisions = select_related(revisions, "secondyear")

        revision = revisions.order_by("-revision")[0]

        revision = self.duplicate_revision(revision)

        revision.revision += 1

        peak_hour_month_data, offpeak_hour_month_data = self.__integration_service.get_hour_month(
            company_plan_monitoring.year)
        company_plan_monitoring_data = update_data.get("company_plan_monitoring", {}) or {}

        ret_update = self.update_monthly_plan_monitoring(
            revision.firstyear_plan_monitoring,
            company_plan_monitoring_data.get("firstyear_plan_monitoring", {}) or {},
            peak_hour_month_data, offpeak_hour_month_data, company_plan_monitoring.company_id, company_plan_monitoring.year, 
            company_plan_monitoring.calculation_mode, revision.contract_usage_factor_offpeak, revision.contract_usage_factor_peak)

        company_plan_monitoring.has_open_justification = ret_update.has_alert
        company_plan_monitoring.save()

        peak_hour_month_data, offpeak_hour_month_data = self.__integration_service.get_hour_month(
            company_plan_monitoring.year + 1)

        self.update_monthly_plan_monitoring(
            revision.secondyear_plan_monitoring,
            company_plan_monitoring_data.get("secondyear_plan_monitoring", {}) or {},
            peak_hour_month_data, offpeak_hour_month_data, company_plan_monitoring.company_id, 
            company_plan_monitoring.year + 1, company_plan_monitoring.calculation_mode, revision.contract_usage_factor_offpeak, revision.contract_usage_factor_peak)

        revision.save()

        PlanMonitoringChangeTrack.objects.create(
            company_plan_monitoring=company_plan_monitoring,
            plan_monitoring_revision=revision.revision,
            comment=message,
            user=user,
            change_at=datetime.now(tz=timezone.utc),
            action=CompanyPlanMonitoringChangeAction.change
        )

        transaction.savepoint_commit(trans_savepoint)

        return company_plan_monitoring

    def update_monthly_plan_monitoring(self, monthly_plan_monitoring: MonthlyPlanMonitoring, monthly_data,
                                       peak_hour_month_data, offpeak_hour_month_data, company, year, calculation_mode, contract_usage_factor_offpeak: float, contract_usage_factor_peak: float, save=True):
        current_year = datetime.now().year
        current_month = datetime.now().month
        previos_month = current_month - 1
        english_month_names = []
        has_alert = False

        realized_offpeak_power_demand_data = self.__integration_service.get_realized_offpeak_power_demand(company, year, contract_usage_factor_offpeak)
        realized_peak_power_demand_data = self.__integration_service.get_realized_peak_power_demand(company, year, contract_usage_factor_peak)
        realized_production_data = self.__integration_service.get_realized_production(company, year)
        realized_peak_power_consumption_data = self.__integration_service.get_realized_peak_power_consumption(company, year)
        realized_offpeak_power_consumption_data = self.__integration_service.get_realized_offpeak_power_consumption(company, year)
        contracted_offpeak_power_demands = self.__integration_service.get_contracted_offpeak_power_demand(company, year, contract_usage_factor_offpeak)
        contracted_peak_power_demands = self.__integration_service.get_contracted_peak_power_demand(company, year, contract_usage_factor_peak)

        with different_locale('C.UTF-8'):
            english_month_names = list(map(lambda s: s.lower(), month_name))

        if(previos_month > 0 and year == current_year):
            plan_monitoring: PlanMonitoring = getattr(monthly_plan_monitoring, english_month_names[previos_month])

            self.__update_plan_monitoring_realized(
                    plan_monitoring,
                    monthly_data.get(english_month_names[previos_month], {}) or {}, calculation_mode)

            self.__update_plan_monitoring_realized_from_integration(previos_month, english_month_names, realized_offpeak_power_demand_data, realized_peak_power_demand_data, realized_production_data, realized_peak_power_consumption_data, realized_offpeak_power_consumption_data, contracted_offpeak_power_demands, contracted_peak_power_demands, plan_monitoring)

            self.__plan_monitoring_calculate_service.calc_plan_monitoring(
                plan_monitoring,
                peak_hour_month_data[english_month_names[previos_month]],
                offpeak_hour_month_data[english_month_names[previos_month]], calculation_mode)

            alerts, has_open_alert = self.__plan_monitoring_calculate_service. \
                generate_plan_monitoring_alerts(plan_monitoring)
            plan_monitoring.__dict__.update(alerts)
            has_alert = has_open_alert
            if(save):
                plan_monitoring.save()

        for i in range(current_month if year == current_year else 1, 13):
            plan_monitoring: PlanMonitoring = getattr(monthly_plan_monitoring, english_month_names[i])

            plan_monitoring.realized_offpeak_power_demand = None
            plan_monitoring.realized_peakpower_demand = None
            plan_monitoring.realized_production = None
            plan_monitoring.realized_peak_power_consumption = None
            plan_monitoring.realized_offpeak_power_consumption = None

            plan_monitoring.realized_offpeak_power_demand_readonly = True
            plan_monitoring.realized_peakpower_demand_readonly = True
            plan_monitoring.realized_production_readonly = True
            plan_monitoring.realized_peak_power_consumption_readonly = True
            plan_monitoring.realized_offpeak_power_consumption_readonly = True
                

            plan_monitoring.contracted_offpeak_power_demand = contracted_offpeak_power_demands.get(english_month_names[i])
            plan_monitoring.contracted_peak_power_demand = contracted_peak_power_demands.get(english_month_names[i])

            if i > current_month or year > current_year:
                self.__update_plan_monitoring_projected(
                    plan_monitoring,
                    monthly_data.get(english_month_names[i], {}) or {})

            self.__plan_monitoring_calculate_service.calc_plan_monitoring(
                plan_monitoring,
                peak_hour_month_data[english_month_names[i]],
                offpeak_hour_month_data[english_month_names[i]], calculation_mode)

            if(save):
                plan_monitoring.save()

        if(save):
            monthly_plan_monitoring.save()

        ret_type = namedtuple("_", ["has_alert"])
        return ret_type(has_alert)

    def __update_plan_monitoring_realized_from_integration(self, previos_month, english_month_names, realized_offpeak_power_demand_data, 
        realized_peak_power_demand_data, realized_production_data, realized_peak_power_consumption_data, 
        realized_offpeak_power_consumption_data, contracted_offpeak_power_demands, contracted_peak_power_demands, plan_monitoring: PlanMonitoring):

        if realized_offpeak_power_demand_data[english_month_names[previos_month]] is not None:
            plan_monitoring.realized_offpeak_power_demand = realized_offpeak_power_demand_data[english_month_names[previos_month]]
        plan_monitoring.realized_offpeak_power_demand_readonly = realized_offpeak_power_demand_data[english_month_names[previos_month]] is not None
        if realized_peak_power_demand_data[english_month_names[previos_month]] is not None:
            plan_monitoring.realized_peakpower_demand = realized_peak_power_demand_data[english_month_names[previos_month]]
        plan_monitoring.realized_peakpower_demand_readonly = plan_monitoring.realized_peakpower_demand is not None
        if realized_production_data[english_month_names[previos_month]] is not None:
            plan_monitoring.realized_production = realized_production_data[english_month_names[previos_month]]
        plan_monitoring.realized_production_readonly = plan_monitoring.realized_production is not None
        if realized_peak_power_consumption_data[english_month_names[previos_month]] is not None:
            plan_monitoring.realized_peak_power_consumption = realized_peak_power_consumption_data[english_month_names[previos_month]]
        plan_monitoring.realized_peak_power_consumption_readonly = plan_monitoring.realized_peak_power_consumption is not None
        if realized_offpeak_power_consumption_data[english_month_names[previos_month]] is not None:
            plan_monitoring.realized_offpeak_power_consumption = realized_offpeak_power_consumption_data[english_month_names[previos_month]]
        plan_monitoring.realized_offpeak_power_consumption_readonly = plan_monitoring.realized_offpeak_power_consumption is not None
        plan_monitoring.realized_total_consumption_readonly = plan_monitoring.realized_peak_power_consumption_readonly or \
                plan_monitoring.realized_offpeak_power_consumption_readonly
        plan_monitoring.contracted_offpeak_power_demand = contracted_offpeak_power_demands.get(english_month_names[previos_month])
        plan_monitoring.contracted_peak_power_demand = contracted_peak_power_demands.get(english_month_names[previos_month])

    def __update_plan_monitoring_projected(self, plan_monitoring: PlanMonitoring, plan_monitoring_data):
        plan_monitoring.projected_peakpower_demand = plan_monitoring_data.get(
            "projected_peakpower_demand", plan_monitoring.projected_peakpower_demand)
        plan_monitoring.projected_offpeak_power_demand = plan_monitoring_data.get(
            "projected_offpeak_power_demand", plan_monitoring.projected_offpeak_power_demand)
        plan_monitoring.projected_peak_power_consumption = plan_monitoring_data.get(
            "projected_peak_power_consumption", plan_monitoring.projected_peak_power_consumption)
        plan_monitoring.projected_offpeak_power_consumption = plan_monitoring_data.get(
            "projected_offpeak_power_consumption", plan_monitoring.projected_offpeak_power_consumption)
        plan_monitoring.projected_production = plan_monitoring_data.get(
            "projected_production", plan_monitoring.projected_production)
        plan_monitoring.projected_productive_stops = plan_monitoring_data.get(
            "projected_productive_stops", plan_monitoring.projected_productive_stops)
        plan_monitoring.projected_total_consumption = plan_monitoring_data.get(
            "projected_total_consumption", plan_monitoring.projected_total_consumption)

    def __update_plan_monitoring_realized(self, plan_monitoring: PlanMonitoring, plan_monitoring_data: dict, calculation_mode: CompanyPlanMonitoringCalculationMode):
        if "realized_peakpower_demand" in plan_monitoring_data:
            plan_monitoring.realized_peakpower_demand = plan_monitoring_data.get("realized_peakpower_demand")
        if "realized_offpeak_power_demand" in plan_monitoring_data:
            plan_monitoring.realized_offpeak_power_demand = plan_monitoring_data.get("realized_offpeak_power_demand")        
        
        if(calculation_mode == CompanyPlanMonitoringCalculationMode.flat):
            if plan_monitoring.realized_peak_power_consumption is None and plan_monitoring.realized_offpeak_power_consumption is None:
                plan_monitoring.realized_total_consumption = plan_monitoring_data.get("realized_total_consumption")
        else:
            if "realized_peak_power_consumption" in plan_monitoring_data:
                plan_monitoring.realized_peak_power_consumption = plan_monitoring_data.get("realized_peak_power_consumption")
            if "realized_offpeak_power_consumption" in plan_monitoring_data:
                plan_monitoring.realized_offpeak_power_consumption = plan_monitoring_data.get("realized_offpeak_power_consumption")
        
        if "realized_production" in plan_monitoring_data:
            plan_monitoring.realized_production = plan_monitoring_data.get("realized_production")

    def duplicate_revision(self, source_revision: CompanyPlanMonitoringRevision) -> CompanyPlanMonitoringRevision:
        def duplicate_plan_monitoring(plan_monitoring):
            plan_monitoring = copy(plan_monitoring)
            plan_monitoring.pk = None
            plan_monitoring.save(force_insert=True)
            return plan_monitoring

        def duplicate_monthly(source_monthly: MonthlyPlanMonitoring):
            source_monthly.january = duplicate_plan_monitoring(
                source_monthly.january)
            source_monthly.february = duplicate_plan_monitoring(
                source_monthly.february)
            source_monthly.march = duplicate_plan_monitoring(
                source_monthly.march)
            source_monthly.april = duplicate_plan_monitoring(
                source_monthly.april)
            source_monthly.may = duplicate_plan_monitoring(
                source_monthly.may)
            source_monthly.june = duplicate_plan_monitoring(
                source_monthly.june)
            source_monthly.july = duplicate_plan_monitoring(
                source_monthly.july)
            source_monthly.august = duplicate_plan_monitoring(
                source_monthly.august)
            source_monthly.september = duplicate_plan_monitoring(
                source_monthly.september)
            source_monthly.october = duplicate_plan_monitoring(
                source_monthly.october)
            source_monthly.november = duplicate_plan_monitoring(
                source_monthly.november)
            source_monthly.december = duplicate_plan_monitoring(
                source_monthly.december)

            source_monthly.pk = None
            source_monthly.save(force_insert=True)
            return source_monthly

        new_revision: CompanyPlanMonitoringRevision = copy(source_revision)
        new_revision.firstyear_plan_monitoring = duplicate_monthly(
            copy(new_revision.firstyear_plan_monitoring))
        new_revision.secondyear_plan_monitoring = duplicate_monthly(
            copy(new_revision.secondyear_plan_monitoring))

        new_revision.pk = None
        new_revision.save(force_insert=True)
        return new_revision
