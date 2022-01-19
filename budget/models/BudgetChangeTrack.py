from django.db import models
from .CompanyBudget import CompanyBudget
from .CompanyBudgetRevision import CompanyBudgetRevisionState
from enumchoicefield import ChoiceEnum, EnumChoiceField

class BudgetChangeTrack(models.Model):
    id = models.BigAutoField(db_column='ID_COMPANY_BUDGET_CHANGE_TRACK', primary_key=True)
    company_budget = models.ForeignKey(CompanyBudget, models.DO_NOTHING, db_column='ID_COMPANY_BUDGET', blank=True, null=True)  # Field name made lowercase.
    budget_revision = models.SmallIntegerField(db_column='BUDGET_REVISION', blank=True, null=True)  # Field name made lowercase.
    comment = models.CharField(db_column='COMMENT', max_length=4000, blank=True, null=True)
    user = models.CharField(db_column='USER', max_length=50, blank=True, null=True)
    change_at = models.DateTimeField(db_column='CHANGE_AT', blank=True, null=True)  # Field name made lowercase.
    state = EnumChoiceField(CompanyBudgetRevisionState, db_column='STATE')

    class Meta:
        managed = False
        db_table = 'COMPANY_BUDGET_CHANGE_TRACK'