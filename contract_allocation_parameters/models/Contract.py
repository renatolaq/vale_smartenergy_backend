from django.db import models

from .Revision import Revision

class Contract(models.Model):
    id = models.BigAutoField(db_column='ID_ENERGY_CONT_PRIOR_CONTRACT', primary_key=True)  # Field name made lowercase.
    revision = models.ForeignKey(Revision, models.DO_NOTHING, db_column='ID_ENERGY_CONT_PRIOR_REVISION')  # Field name made lowercase.
    company_provider = models.BigIntegerField(db_column='ID_COMPANY_PROVIDER', blank=True, null=True)  # Field name made lowercase.
    contract_cliq_provider = models.BigIntegerField(db_column='ID_CLIQ_CONTRACT_PROVIDER', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'ENERGY_CONT_PRIOR_CONTRACT'