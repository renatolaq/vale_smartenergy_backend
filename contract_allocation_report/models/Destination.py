from django.db import models

from .Source import Source
from cliq_contract.models import CliqContract
from company.models import Company

class Destination(models.Model):
    id = models.BigAutoField(db_column='ID_CONTR_ALLOC_REP_DESTINATION', primary_key=True)  # Field name made lowercase.
    source = models.ForeignKey(Source, models.CASCADE, db_column='ID_CONTR_ALLOC_REP_SOURCE')  # Field name made lowercase.
    unit = models.ForeignKey(Company, models.DO_NOTHING, db_column='ID_COMPANY')  # Field name made lowercase.
    allocated_power = models.FloatField(db_column='ALLOCATED_POWER')
    icms_cost = models.FloatField(db_column='ICMS_COST')
    icms_cost_not_creditable = models.FloatField(db_column='ICMS_COST_NOT_CREDITABLE')

    class Meta:
        managed = False
        db_table = 'CONTR_ALLOC_REP_DESTINATION'