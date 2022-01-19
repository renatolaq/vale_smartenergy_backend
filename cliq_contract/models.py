from django.db import models
from profiles.models import Profile
from assets.models import Assets, Submarket
from asset_items.models import AssetItems
from company.models import Company
from agents.models import Agents
from energy_composition.models import EnergyComposition
from energy_contract.models import EnergyContract, EnergyProduct
from core.models import Seasonality,CceeDescription
import json

class JSONField(models.TextField):
    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        return json.loads(value)

    def to_python(self, value):
        if value is None:
          return value
        return json.dumps(value)


class CliqContract(models.Model):
    id_contract_cliq = models.AutoField(db_column='ID_CONTRACT_CLIQ', primary_key=True)  # Field name made lowercase.
    id_vendor_profile = models.ForeignKey(Profile, models.DO_NOTHING,
                                          db_column='ID_VENDOR_PROFILE',
                                          related_name='cliq_vendor')  # Field name made lowercase.
    id_buyer_profile = models.ForeignKey(Profile, models.DO_NOTHING,
                                         db_column='ID_BUYER_PROFILE', blank=True, null=True,
                                         related_name='cliq_buyer')  # Field name made lowercase.
    id_contract = models.ForeignKey(EnergyContract, models.DO_NOTHING,
                                    db_column='ID_CONTRACT', related_name='cliq_contract')  # Field name made lowercase.
    id_ccee = models.ForeignKey(CceeDescription, models.DO_NOTHING, db_column='ID_CCEE',
                                related_name='cliq_ccee', blank=True, null=True)  # Field name made lowercase.
    id_buyer_assets = models.ForeignKey(Assets, models.DO_NOTHING, db_column='BUYER_ASSET_ID', blank=True,
                                    null=True, related_name='cliq_asset')  # Field name made lowercase.
    id_buyer_asset_items = models.ForeignKey(AssetItems, models.DO_NOTHING, db_column='BUYER_ASSET_ITEMS', blank=True,
                                          null=True, related_name='cliq_items')  # Field name made lowercase.
    id_submarket = models.ForeignKey(Submarket, models.DO_NOTHING, db_column='ID_SUBMARKET', blank=True,
                                     null=True, related_name='cliq_submarket')  # Field name made lowercase.
    ccee_type_contract = models.CharField(db_column='CCEE_TYPE_CONTRACT', max_length=5, blank=True,
                                          null=True)  # Field name made lowercase.
    transaction_type = models.CharField(db_column='TRANSACTION_TYPE', max_length=30)  # Field name made lowercase.
    flexibility = models.CharField(db_column='FLEXIBILITY', max_length=20, blank=True,
                                   null=True)  # Field name made lowercase.
    mwm_volume_peak = models.DecimalField(db_column='MWM_VOLUME_PEAK', max_digits=18,
                                     decimal_places=6, blank=True,
                                   null=True)  # Field name made lowercase.
    mwm_volume_offpeak = models.DecimalField(db_column='MWM_VOLUME_OFFPEAK', max_digits=18,
                                     decimal_places=6, blank=True,
                                   null=True)  # Field name made lowercase.
    mwm_volume = models.DecimalField(db_column='MWM_VOLUME', max_digits=18,
                                     decimal_places=6, blank=True,
                                   null=True)  # Field name made lowercase.
    contractual_loss = models.DecimalField(db_column='CONTRACTUAL_LOSS', max_digits=18,
                                           decimal_places=6, blank=True, null=True)  # Field name made lowercase.
    status = models.CharField(db_column='STATUS', max_length=1, blank=True, null=True)  # Field name made lowercase.

    submarket = models.BooleanField(db_column='SUBMARKET', null=True)  # Field name made lowercase.

    modulation_data = JSONField(db_column='DECLARED_MODULATION', null=True, blank=True) # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'CLIQ_CONTRACT'

class SeasonalityCliq(models.Model):
    id_seasonality_cliq = models.AutoField(db_column='ID_SEASONALITY_CLIQ', primary_key=True)  # Field name made lowercase.
    id_seasonality = models.ForeignKey(Seasonality, models.DO_NOTHING, db_column='ID_SEASONALITY', blank=True,
                                          null=True, related_name='seasonalityCliq_seasonality')  # Field name made lowercase.
    id_contract_cliq = models.ForeignKey(CliqContract, models.DO_NOTHING, db_column='ID_CONTRACT_CLIQ', blank=True,
                                         null=True, related_name='seasonalityCliq_cliqContract')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'SEASONALITY_CLIQ'
        unique_together = ('id_seasonality_cliq', 'id_seasonality', 'id_contract_cliq')
        
