from django.db import models

from .Revision import Revision

class Consumer(models.Model):
    id = models.BigAutoField(db_column='ID_ENERGY_CONT_PRIOR_CONSUMER', primary_key=True)  # Field name made lowercase.
    revision = models.ForeignKey(Revision, models.DO_NOTHING, db_column='ID_ENERGY_CONT_PRIOR_REVISION')  # Field name made lowercase.
    state_consumer = models.BigIntegerField(db_column='ID_STATE_CONSUMER', blank=True, null=True)  # Field name made lowercase.
    company_consumer = models.BigIntegerField(db_column='ID_COMPANY_CONSUMER', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'ENERGY_CONT_PRIOR_CONSUMER'