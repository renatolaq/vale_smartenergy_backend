from decimal import Decimal

from calendar import monthrange, isleap

from ..models.Budget import Budget
from .IntegrationService import IntegrationService


class BudgetCalculateService:
    def __init__(self, integration_service: IntegrationService):
        self.__integration_service = integration_service

    def distribute_amoung_months(self, year_data: dict, year) -> dict:
        distribuition_factors = self.__get_distribution_factors(year)

        return {
            "january": self.__yearly_to_monthly(year_data, distribuition_factors['january']),
            "february": self.__yearly_to_monthly(year_data, distribuition_factors['february']),
            "march": self.__yearly_to_monthly(year_data, distribuition_factors['march']),
            "april": self.__yearly_to_monthly(year_data, distribuition_factors['april']),
            "may": self.__yearly_to_monthly(year_data, distribuition_factors['may']),
            "june": self.__yearly_to_monthly(year_data, distribuition_factors['june']),
            "july": self.__yearly_to_monthly(year_data, distribuition_factors['july']),
            "august": self.__yearly_to_monthly(year_data, distribuition_factors['august']),
            "september": self.__yearly_to_monthly(year_data, distribuition_factors['september']),
            "october": self.__yearly_to_monthly(year_data, distribuition_factors['october']),
            "november": self.__yearly_to_monthly(year_data, distribuition_factors['november']),
            "december": self.__yearly_to_monthly(year_data, distribuition_factors['december']),
        }

    def __get_distribution_factors(self, year):
        days_of_year = 366 if isleap(year) else 365
        return {
            "january": monthrange(year, 1)[1]/days_of_year,
            "february": monthrange(year, 2)[1]/days_of_year,
            "march": monthrange(year, 3)[1]/days_of_year,
            "april": monthrange(year, 4)[1]/days_of_year,
            "may": monthrange(year, 5)[1]/days_of_year,
            "june": monthrange(year, 6)[1]/days_of_year,
            "july": monthrange(year, 7)[1]/days_of_year,
            "august": monthrange(year, 8)[1]/days_of_year,
            "september": monthrange(year, 9)[1]/days_of_year,
            "october": monthrange(year, 10)[1]/days_of_year,
            "november": monthrange(year, 11)[1]/days_of_year,
            "december": monthrange(year, 12)[1]/days_of_year
        }

    def __yearly_to_monthly(self, budget_data, factor):
        def calc(field): return budget_data.get(field) * factor \
            if budget_data.get(field) is not None else None
        return {
            "contracted_peak_power_demand": budget_data.get("contracted_peak_power_demand"),
            "contracted_offpeak_power_demand": budget_data.get("contracted_offpeak_power_demand"),
            "estimated_peak_power_demand": budget_data.get("estimated_peak_power_demand"),
            "estimated_offpeak_power_demand": budget_data.get("estimated_offpeak_power_demand"),
            "consumption_peak_power_demand": calc("consumption_peak_power_demand"),
            "consumption_offpeak_power_demand": calc("consumption_offpeak_power_demand"),
            "total_consumption": calc("total_consumption"),
            "production": calc("production"),
            "productive_stops": calc("productive_stops")
        }

    def calc_budget_update_object(self, budget: Budget, budget_data: dict,
                                  consumption_limit: float, peak_hour_month, offpeak_hour_month):
        def calc_if_valued(func, *args):
            if(all(value is not None for value in args)):
                return func(*args)
            return None

        budget.total_consumption = calc_if_valued(
            self.calc_total_consumption,
            budget_data.get("consumption_peak_power_demand"),
            budget_data.get("consumption_offpeak_power_demand"))

        budget.utilization_factor_consistency_peakpower = calc_if_valued(
            self.calc_utilization_factor_consistency_peakpower,
            budget_data.get("estimated_peak_power_demand"),
            budget_data.get("contracted_peak_power_demand"))

        budget.utilization_factor_consistency_offpeakpower = calc_if_valued(
            self.calc_utilization_factor_consistency_offpeakpower,
            budget_data.get("estimated_offpeak_power_demand"),
            budget_data.get("contracted_offpeak_power_demand"))

        budget.loadfactor_consistency_peakpower = calc_if_valued(
            self.calc_loadfactor_consistency_peakpower,
            budget_data.get("consumption_peak_power_demand"),
            peak_hour_month,
            budget_data.get("estimated_peak_power_demand"))

        budget.loadfactor_consistency_offpeakpower = calc_if_valued(
            self.calc_loadfactor_consistency_offpeakpower,
            budget_data.get("consumption_offpeak_power_demand"),
            offpeak_hour_month, budget_data.get("estimated_offpeak_power_demand"))

        budget.uniqueload_factor_consistency = calc_if_valued(
            self.calc_uniqueload_factor_consistency,
            budget.total_consumption,
            peak_hour_month, offpeak_hour_month,
            budget_data.get("estimated_peak_power_demand"),
            budget_data.get("estimated_offpeak_power_demand"))

        budget.modulation_factor_consistency = calc_if_valued(
            self.calc_modulation_factor_consistency,
            budget_data.get("estimated_peak_power_demand"),
            budget_data.get("estimated_offpeak_power_demand"))

        budget.specific_consumption = calc_if_valued(
            self.calc_specific_consumption,
            budget.total_consumption,
            budget_data.get("production"))

        alerts = self.generate_budget_alerts(
            {**(budget.__dict__), **(budget_data)}, consumption_limit)

        for item in alerts.items():
            setattr(budget, item[0], item[1])

    def calc_budget(self, budget_data, consumption_limit, peak_hour, offpeak_hour):
        budget = type('', (), {})()
        self.calc_budget_update_object(
            budget, budget_data, consumption_limit, peak_hour, offpeak_hour)
        budget_data.update(budget.__dict__)

    def unflat_budget_data(self, budget_data, peak_hours, offpeak_hours):
        if (budget_data["total_consumption"]):
            budget_data["consumption_peak_power_demand"] = (
                peak_hours / (peak_hours + offpeak_hours)) * budget_data["total_consumption"]
            budget_data["consumption_offpeak_power_demand"] = (
                offpeak_hours / (peak_hours + offpeak_hours)) * budget_data["total_consumption"]
        else:
            budget_data["consumption_peak_power_demand"] = None
            budget_data["consumption_offpeak_power_demand"] = None

    def unflat_monthly_budget_data(self, budget_data, peak_hour_month_data, offpeak_hour_month_data):
        self.unflat_budget_data(
            budget_data["january"], peak_hour_month_data["january"], offpeak_hour_month_data["january"])
        self.unflat_budget_data(
            budget_data["february"], peak_hour_month_data["february"], offpeak_hour_month_data["february"])
        self.unflat_budget_data(
            budget_data["march"], peak_hour_month_data["march"], offpeak_hour_month_data["march"])
        self.unflat_budget_data(
            budget_data["april"], peak_hour_month_data["april"], offpeak_hour_month_data["april"])
        self.unflat_budget_data(
            budget_data["may"], peak_hour_month_data["may"], offpeak_hour_month_data["may"])
        self.unflat_budget_data(
            budget_data["june"], peak_hour_month_data["june"], offpeak_hour_month_data["june"])
        self.unflat_budget_data(
            budget_data["july"], peak_hour_month_data["july"], offpeak_hour_month_data["july"])
        self.unflat_budget_data(
            budget_data["august"], peak_hour_month_data["august"], offpeak_hour_month_data["august"])
        self.unflat_budget_data(
            budget_data["september"], peak_hour_month_data["september"], offpeak_hour_month_data["september"])
        self.unflat_budget_data(
            budget_data["october"], peak_hour_month_data["october"], offpeak_hour_month_data["october"])
        self.unflat_budget_data(
            budget_data["november"], peak_hour_month_data["november"], offpeak_hour_month_data["november"])
        self.unflat_budget_data(
            budget_data["december"], peak_hour_month_data["december"], offpeak_hour_month_data["december"])

    def calc_monthly_budget(self, monthly_budget, consumption_limit: float, contract_usage_factor_offpeak: float, contract_usage_factor_peak: float, company: int, year: int):
        peak_hour_month_data, offpeak_hour_month_data = self.__integration_service.get_hour_month(
            year)
        contracted_peak_power_demand = self.__integration_service.get_contracted_peak_power_demand(
            company, year, contract_usage_factor_peak)
        contracted_offpeak_power_demand = self.__integration_service.get_contracted_offpeak_power_demand(
            company, year, contract_usage_factor_offpeak)
        production = self.__integration_service.get_production(company, year)

        def calc_month(month):
            budget_data = monthly_budget[month]
            budget = type('', (), {})()

            budget_data["contracted_peak_power_demand"] = contracted_peak_power_demand.get(
                month) if contracted_peak_power_demand.get(month) is not None else budget_data["contracted_peak_power_demand"]
            budget_data["contracted_offpeak_power_demand"] = contracted_offpeak_power_demand.get(
                month) if contracted_offpeak_power_demand.get(month) is not None else budget_data["contracted_offpeak_power_demand"]
            budget_data["production"] = production.get(month) if production.get(
                month) is not None else budget_data["production"]
            budget_data["production_readonly"] = production.get(month) is not None

            self.calc_budget_update_object(
                budget, budget_data, consumption_limit, peak_hour_month_data[month], offpeak_hour_month_data[month])
            budget_data.update(budget.__dict__)

        calc_month("january")
        calc_month("february")
        calc_month("march")
        calc_month("april")
        calc_month("may")
        calc_month("june")
        calc_month("july")
        calc_month("august")
        calc_month("september")
        calc_month("october")
        calc_month("november")
        calc_month("december")

    def calc_total_consumption(self, consumption_peak_power_demand: float,
                               consumption_offpeak_power_demand: float):
        return consumption_peak_power_demand + consumption_offpeak_power_demand

    def calc_utilization_factor_consistency_peakpower(self,
                                                      estimated_peak_power_demand: float,
                                                      contracted_peak_power_demand: float):  #sempre preenchido
        if(not contracted_peak_power_demand):
            return None
        return estimated_peak_power_demand / contracted_peak_power_demand

    def calc_utilization_factor_consistency_offpeakpower(self,
                                                         estimated_offpeak_power_demand: float,
                                                         contracted_offpeak_power_demand: float): #sempre preenchido
        if(not contracted_offpeak_power_demand):
            return None
        return estimated_offpeak_power_demand / contracted_offpeak_power_demand

    def calc_loadfactor_consistency_peakpower(self,
                                              consumption_peak_power_demand, peak_hour_month: float,
                                              estimated_peak_power_demand: float): #Pode passar vazio
        if(not peak_hour_month or not estimated_peak_power_demand):
            return None
        return (consumption_peak_power_demand / peak_hour_month) / estimated_peak_power_demand

    def calc_loadfactor_consistency_offpeakpower(self,
                                                 consumption_offpeak_power_demand: float,
                                                 offpeak_hour_month, estimated_offpeak_power_demand: float):
        if(not offpeak_hour_month or not estimated_offpeak_power_demand):  #Pode passar vazio
            return None
        return (consumption_offpeak_power_demand / offpeak_hour_month) / estimated_offpeak_power_demand

    def calc_uniqueload_factor_consistency(self, total_consumption: float,
                                           peak_hour_month, offpeak_hour_month: float,
                                           estimated_peak_power_demand, estimated_offpeak_power_demand: float): 
        if(not (peak_hour_month+offpeak_hour_month) or not max(estimated_peak_power_demand, estimated_offpeak_power_demand)):  #Pode passar vazio
            return None
        return (total_consumption/(peak_hour_month+offpeak_hour_month)) / \
            max(estimated_peak_power_demand, estimated_offpeak_power_demand)

    def calc_modulation_factor_consistency(self, estimated_peak_power_demand: float,
                                           estimated_offpeak_power_demand: float):  #Pode passar vazio
        if(not estimated_offpeak_power_demand):
            return None
        return 1 - (estimated_peak_power_demand / estimated_offpeak_power_demand)

    def calc_specific_consumption(self, total_consumption: float, production: float):
        if(not production):  #Pode passar vazio
            return None
        return total_consumption / production

    def generate_budget_alerts(self, budget: dict, consumption_limit: float) -> dict:
        ret = {}

        def out_of_range(field):
            if(budget.get(field) != None):
                if(1 < budget[field] or budget[field] < 0):
                    ret[field + "_alerts"] = ["FACTOR_OUT_OF_RANGE"] + \
                        (ret.get(field + "_alerts") or [])

        def variation_greater_than_90_per(field):
            if(budget.get(field) != None):
                if(budget[field] > 0.9):
                    ret[field + "_alerts"] = ["FACTOR_VARIATION_GREATER_THAN_90_PER"] + \
                        (ret.get(field + "_alerts") or [])

        def consumption_differs_from_previous_years(field):
            if(budget.get(field) != None and consumption_limit != None):
                if(budget[field] > consumption_limit):  # TODO
                    ret[field + "_alerts"] = ["CONSUMPTION_DIFFERS_FROM_PREVIOUS_YEARS"] + \
                        (ret.get(field + "_alerts") or [])

        #ret["contracted_peak_power_demand_alerts"] = None
        #ret["contracted_offpeak_power_demand_alerts"] = None
        #ret["estimated_peak_power_demand_alerts"] = None
        #ret["estimated_offpeak_power_demand_alerts"] = None
        ret["consumption_peak_power_demand_alerts"] = None
        ret["consumption_offpeak_power_demand_alerts"] = None
        #ret["production_alerts"] = None
        #ret["productive_stops_alerts"] = None
        #ret["total_consumption_alerts"] = None
        ret["utilization_factor_consistency_offpeakpower_alerts"] = None
        ret["utilization_factor_consistency_peakpower_alerts"] = None
        ret["loadfactor_consistency_offpeakpower_alerts"] = None
        ret["loadfactor_consistency_peakpower_alerts"] = None
        ret["uniqueload_factor_consistency_alerts"] = None
        ret["modulation_factor_consistency_alerts"] = None
        #ret["specific_consumption_alerts"] = None
        out_of_range("utilization_factor_consistency_peakpower")
        out_of_range("utilization_factor_consistency_offpeakpower")
        out_of_range("loadfactor_consistency_peakpower")
        out_of_range("loadfactor_consistency_offpeakpower")
        out_of_range("uniqueload_factor_consistency")
        out_of_range("modulation_factor_consistency")

        variation_greater_than_90_per(
            "utilization_factor_consistency_peakpower")
        variation_greater_than_90_per(
            "utilization_factor_consistency_offpeakpower")
        variation_greater_than_90_per("loadfactor_consistency_peakpower")
        variation_greater_than_90_per("loadfactor_consistency_offpeakpower")
        variation_greater_than_90_per("uniqueload_factor_consistency")
        variation_greater_than_90_per("modulation_factor_consistency")

        # TODO
        # consumption_differs_from_previous_years("consumption_peak_power_demand")
        # consumption_differs_from_previous_years("consumption_offpeak_power_demand")
        # consumption_differs_from_previous_years("specific_consumption")

        return ret
