from django.db import models
from enumchoicefield import ChoiceEnum, EnumChoiceField


class EnergyContractPrioritizationType(ChoiceEnum):
    icms = "ICMS"
    allocation_order = "AllocationOrder"

class EnergyContractPrioritizationSubtype(ChoiceEnum):
    icms_cost = "ICMSCost"
    icms_calculation_basis = "ICMSCalculationBasis"
    icms_creditable = "ICMSCreditable"
    compulsory = "Compulsory"
    preferred = "Preferred"
    prohibited = "Prohibited"
    excluded = "Excluded"

class EnergyContractPrioritization(models.Model):
    id = models.BigAutoField(db_column='ID_ENERGY_CONT_PRIOR', primary_key=True)  # Field name made lowercase.
    name = models.CharField(db_column='NAME', max_length=400)  # Field name made lowercase.
    type = EnumChoiceField(EnergyContractPrioritizationType, db_column='TYPE', max_length=50)  # Field name made lowercase.
    subtype = EnumChoiceField(EnergyContractPrioritizationSubtype, db_column='SUBTYPE', max_length=50)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'ENERGY_CONT_PRIOR'