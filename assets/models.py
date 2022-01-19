from django.db import models
from company.models import Company
from profiles.models import Profile
from energy_composition.models import EnergyComposition
from core.models import Seasonality, CceeDescription 



class Assets(models.Model):
    id_assets = models.AutoField(db_column='ID_ASSETS', primary_key=True)  # Field name made lowercase.
    id_submarket = models.ForeignKey('Submarket', models.DO_NOTHING, db_column='ID_SUBMARKET')  # Field name made lowercase.
    id_company = models.ForeignKey(Company, models.DO_NOTHING, db_column='ID_COMPANY', related_name='assets_company')  # Field name made lowercase.
    id_profile = models.ForeignKey(Profile, models.DO_NOTHING, db_column='ID_PROFILE', related_name='assets_profile')  # Field name made lowercase.
    id_ccee_proinfa = models.ForeignKey(CceeDescription, models.DO_NOTHING, db_column='ID_CCEE_PROINFA', blank=True, null=True)  # Field name made lowercase.
    id_ccee_siga = models.OneToOneField(CceeDescription, models.DO_NOTHING, db_column='ID_CCEE_SIGA', unique=True, related_name='assets_id_ccee_proinfa')  # Field name made lowercase.
    show_balance = models.CharField(db_column='SHOW_BALANCE', max_length=30)  # Field name made lowercase.
    status = models.CharField(db_column='STATUS', max_length=1)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'assets'

class Submarket(models.Model):
    id_submarket = models.AutoField(db_column='ID_SUBMARKET', primary_key=True)  # Field name made lowercase.
    description = models.CharField(db_column='DESCRIPTION', max_length=5)  # Field name made lowercase.
    status = models.CharField(db_column='STATUS', max_length=1)  # Field name made lowercase.
    id_ccee = models.ForeignKey(CceeDescription, models.DO_NOTHING, db_column='ID_CCEE',
                                related_name='ccee_description', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'SUBMARKET'

class AssetsComposition(models.Model):
    id_assets_composition = models.AutoField(db_column='ID_ASSETS_COMPOSITION', primary_key=True)  # Field name made lowercase.
    id_assets = models.ForeignKey('Assets', models.DO_NOTHING, db_column='ID_ASSETS', blank=True, null=True, related_name='AssetsComposition_id_assets')  # Field name made lowercase.
    id_energy_composition = models.ForeignKey(EnergyComposition, models.DO_NOTHING, db_column='ID_ENERGY_COMPOSITION', blank=True, null=True)  # Field name made lowercase.
    status = models.CharField(db_column='STATUS', max_length=1, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'ASSETS_COMPOSITION'

class SeasonalityProinfa(models.Model):
    id_seasonality_proinfa = models.AutoField(db_column='ID_SEASONALITY_PROINFA', primary_key=True)  # Field name made lowercase.
    id_seasonality = models.ForeignKey(Seasonality, models.DO_NOTHING, db_column='ID_SEASONALITY')  # Field name made lowercase.
    id_ccee = models.ForeignKey(CceeDescription, models.DO_NOTHING, db_column='ID_CCEE', blank=True, null=True, related_name='id_ccee_SeasonalityProinfa')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'SEASONALITY_PROINFA'



#####
class TypePermissionContract(models.Model):
    id_use_contract_type = models.AutoField(db_column='ID_USE_CONTRACT_TYPE', primary_key=True)  # Field name made lowercase.
    description = models.CharField(db_column='DESCRIPTION', max_length=50)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'type_permission_contract'


class NominalTension(models.Model):
    id_rated_voltage = models.AutoField(db_column='ID_RATED_VOLTAGE', primary_key=True)  # Field name made lowercase.
    tension = models.DecimalField(db_column='TENSION', max_digits=18, decimal_places=9)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'nominal_tension'

