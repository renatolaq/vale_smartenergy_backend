from django.db import models
from .PlanMonitoring import PlanMonitoring

class MonthlyPlanMonitoring(models.Model):
    id = models.BigAutoField(db_column='ID_COMPANY_PLAN_MON_MONTHLY', primary_key=True)
    january = models.ForeignKey(PlanMonitoring, models.DO_NOTHING, db_column='ID_COMPANY_PLAN_MON_DATA_JAN', related_name='january')
    february = models.ForeignKey(PlanMonitoring, models.DO_NOTHING, db_column='ID_COMPANY_PLAN_MON_DATA_FEB', related_name='february')
    march = models.ForeignKey(PlanMonitoring, models.DO_NOTHING, db_column='ID_COMPANY_PLAN_MON_DATA_MAR', related_name='march')
    april = models.ForeignKey(PlanMonitoring, models.DO_NOTHING, db_column='ID_COMPANY_PLAN_MON_DATA_APR', related_name='april')
    may = models.ForeignKey(PlanMonitoring, models.DO_NOTHING, db_column='ID_COMPANY_PLAN_MON_DATA_MAY', related_name='may')
    june = models.ForeignKey(PlanMonitoring, models.DO_NOTHING, db_column='ID_COMPANY_PLAN_MON_DATA_JUN', related_name='june')
    july = models.ForeignKey(PlanMonitoring, models.DO_NOTHING, db_column='ID_COMPANY_PLAN_MON_DATA_JUL', related_name='july')
    august = models.ForeignKey(PlanMonitoring, models.DO_NOTHING, db_column='ID_COMPANY_PLAN_MON_DATA_AUG', related_name='august')
    september = models.ForeignKey(PlanMonitoring, models.DO_NOTHING, db_column='ID_COMPANY_PLAN_MON_DATA_SEP', related_name='september')
    october = models.ForeignKey(PlanMonitoring, models.DO_NOTHING, db_column='ID_COMPANY_PLAN_MON_DATA_OCT', related_name='october')
    november = models.ForeignKey(PlanMonitoring, models.DO_NOTHING, db_column='ID_COMPANY_PLAN_MON_DATA_NOV', related_name='november')
    december = models.ForeignKey(PlanMonitoring, models.DO_NOTHING, db_column='ID_COMPANY_PLAN_MON_DATA_DEC', related_name='december')

    class Meta:
        managed = False
        db_table = 'COMPANY_PLAN_MONITORING_MONTHLY'