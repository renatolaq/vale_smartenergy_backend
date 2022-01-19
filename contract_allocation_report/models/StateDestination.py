from django.db import models

from company.models import State as CompanyState
from .Source import Source

class StateDestination(models.Model):
    id = models.BigAutoField(db_column='ID_CONTR_ALLOC_REP_ST_ALLOCATION', primary_key=True)  # Field name made lowercase.
    source = models.ForeignKey(Source, models.CASCADE, db_column='ID_CONTR_ALLOC_REP_SOURCE')  # Field name made lowercase.
    state = models.ForeignKey(CompanyState, models.DO_NOTHING, db_column='ID_STATE')  # Field name made lowercase.
    allocated_power = models.FloatField(db_column='ALLOCATED_POWER')

    class Meta:
        managed = False
        db_table = 'CONTR_ALLOC_REP_ST_DESTINATION'