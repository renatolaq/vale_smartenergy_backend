from django.db import models
from .CompanyPlanMonitoring import CompanyPlanMonitoring
from .MonthlyPlanMonitoring import MonthlyPlanMonitoring

class CompanyPlanMonitoringRevision(models.Model):
    id = models.BigAutoField(db_column='ID_COMPANY_PLAN_MONITORING_REV', primary_key=True)
    company_plan_monitoring = models.ForeignKey(CompanyPlanMonitoring, models.DO_NOTHING, db_column='ID_COMPANY_PLAN_MONITORING')
    revision = models.IntegerField(db_column='REVISION')
    contract_usage_factor_peak = models.FloatField(
         db_column='CONTRACT_USAGE_FACTOR_PEAK', blank=True, null=True)
    contract_usage_factor_offpeak = models.FloatField(
         db_column='CONTRACT_USAGE_FACTOR_OFFPEAK', blank=True, null=True)
    firstyear_plan_monitoring = models.ForeignKey(MonthlyPlanMonitoring, models.DO_NOTHING, db_column='ID_PLAN_MONITORING_FIRST_YEAR', related_name='firstYearPlanMonitoring')
    secondyear_plan_monitoring = models.ForeignKey(MonthlyPlanMonitoring, models.DO_NOTHING, db_column='ID_PLAN_MONITORING_SECOND_YEAR', related_name='secondYearPlanMonitoring')

    class Meta:
        managed = False
        db_table = 'COMPANY_PLAN_MONITORING_REVISION'