from django.db import models
from enumchoicefield import EnumChoiceField, ChoiceEnum

class CompanyPlanMonitoringCalculationMode(ChoiceEnum):
    modular = "Modular"
    flat = "Flat"

class CompanyPlanMonitoring(models.Model):
    id = models.BigAutoField(primary_key=True, db_column='ID_COMPANY_PLAN_MONITORING')
    year = models.SmallIntegerField(db_column='YEAR')
    company_id = models.BigIntegerField(db_column='ID_COMPANY')
    has_open_justification = models.BooleanField(db_column="HAS_OPEN_JUSTIFICATION")
    calculation_mode = EnumChoiceField(CompanyPlanMonitoringCalculationMode, db_column='CALCULATION_MODE')

    class Meta:
        managed = False
        db_table = 'COMPANY_PLAN_MONITORING'