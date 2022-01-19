from django.db import models
from enumchoicefield import ChoiceEnum, EnumChoiceField
from .CompanyBudget import CompanyBudget
from .MonthlyBudget import MonthlyBudget


class CompanyBudgetRevisionState(ChoiceEnum):
    in_creation_by_analyst = "inCreationByAnalyst"
    budgeting = "budgeting"
    releasedto_analysis = "releasedToAnalysis"
    releasedto_operational_manager_approval = "releasedToOperationalManagerApproval"
    releasedto_energy_manager_approval = "releasedToEnergyManagerApproval"
    energy_manager_approved = "energyManagerApproved"
    disapproved = "disapproved"


class CompanyBudgetRevision(models.Model):
    id = models.BigAutoField(db_column='ID_COMPANY_BUDGET_REVISION', primary_key=True)
    company_budget = models.ForeignKey(
        CompanyBudget, models.DO_NOTHING, db_column='ID_COMPANY_BUDGET')
    revision = models.IntegerField(db_column='REVISION')
    state = EnumChoiceField(CompanyBudgetRevisionState, db_column='STATE')
    consumption_limit = models.FloatField(
        db_column='CONSUMPTION_LIMIT', blank=True, null=True)
    contract_usage_factor_peak = models.FloatField(
         db_column='CONTRACT_USAGE_FACTOR_PEAK', blank=True, null=True)
    contract_usage_factor_offpeak = models.FloatField(
         db_column='CONTRACT_USAGE_FACTOR_OFFPEAK', blank=True, null=True)
    firstyear_budget = models.ForeignKey(
        MonthlyBudget, models.DO_NOTHING, db_column='ID_CPNY_BUDGET_MON_FIRST_YEAR', related_name='firstYearBudget')
    secondyear_budget = models.ForeignKey(
        MonthlyBudget, models.DO_NOTHING, db_column='ID_CPNY_BUDGET_MON_SECOND_YEAR', related_name='secondYearBudget')
    thirdyear_budget = models.ForeignKey(
        MonthlyBudget, models.DO_NOTHING, db_column='ID_CPNY_BUDGET_MON_THIRD_YEAR', related_name='thirdYearBudget')
    fourthyear_budget = models.ForeignKey(
        MonthlyBudget, models.DO_NOTHING, db_column='ID_CPNY_BUDGET_MON_FOURTH_YEAR', related_name='fourthYearBudget')
    fifthyear_budget = models.ForeignKey(
        MonthlyBudget, models.DO_NOTHING, db_column='ID_CPNY_BUDGET_MON_FIFTH_YEAR', related_name='fifthYearBudget')

    can_change_contract_usage_factor = True

    class Meta:
        managed = False
        db_table = 'COMPANY_BUDGET_REVISION'
