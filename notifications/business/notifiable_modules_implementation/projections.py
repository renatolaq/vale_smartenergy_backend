from ..notifiable_modules import Modules
from ..notifiable_modules_abstract import AbstractClassNotifiableModule
from plan_monitoring.models.CompanyPlanMonitoringRevision import CompanyPlanMonitoringRevision
from plan_monitoring.models.MonthlyPlanMonitoring import MonthlyPlanMonitoring
from django.db.models.signals import post_save
from django.dispatch import receiver
import notifications.business.signal_business as signal_business

def generate_month_rows(year="firstyear", month="january"):
    base_fields = [
        "contracted_offpeak_power_demand",
        "contracted_peak_power_demand",
        "estimated_offpeak_power_consumption",
        "estimated_offpeak_power_demand",
        "estimated_peak_power_consumption",
        "estimated_peak_power_demand",
        "estimated_production",
        "estimated_productive_stops",
        "estimated_specific_consumption",
        "estimated_total_consumption",
        "projected_offpeak_power_consumption",
        "projected_offpeak_power_demand",
        "projected_peak_power_consumption",
        "projected_peak_power_demand",
        "projected_production",
        "projected_productive_stops",
        "projected_specific_consumption",
        "projected_total_consumption",
        "realized_load_factor_consistency_offpeak_power",
        "realized_load_factor_consistency_peak_power",
        "realized_modulation_factor_consistency",
        "realized_offpeak_power_consumption",
        "realized_offpeak_power_demand",
        "realized_peak_power_consumption",
        "realized_peak_power_demand",
        "realized_production",
        "realized_specific_consumption",
        "realized_total_consumption",
        "realized_unique_load_factor_consistency",
        "realized_utilization_factor_consistency_offpeak_power",
        "realized_utilization_factor_consistency_peak_power",
        "variation_consumption_estimated_projected",
        "variation_consumption_estimated_realized",
        "variation_specific_consumption_estimated_projected",
        "variation_specific_consumption_estimated_realized"
    ]

    return [f'{year}_plan_monitoring__{month}__{field}' for field in base_fields]

def generate_month_fields(year="firstyear"):
    months = [
        "january",
        "february",
        "march",
        "april",
        "may",
        "june",
        "july",
        "august",
        "september",
        "october",
        "november",
        "december"
    ]

    year_fields = []

    for month in months:
        year_fields += generate_month_rows(year, month)

    return year_fields

class ProjectionsNotifiableModule(AbstractClassNotifiableModule):
    main_model = CompanyPlanMonitoringRevision
    module_name = Modules.PROJECTIONS

    def get_specified_fields(self):
        firstyear_fields = generate_month_fields(year="firstyear")
        secondyear_fields = generate_month_fields(year="secondyear")

        specified_fields = [
            "revision",
            "contract_usage_factor_peak",
            "contract_usage_factor_offpeak",
            "company_plan_monitoring__year",
            "company_plan_monitoring__company_id",
            "company_plan_monitoring__has_open_justification",
            "company_plan_monitoring__calculation_mode"
        ]

        specified_fields += firstyear_fields
        specified_fields += secondyear_fields

        return specified_fields

    def get_fields(self):
        non_related_fields, related_fields = super().get_fields()
        additional_deeper_fields = []

        deeper_fields = super().get_fields(
            specific_model=MonthlyPlanMonitoring,
            source_path="firstyear_plan_monitoring"
        )
        additional_deeper_fields += deeper_fields[0]
        additional_deeper_fields += deeper_fields[1]

        deeper_fields = super().get_fields(
            specific_model=MonthlyPlanMonitoring,
            source_path="secondyear_plan_monitoring"
        )
        additional_deeper_fields += deeper_fields[0]
        additional_deeper_fields += deeper_fields[1]

        related_fields += additional_deeper_fields

        specified_fields = self.get_specified_fields()

        try:
            non_related_fields = [
                field
                for field in non_related_fields
                if field["name"] in specified_fields
            ]
            related_fields = [
                field
                for field in related_fields
                if field["name"] in specified_fields
            ]
        except IndexError:
            pass

        return non_related_fields, related_fields

    @staticmethod
    @receiver(post_save, sender=main_model)
    def post_save_signal_handler(sender, instance, **kwargs):
        kwargs["notifiable_module"] = ProjectionsNotifiableModule()
        signal_business.NotificationSignalBusiness.dispatch_signal(
            sender, instance, **kwargs
        )
