
from ..models.PlanMonitoring import PlanMonitoring
from collections import namedtuple
from ..models.CompanyPlanMonitoring import CompanyPlanMonitoringCalculationMode
from calendar import month_name, different_locale
from datetime import datetime

class PlanMonitoringCalculateService:
    def unflat_plan_monitoring_data(self, plan_monitoring_data, peak_hours, offpeak_hours):
        if (plan_monitoring_data["projected_total_consumption"] is not None):
            plan_monitoring_data["projected_peak_power_consumption"] = (
                peak_hours / (peak_hours + offpeak_hours)) * plan_monitoring_data["projected_total_consumption"]
            plan_monitoring_data["projected_offpeak_power_consumption"] = (
                offpeak_hours / (peak_hours + offpeak_hours)) * plan_monitoring_data["projected_total_consumption"]
        else:
            plan_monitoring_data["projected_peak_power_consumption"] = None
            plan_monitoring_data["projected_offpeak_power_consumption"] = None

        if (bool(plan_monitoring_data["realized_total_consumption"])):
            plan_monitoring_data["realized_peak_power_consumption"] = (
                peak_hours / (peak_hours + offpeak_hours)) * plan_monitoring_data["realized_total_consumption"]
            plan_monitoring_data["realized_offpeak_power_consumption"] = (
                offpeak_hours / (peak_hours + offpeak_hours)) * plan_monitoring_data["realized_total_consumption"]

    def calc_plan_monitoring(self, plan_monitoring: PlanMonitoring,
                             peak_hour_month, offpeak_hour_month, calculation_mode):
        def calc_if_valued(func, *args):
            if(all(value is not None for value in args)):
                return func(*args)
            return None

        plan_monitoring_data = plan_monitoring.__dict__

        if(calculation_mode == CompanyPlanMonitoringCalculationMode.flat):
            self.unflat_plan_monitoring_data(plan_monitoring_data,
                                             peak_hour_month, offpeak_hour_month)

        plan_monitoring.estimated_total_consumption = calc_if_valued(
            self.calc_total_consumption,
            plan_monitoring_data.get("estimated_peak_power_consumption"),
            plan_monitoring_data.get("estimated_offpeak_power_consumption")
        )
        plan_monitoring.realized_total_consumption = calc_if_valued(
            self.calc_total_consumption,
            plan_monitoring_data.get("realized_peak_power_consumption"),
            plan_monitoring_data.get("realized_offpeak_power_consumption")
        )
        plan_monitoring.projected_total_consumption = calc_if_valued(
            self.calc_total_consumption,
            plan_monitoring_data.get("projected_peak_power_consumption"),
            plan_monitoring_data.get("projected_offpeak_power_consumption")
        )
        plan_monitoring.variation_consumption_estimated_realized = calc_if_valued(
            self.calc_variation,
            plan_monitoring.realized_total_consumption,
            plan_monitoring.estimated_total_consumption)
        plan_monitoring.variation_consumption_estimated_projected = calc_if_valued(
            self.calc_variation,
            plan_monitoring.realized_total_consumption,
            plan_monitoring.projected_total_consumption)
        plan_monitoring.realized_utilization_factor_consistency_offpeakpower = calc_if_valued(
            self.calc_realized_utilization_factor_consistency_power,
            plan_monitoring_data.get("realized_offpeak_power_demand"),
            plan_monitoring_data.get("contracted_offpeak_power_demand")
        )
        plan_monitoring.realized_utilization_factor_consistency_peakpower = calc_if_valued(
            self.calc_realized_utilization_factor_consistency_power,
            plan_monitoring_data.get("realized_peakpower_demand"),
            plan_monitoring_data.get("contracted_peak_power_demand")
        )
        plan_monitoring.realized_load_factor_consistency_offpeakpower = calc_if_valued(
            self.calc_realized_load_factor_consistency_power,
            plan_monitoring_data.get("realized_offpeak_power_consumption"),
            plan_monitoring_data.get("realized_offpeak_power_demand"),
            offpeak_hour_month
        )
        plan_monitoring.realized_load_factor_consistency_peakpower = calc_if_valued(
            self.calc_realized_load_factor_consistency_power,
            plan_monitoring_data.get("realized_peak_power_consumption"),
            plan_monitoring_data.get("realized_peakpower_demand"),
            peak_hour_month
        )
        plan_monitoring.realized_uniqueload_factor_consistency = calc_if_valued(
            self.calc_unique_load_factor_consistency,
            plan_monitoring_data.get("realized_peak_power_consumption"),
            plan_monitoring_data.get("realized_offpeak_power_consumption"),
            offpeak_hour_month,
            peak_hour_month,
            plan_monitoring_data.get("realized_peakpower_demand"),
            plan_monitoring_data.get("realized_offpeak_power_demand")
        )
        plan_monitoring.realized_modulation_factor_consistency = calc_if_valued(
            self.calc_modulation_factor_consistency,
            plan_monitoring_data.get("realized_peakpower_demand"),
            plan_monitoring_data.get("realized_offpeak_power_demand")
        )
        plan_monitoring.estimated_specific_consumption = calc_if_valued(
            self.calc_specific_consumption,
            plan_monitoring_data.get("estimated_total_consumption"),
            plan_monitoring_data.get("estimated_production")
        )
        plan_monitoring.realized_specific_consumption = calc_if_valued(
            self.calc_specific_consumption,
            plan_monitoring_data.get("realized_total_consumption"),
            plan_monitoring_data.get("realized_production")
        )
        plan_monitoring.projected_specific_consumption = calc_if_valued(
            self.calc_specific_consumption,
            plan_monitoring_data.get("projected_total_consumption"),
            plan_monitoring_data.get("projected_production")
        )
        plan_monitoring.variation_specific_consumption_estimated_realized = calc_if_valued( 
            self.calc_variation,
            plan_monitoring.realized_specific_consumption,
            plan_monitoring.estimated_specific_consumption)
        plan_monitoring.variation_specific_consumption_estimated_projected = calc_if_valued(
            self.calc_variation,
            plan_monitoring.realized_specific_consumption,
            plan_monitoring.projected_specific_consumption)

    def generate_plan_monitoring_alerts(self, plan_monitoring: PlanMonitoring):
        ret = {}
        has_open_alert = False

        def diverges_more_than_5_per_of_planned(field_realized, field_projected):
            nonlocal has_open_alert
            if(plan_monitoring.__dict__.get(field_realized) is not None and 
                plan_monitoring.__dict__.get(field_projected) is not None):

                if(plan_monitoring.__dict__[field_realized] > plan_monitoring.__dict__[field_projected] * 1.05 or 
                    plan_monitoring.__dict__[field_realized] < plan_monitoring.__dict__[field_projected] * 0.95):

                    current_alerts = ret.get(field_realized + "_alerts", [])
                    current_alerts = [a for a in current_alerts if a.startswith(
                        "VALUE_DIVERGES_MORE_THAN_5_PER_OF_PLANNED:")]
                    
                    saved_alerts = plan_monitoring.__dict__.get(field_realized + "_alerts", []) or []
                    saved_alerts = [a for a in saved_alerts if a.startswith(
                        "VALUE_DIVERGES_MORE_THAN_5_PER_OF_PLANNED:")]

                    if saved_alerts:
                        current_alerts = [saved_alerts[0]]

                    if not current_alerts:
                        ret[field_realized + "_alerts"] = [
                            "VALUE_DIVERGES_MORE_THAN_5_PER_OF_PLANNED:"] + current_alerts
                        has_open_alert = True
                    elif(current_alerts[0].endswith(":")):
                        has_open_alert = True

        def greater_than_and_less_than_5_per(field):
            nonlocal has_open_alert
            if(plan_monitoring.__dict__.get(field) is not None):

                if(plan_monitoring.__dict__[field] > 1.05 or 
                    plan_monitoring.__dict__[field] < 0.95):

                    current_alerts = ret.get(field + "_alerts", [])
                    current_alerts = [a for a in current_alerts if a.startswith(
                        "VALUE_DIVERGES_MORE_THAN_5_PER_OF_PLANNED:")]
                    
                    saved_alerts = plan_monitoring.__dict__.get(field + "_alerts", []) or []
                    saved_alerts = [a for a in saved_alerts if a.startswith(
                        "VALUE_DIVERGES_MORE_THAN_5_PER_OF_PLANNED:")]

                    if saved_alerts:
                        current_alerts = [saved_alerts[0]]

                    if not current_alerts:
                        ret[field + "_alerts"] = [
                            "VALUE_DIVERGES_MORE_THAN_5_PER_OF_PLANNED:"] + current_alerts
                        has_open_alert = True
                    elif(current_alerts[0].endswith(":")):
                        has_open_alert = True

        diverges_more_than_5_per_of_planned("realized_total_consumption", "projected_total_consumption")
        diverges_more_than_5_per_of_planned("realized_specific_consumption", "projected_specific_consumption")        
        greater_than_and_less_than_5_per("realized_utilization_factor_consistency_offpeakpower")
        greater_than_and_less_than_5_per("realized_utilization_factor_consistency_peakpower")

        ret_type = namedtuple("Alerts", ["alerts", "has_open_alert"])
        return ret_type(ret, has_open_alert)

    def calc_total_consumption(self, consumption_peak_power: float,
                               consumption_offpeak_power: float):
        return consumption_peak_power + consumption_offpeak_power

    def calc_realized_utilization_factor_consistency_power(self, realized_power_demand: float,
                                                           contracted_power_demand: float):
        if(contracted_power_demand == 0):
            return 0

        return realized_power_demand / contracted_power_demand

    def calc_realized_load_factor_consistency_power(self, power_consumption: float,
                                                    power_demand: float, hour_month: float):
        if(hour_month == 0 or power_demand == 0):
            return 0

        return ((power_consumption * 1000) / hour_month)/power_demand

    def calc_unique_load_factor_consistency(self, peak_power_consumption: float,
                                            offpeak_power_consumption: float,
                                            offpeak_hour_month: float,
                                            peak_hour_month: float,
                                            peak_power_demand: float,
                                            offpeak_power_demand: float):
        if(peak_power_demand == 0 and offpeak_power_demand == 0):
            return 0
        if(offpeak_hour_month == 0 and peak_hour_month == 0):
            return 0
        return ((peak_power_consumption+offpeak_power_consumption)/(offpeak_hour_month+peak_hour_month))/max(peak_power_demand, offpeak_power_demand)

    def calc_modulation_factor_consistency(self, peak_power_demand: float,
                                           offpeak_power_demand: float):
        if(offpeak_power_demand == 0):
            return 0
        return 1 - (peak_power_demand/offpeak_power_demand)

    def calc_specific_consumption(self, total_consumption: float,
                                  production: float):
        if(production == 0):
            return 0
        return total_consumption/production

    def calc_variation(self, realized, estimated):
        if(estimated == 0):
            return realized
        return 1 - (realized / estimated)


    def has_open_justification(self, monthly_plan_monitoring) -> bool:
        english_month_names = None
        start_month = datetime.now().month - 1
        with different_locale('C.UTF-8'):
            english_month_names = list(map(lambda s: s.lower(), month_name))
        
        for i in range(1, start_month + 1):
            plan_monitoring: PlanMonitoring = getattr(monthly_plan_monitoring, english_month_names[i])
            alert_fields = filter(lambda attr_name: attr_name.endswith("_alerts"), dir(plan_monitoring))
            for alert_field_name in alert_fields:
                if(any(value.endswith(":") for value in (getattr(plan_monitoring, alert_field_name) or []))):
                    return True
        return False