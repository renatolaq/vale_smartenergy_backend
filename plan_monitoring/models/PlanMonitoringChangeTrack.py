from django.db import models
from .CompanyPlanMonitoring import CompanyPlanMonitoring
from enumchoicefield import ChoiceEnum, EnumChoiceField

class CompanyPlanMonitoringChangeAction(ChoiceEnum):
    change = "change"
    justification = "justification"

class PlanMonitoringChangeTrack(models.Model):
    id = models.BigAutoField(primary_key=True, db_column='ID_PLAN_MON_CHANGE_TRACK')
    company_plan_monitoring = models.ForeignKey(CompanyPlanMonitoring, models.DO_NOTHING, db_column='ID_COMPANY_PLAN_MONITORING', blank=True, null=True)
    plan_monitoring_revision = models.SmallIntegerField(db_column='PLANMONITORINGREVISION', blank=True, null=True)
    comment = models.CharField(db_column='COMMENT', max_length=400, blank=True, null=True)
    user = models.CharField(db_column='USER', max_length=50, blank=True, null=True)
    change_at = models.DateTimeField(db_column='CHANGE_AT', blank=True, null=True)
    action = EnumChoiceField(CompanyPlanMonitoringChangeAction, db_column='ACTION', max_length=20, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'COMPANY_PLAN_MONITORING_CHANGE_TRACK'