from django.db import models

from .EnergyContractPrioritization import EnergyContractPrioritization

class Revision(models.Model):
    id = models.BigAutoField(db_column='ID_ENERGY_CONT_PRIOR_REVISION', primary_key=True)  # Field name made lowercase.
    energy_contract_prioritization = models.ForeignKey(EnergyContractPrioritization, models.DO_NOTHING, db_column='ID_ENERGY_CONT_PRIOR')  # Field name made lowercase.
    revision = models.IntegerField(db_column='REVISION')  # Field name made lowercase.
    change_justification = models.CharField(db_column='CHANGE_JUSTIFICATION', max_length=400)  # Field name made lowercase.
    change_at = models.DateTimeField(db_column='CHANGE_AT')  # Field name made lowercase.
    user = models.CharField(db_column='USER', max_length=50)  # Field name made lowercase.
    active = models.BooleanField(db_column='ACTIVE')  # Field name made lowercase.
    order = models.IntegerField(db_column='ORDER')  # Field name made lowercase.
    contracts_edited = models.BooleanField(db_column='CONTRACTS_EDITED')
    generators_edited = models.BooleanField(db_column='GENERATORS_EDITED')
    consumers_edited = models.BooleanField(db_column='CONSUMERS_EDITED')
    parameters_edited = models.BooleanField(db_column='PARAMETERS_EDITED')

    class Meta:
        managed = False
        db_table = 'ENERGY_CONT_PRIOR_REVISION'