from django.db import models
from separatedvaluesfield.models import SeparatedValuesField as _SeparatedValuesField

class SeparatedValuesField(_SeparatedValuesField):
    def _get_val_from_obj(self, obj):
        return getattr(obj, self.attname, None)

class Budget(models.Model):
    id = models.BigAutoField(db_column='ID_COMPANY_BUDGET_DATA', primary_key=True)
    contracted_peak_power_demand = models.FloatField(
        db_column='CONT_PEAK_PW_DEMAND', blank=True, null=True)
    contracted_offpeak_power_demand = models.FloatField(
        db_column='CONT_OFFPEAK_PW_DEMAND', blank=True, null=True)
    estimated_peak_power_demand = models.FloatField(
        db_column='EST_PEAK_PW_DEMAND', blank=True, null=True)
    estimated_offpeak_power_demand = models.FloatField(
        db_column='EST_OFFPEAK_PW_DEMAND', blank=True, null=True)
    consumption_peak_power_demand = models.FloatField(
        db_column='CONS_PEAK_PW_DEMAND', blank=True, null=True)
    consumption_offpeak_power_demand = models.FloatField(
        db_column='CONS_OFFPEAK_PW_DEMAND', blank=True, null=True)
    production = models.FloatField(db_column='PRODUCTION',blank=True, null=True)
    production_readonly = models.BooleanField(db_column='PRODUCTION_READONLY',blank=True, null=True)
    productive_stops = models.FloatField(
        db_column='PRODUCTIVE_STOPS', blank=True, null=True)
    total_consumption = models.FloatField(
        db_column='TOTAL_CONSUMPTION', blank=True, null=True)
    utilization_factor_consistency_offpeakpower = models.FloatField(
        db_column='UTIL_FAC_CONS_OFPEAK_PW', blank=True, null=True)
    utilization_factor_consistency_peakpower = models.FloatField(
        db_column='UTIL_FAC_CONS_PEAK_PW', blank=True, null=True)
    loadfactor_consistency_offpeakpower = models.FloatField(
        db_column='LOAD_FAC_CONS_OFPEAK_PW', blank=True, null=True)
    loadfactor_consistency_peakpower = models.FloatField(
        db_column='LOAD_FAC_CONS_PEAK_PW', blank=True, null=True)
    uniqueload_factor_consistency = models.FloatField(
        db_column='UNIQUE_LOAD_FAC_CONS', blank=True, null=True)
    modulation_factor_consistency = models.FloatField(
        db_column='MODULATION_FAC_CONS', blank=True, null=True)
    specific_consumption = models.FloatField(
        db_column='SPECIFIC_CONSUMPTION', blank=True, null=True)

    consumption_peak_power_demand_alerts = SeparatedValuesField(
        max_length=400, db_column='CONS_PEAK_PW_DEMAND_ALERTS', blank=True, null=True, token="|")
    consumption_offpeak_power_demand_alerts = SeparatedValuesField(
        max_length=400, db_column='CONS_OFFPEAK_PW_DEMAND_ALERTS', blank=True, null=True, token="|")
    utilization_factor_consistency_offpeakpower_alerts = SeparatedValuesField(
        max_length=400, db_column='UTIL_FAC_CONS_OFPEAK_PW_ALERTS', blank=True, null=True, token="|")
    utilization_factor_consistency_peakpower_alerts = SeparatedValuesField(
        max_length=400, db_column='UTIL_FAC_CONS_PEAK_PW_ALERTS', blank=True, null=True, token="|")
    loadfactor_consistency_offpeakpower_alerts = SeparatedValuesField(
        max_length=400, db_column='LOAD_FAC_CONS_OFPEAK_PW_ALERTS', blank=True, null=True, token="|")
    loadfactor_consistency_peakpower_alerts = SeparatedValuesField(
        max_length=400, db_column='LOAD_FAC_CONS_PEAK_PW_ALERTS', blank=True, null=True, token="|")
    uniqueload_factor_consistency_alerts = SeparatedValuesField(
        max_length=400, db_column='UNIQUE_LOAD_FAC_CONS_ALERTS', blank=True, null=True, token="|")
    modulation_factor_consistency_alerts = SeparatedValuesField(
        max_length=400, db_column='MODULATION_FAC_CONS_ALERTS', blank=True, null=True, token="|")

    

    class Meta:
        managed = False
        db_table = 'COMPANY_BUDGET_DATA'
