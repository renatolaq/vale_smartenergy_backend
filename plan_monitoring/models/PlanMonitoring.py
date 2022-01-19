from django.db import models
from separatedvaluesfield.models import SeparatedValuesField


class PlanMonitoring(models.Model):
    id = models.BigAutoField(db_column='ID_COMPANY_PLAN_MONITORING_DAT', primary_key=True)
    contracted_peak_power_demand = models.FloatField(
        db_column='CONT_PEAK_PW_DEMAND', blank=True, null=True)
    contracted_offpeak_power_demand = models.FloatField(
        db_column='CONT_OFFPEAK_PW_DEMAND', blank=True, null=True)
    realized_peakpower_demand = models.FloatField(
        db_column='REA_PEAK_PW_DEMAND', blank=True, null=True)
    realized_peakpower_demand_readonly = False
    realized_offpeak_power_demand = models.FloatField(
        db_column='REA_OFFPEAK_PW_DEMAND', blank=True, null=True)
    realized_offpeak_power_demand_readonly = False
    estimated_peakpower_demand = models.FloatField(
        db_column='EST_PEAK_PW_DEMAND', blank=True, null=True)
    estimated_offpeak_power_demand = models.FloatField(
        db_column='EST_OFFPEAK_PW_DEMAND', blank=True, null=True)
    projected_peakpower_demand = models.FloatField(
        db_column='PRO_PEAK_PW_DEMAND', blank=True, null=True)
    projected_offpeak_power_demand = models.FloatField(
        db_column='PRO_OFFPEAK_PW_DEMAND', blank=True, null=True)

    projected_peak_power_consumption = models.FloatField(
        db_column='PRO_PEAK_PW_CONS', blank=True, null=True) 
    projected_offpeak_power_consumption = models.FloatField(
        db_column='PRO_OFFPEAK_PW_CONS', blank=True, null=True)
    realized_peak_power_consumption = models.FloatField(
        db_column='REA_PEAK_PW_CONS', blank=True, null=True)
    realized_peak_power_consumption_readonly = False
    realized_offpeak_power_consumption = models.FloatField(
        db_column='REA_OFFPEAK_PW_CONS', blank=True, null=True)
    realized_offpeak_power_consumption_readonly = False
    estimated_peak_power_consumption = models.FloatField(
        db_column='EST_PEAK_PW_CONS', blank=True, null=True)
    estimated_offpeak_power_consumption = models.FloatField(
        db_column='EST_OFFPEAK_PW_CONS', blank=True, null=True)

    estimated_production = models.FloatField(
        db_column='ESTIMATED_PRODUCTION', blank=True, null=True)
    realized_production = models.FloatField(
        db_column='REALIZED_PRODUCTION', blank=True, null=True)
    realized_production_readonly = False
    projected_production = models.FloatField(
        db_column='PROJECTED_PRODUCTION', blank=True, null=True)

    estimated_productive_stops = models.FloatField(
        db_column='EST_PRODUCTIVE_STOPS', blank=True, null=True)
    projected_productive_stops = models.FloatField(
        db_column='PRO_PRODUCTIVE_STOPS', blank=True, null=True)

    # calculated
    estimated_total_consumption = models.FloatField(
        db_column='EST_TOTAL_CONS', blank=True, null=True)
    realized_total_consumption = models.FloatField(
        db_column='REA_TOTAL_CONS', blank=True, null=True)
    realized_total_consumption_readonly = False
    projected_total_consumption = models.FloatField(
        db_column='PRO_TOTAL_CONS', blank=True, null=True)
    variation_consumption_estimated_realized = models.FloatField(
        db_column='VAR_CONS_EST_REA', blank=True, null=True)
    variation_consumption_estimated_projected = models.FloatField(
        db_column='VAR_CONS_EST_PRO', blank=True, null=True)
    realized_utilization_factor_consistency_offpeakpower = models.FloatField(
        db_column='REA_UT_FAC_CONS_OFFP_PW', blank=True, null=True)
    realized_utilization_factor_consistency_peakpower = models.FloatField(
        db_column='REA_UTIL_FAC_CONS_P_PW', blank=True, null=True)
    realized_load_factor_consistency_offpeakpower = models.FloatField(
        db_column='REA_LD_FAC_CONS_OFFP_PW', blank=True, null=True)
    realized_load_factor_consistency_peakpower = models.FloatField(
        db_column='REA_LD_FAC_CONS_PEAK_PW', blank=True, null=True)
    realized_uniqueload_factor_consistency = models.FloatField(
        db_column='REA_UNI_LD_FAC_CONS', blank=True, null=True)
    realized_modulation_factor_consistency = models.FloatField(
        db_column='REA_MODULATION_FAC_CONS', blank=True, null=True)
    estimated_specific_consumption = models.FloatField(
        db_column='EST_SPEC_CONS', blank=True, null=True)
    realized_specific_consumption = models.FloatField(
        db_column='REA_SPEC_CONS', blank=True, null=True)
    projected_specific_consumption = models.FloatField(
        db_column='PRO_SPEC_CONS', blank=True, null=True)
    variation_specific_consumption_estimated_realized = models.FloatField(
        db_column='VAR_SPEC_CONS_EST_REA', blank=True, null=True)
    variation_specific_consumption_estimated_projected = models.FloatField(
        db_column='VAR_SPEC_CONS_EST_PRO', blank=True, null=True)
    
    realized_total_consumption_alerts = SeparatedValuesField(
        db_column='REA_TOTAL_CONS_ALERTS', max_length=400, blank=True, null=True, token="|")
    realized_specific_consumption_alerts = SeparatedValuesField(
        db_column='REA_SPEC_CONS_ALERTS', max_length=400, blank=True, null=True, token="|")
    realized_utilization_factor_consistency_offpeakpower_alerts = SeparatedValuesField(
        db_column='REA_UT_FAC_CONS_OFFP_PW_ALERTS', max_length=400, blank=True, null=True, token="|")
    realized_utilization_factor_consistency_peakpower_alerts = SeparatedValuesField(
        db_column='REA_UTIL_FAC_CONS_P_PW_ALERTS', max_length=400, blank=True, null=True, token="|")

    class Meta:
        managed = False
        db_table = 'COMPANY_PLAN_MONITORING_DATA'
