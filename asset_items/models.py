from django.db import models

from assets.models import Assets
from company.models import Company
from core.models import Seasonality
from energy_composition.models import EnergyComposition


# Create your models here.
class AssetItems(models.Model):
    id_asset_items = models.AutoField(db_column='ID_ASSET_ITEMS', primary_key=True)  # Field name made lowercase.
    id_assets = models.ForeignKey(Assets, models.DO_NOTHING, db_column='ID_ASSETS', blank=True,
                                  null=True, related_name='assetitems_asset')  # Field name made lowercase.
    id_company = models.OneToOneField(Company, models.DO_NOTHING,
                                      db_column='ID_COMPANY',
                                      related_name='assetitems_company')  # Field name made lowercase.
    id_energy_composition = models.ForeignKey(EnergyComposition, models.DO_NOTHING, db_column='ID_ENERGY_COMPOSITION',
                                              blank=True, null=True, related_name='assetitems_energycomposition')
    status = models.CharField(db_column='STATUS', max_length=1, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'ASSET_ITEMS'

# Creation of new table with the comand: python manage.py inspectdb SEAZONALITY_ASSET_ITEM_DEPRECIATION modelsv2.py
#       for using in case the type of season 3 is depreciation 
# Type available: depreciation or generation  
class SeazonalityAssetItemDepreciation(models.Model):
    seazonality_asset_depreciation = models.AutoField(db_column='SEAZONALITY_ASSET_DEPRECIATION',
                                                      primary_key=True)  # Field name made lowercase.
    id_asset_items = models.ForeignKey('AssetItems', models.DO_NOTHING, db_column='ID_ASSET_ITEMS',
                                       related_name='assetitem_depreciation')  # Field name made lowercase.
    id_seasonality = models.ForeignKey(Seasonality, models.DO_NOTHING,
                                       db_column='ID_SEASONALITY')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'SEAZONALITY_ASSET_ITEM_DEPRECIATION'
        unique_together = (('seazonality_asset_depreciation', 'id_asset_items', 'id_seasonality'),)


class SeasonalityAssetItemCost(models.Model):
    id_seasonality_asset_item_cost = models.AutoField(db_column='ID_SEASONALITY_ASSET_ITEM_COST',
                                                      primary_key=True)  # Field name made lowercase.
    id_seazonality_asset = models.ForeignKey(Seasonality, models.DO_NOTHING,
                                             db_column='ID_SEAZONALITY_ASSET')  # Field name made lowercase.
    id_asset_items = models.ForeignKey('AssetItems', models.DO_NOTHING, db_column='ID_ASSET_ITEMS',
                                       related_name='assetitem_cost')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'SEASONALITY_ASSET_ITEM_COST'
        unique_together = (('id_asset_items', 'id_seasonality_asset_item_cost', 'id_seazonality_asset'),)


class SeasonalityAssetItem(models.Model):
    id_seasonality_asset_item = models.AutoField(db_column='ID_SEASONALITY_ASSET_ITEM',
                                                 primary_key=True)  # Field name made lowercase.
    id_seasonality = models.ForeignKey(Seasonality, models.DO_NOTHING,
                                       db_column='ID_SEASONALITY')  # Field name made lowercase.
    id_asset_items = models.ForeignKey('AssetItems', models.DO_NOTHING, db_column='ID_ASSET_ITEMS',
                                       related_name='assetitem_seasonality')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'seasonality_asset_item'
        unique_together = (('id_seasonality_asset_item', 'id_seasonality', 'id_asset_items'),)
