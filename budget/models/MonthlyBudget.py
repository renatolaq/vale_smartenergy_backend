from django.db import models
from .Budget import Budget

class MonthlyBudget(models.Model):
    id = models.BigAutoField(db_column='ID_COMPANY_BUDGET_MONTHLY', primary_key=True)
    january = models.ForeignKey(Budget, models.DO_NOTHING, db_column='ID_COMPANY_BUDGET_DATA_JAN', related_name='january')
    february = models.ForeignKey(Budget, models.DO_NOTHING, db_column='ID_COMPANY_BUDGET_DATA_FEB', related_name='february')
    march = models.ForeignKey(Budget, models.DO_NOTHING, db_column='ID_COMPANY_BUDGET_DATA_MAR', related_name='march')
    april = models.ForeignKey(Budget, models.DO_NOTHING, db_column='ID_COMPANY_BUDGET_DATA_APR', related_name='april')
    may = models.ForeignKey(Budget, models.DO_NOTHING, db_column='ID_COMPANY_BUDGET_DATA_MAY', related_name='may')
    june = models.ForeignKey(Budget, models.DO_NOTHING, db_column='ID_COMPANY_BUDGET_DATA_JUN', related_name='june')
    july = models.ForeignKey(Budget, models.DO_NOTHING, db_column='ID_COMPANY_BUDGET_DATA_JUL', related_name='july')
    august = models.ForeignKey(Budget, models.DO_NOTHING, db_column='ID_COMPANY_BUDGET_DATA_AUG', related_name='august')
    september = models.ForeignKey(Budget, models.DO_NOTHING, db_column='ID_COMPANY_BUDGET_DATA_SEP', related_name='september')
    october = models.ForeignKey(Budget, models.DO_NOTHING, db_column='ID_COMPANY_BUDGET_DATA_OCT', related_name='october')
    november = models.ForeignKey(Budget, models.DO_NOTHING, db_column='ID_COMPANY_BUDGET_DATA_NOV', related_name='november')
    december = models.ForeignKey(Budget, models.DO_NOTHING, db_column='ID_COMPANY_BUDGET_DATA_DEC', related_name='december')

    class Meta:
        managed = False
        db_table = 'COMPANY_BUDGET_MONTHLY'