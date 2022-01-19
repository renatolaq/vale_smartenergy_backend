from django.db import models
from enumchoicefield import ChoiceEnum, EnumChoiceField


class CompanyBudgetCalculationMode(ChoiceEnum):
    modular = "Modular"
    flat = "Flat"



class CompanyBudget(models.Model):
    id = models.BigAutoField(db_column='ID_COMPANY_BUDGET', primary_key=True)
    year = models.SmallIntegerField(db_column='YEAR')
    company_id = models.BigIntegerField(db_column='ID_COMPANY')
    calculation_mode = EnumChoiceField(CompanyBudgetCalculationMode, db_column='CALCULATION_MODE')

    class Meta:
        managed = False
        db_table = 'COMPANY_BUDGET'
