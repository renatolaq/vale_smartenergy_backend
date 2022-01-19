from django.db import models

from .Revision import Revision

class Generator(models.Model):
    id = models.BigAutoField(db_column='ID_ENERGY_CONT_PRIOR_GENERATOR', primary_key=True)  # Field name made lowercase.
    revision = models.ForeignKey(Revision, models.DO_NOTHING, db_column='ID_ENERGY_CONT_PRIOR_REVISION')  # Field name made lowercase.
    company_generator = models.BigIntegerField(db_column='ID_COMPANY_GENERATOR')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'ENERGY_CONT_PRIOR_GENERATOR'