# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey has `on_delete` set to the desired behavior.
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models

from agents.models import Agents
from profiles.models import Profile


class EnergyProduct(models.Model):
    id_energy_product = models.AutoField(db_column='ID_ENERGY_PRODUCT', primary_key=True)  # Field name made lowercase.
    description = models.CharField(db_column='DESCRIPTION', max_length=30)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'ENERGY_PRODUCT'


class VariableType(models.Model):
    id_variable = models.AutoField(db_column='ID_VARIABLE', primary_key=True)  # Field name made lowercase.
    name = models.CharField(db_column='NAME', max_length=30, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Variable_Type'


class Variable(models.Model):
    id_variable = models.AutoField(db_column='ID_VARIABLE', primary_key=True)  # Field name made lowercase.
    type_id_variable = models.ForeignKey(VariableType, models.DO_NOTHING, db_column='TYPE_ID_VARIABLE', blank=True,
                                         null=True)  # Field name made lowercase.
    name = models.CharField(db_column='NAME', max_length=40, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Variable'


class EnergyContract(models.Model):
    id_contract = models.AutoField(db_column='ID_CONTRACT', primary_key=True)  # Field name made lowercase.
    id_buyer_agents = models.ForeignKey(Agents, models.DO_NOTHING, db_column='ID_BUYER_AGENTS', blank=True,
                                        null=True, related_name="buyer_agents")  # Field name made lowercase.
    id_seller_agents = models.ForeignKey(Agents, models.DO_NOTHING, db_column='ID_SELLER_AGENTS', blank=True,
                                         null=True, related_name="seller_agents")  # Field name made lowercase.
    id_buyer_profile = models.ForeignKey(Profile, models.DO_NOTHING, db_column='ID_BUYER_PROFILE', blank=True,
                                         null=True, related_name='buyer_profile')  # Field name made lowercase.
    id_seller_profile = models.ForeignKey(Profile, models.DO_NOTHING, db_column='ID_SELLER_PROFILE', blank=True,
                                          null=True, related_name='seller_profile')  # Field name made lowercase.
    id_energy_product = models.ForeignKey(EnergyProduct, models.DO_NOTHING, db_column='ID_ENERGY_PRODUCT',
                                          related_name='energy_product')  # Field name made lowercase.
    modality = models.CharField(db_column='MODALITY', max_length=13)  # Field name made lowercase.
    sap_contract = models.DecimalField(db_column='SAP_CONTRACT', max_digits=20,
                                       decimal_places=0, blank=True, null=True)  # Field name made lowercase.
    type = models.CharField(db_column='TYPE', max_length=1, blank=True, null=True)  # Field name made lowercase.
    start_supply = models.DateTimeField(db_column='START_SUPPLY')  # Field name made lowercase.
    end_supply = models.DateTimeField(db_column='END_SUPPLY')  # Field name made lowercase.
    contract_status = models.CharField(db_column='CONTRACT_STATUS', max_length=2, blank=True,
                                       null=True)  # Field name made lowercase.
    signing_data = models.DateTimeField(db_column='SIGNING_DATA', blank=True, null=True)  # Field name made lowercase.
    volume_mwm = models.DecimalField(db_column='VOLUME__MWM', max_digits=18,
                                     decimal_places=6, blank=True, null=True)  # Field name made lowercase.
    volume_mwh = models.DecimalField(db_column='VOLUME__MWH', max_digits=18,
                                     decimal_places=3, blank=True, null=True)  # Field name made lowercase.
    contract_name = models.CharField(db_column='CONTRACT_NAME', unique=True,
                                     max_length=120)  # Field name made lowercase.
    status = models.CharField(db_column='STATUS', max_length=1, blank=True, null=True)  # Field name made lowercase.
    temporary_expire_time = models.DateTimeField(db_column='TEMPORARY_EXPIRE_TIME', null=True)  # Field name made lowercase.
    market = models.BooleanField(db_column='MARKET', null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'ENERGY_CONTRACT'


class Precification(models.Model):
    id_contract = models.OneToOneField('EnergyContract', models.DO_NOTHING, db_column='ID_CONTRACT', primary_key=True,
                                       related_name='precif_energy_contract')  # Field name made lowercase.
    base_price_mwh = models.DecimalField(db_column='BASE_PRICE_MWH', max_digits=18, decimal_places=6, blank=True,
                                         null=True)  # Field name made lowercase.
    base_price_date = models.DateTimeField(db_column='BASE_PRICE_DATE', blank=True,
                                           null=True)  # Field name made lowercase.
    # Calculated field: BASE CONTRACT VALUE
    birthday_date = models.DateTimeField(db_column='BIRTHDAY_DATE', blank=True, null=True)  # Field name made lowercase.
    id_variable = models.ForeignKey(Variable, models.DO_NOTHING, db_column='ID_VARIABLE', null=True, related_name="variable")  # Field name made lowercase.    
    active_price_mwh = models.DecimalField(db_column='ACTIVE_PRICE_MWH', max_digits=18, decimal_places=6, blank=True,
                                           null=True)  # Field name made lowercase.
    retusd = models.DecimalField(db_column='RETUSD', max_digits=18, decimal_places=6, blank=True,
                                 null=True)  # Field name made lowercase.
    last_updated_current_price = models.DateTimeField(db_column='LAST_UPDATED_CURRENT_PRICE', null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'PRECIFICATION'

class FlexibilizationType(models.Model):
    id_flexibilization_type = models.AutoField(db_column="ID_FLEXIBILIZATION_TYPE", primary_key=True)  # Field name made lowercase.
    flexibilization = models.CharField(db_column='FLEXIBILIZATION', max_length=50)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'FLEXIBILIZATION_TYPE'

class Flexibilization(models.Model):
    id_contract = models.OneToOneField('EnergyContract', models.DO_NOTHING, db_column='ID_CONTRACT', primary_key=True,
                                       related_name='flexib_energy_contract')  # Field name made lowercase.
    flexibility_type = models.CharField(db_column='FLEXIBILITY_TYPE', max_length=30)  # Field name made lowercase.
    id_flexibilization_type = models.ForeignKey(FlexibilizationType, models.DO_NOTHING, db_column='ID_FLEXIBILIZATION_TYPE', null=True, related_name="flexibilization_type") 
    min_flexibility_pu_offpeak = models.DecimalField(db_column='MIN_FLEXIBILITY_PU', max_digits=18, decimal_places=6,
                                             blank=True, null=True)  # Field name made lowercase.
    max_flexibility_pu_offpeak = models.DecimalField(db_column='MAX_FLEXIBILITY_PU', max_digits=18, decimal_places=6,
                                             blank=True, null=True)  # Field name made lowercase.
    min_flexibility_pu_peak = models.DecimalField(db_column='MIN_FLEXIBILITY_PU_PEAK', max_digits=18, decimal_places=6,
                                             blank=True, null=True)  # Field name made lowercase.
    max_flexibility_pu_peak = models.DecimalField(db_column='MAX_FLEXIBILITY_PU_PEAK', max_digits=18, decimal_places=6,
                                             blank=True, null=True)  # Field name made lowercase.
    proinfa_flexibility = models.CharField(db_column='PROINFA_FLEXIBILITY', max_length=1)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'FLEXIBILIZATION'


class Modulation(models.Model):
    id_contract = models.OneToOneField('EnergyContract', models.DO_NOTHING, db_column='ID_CONTRACT', primary_key=True,
                                       related_name='modul_energy_contract')  # Field name made lowercase.
    modulation_type = models.CharField(db_column='MODULATION_TYPE', max_length=30)  # Field name made lowercase.
    min_modulation_pu = models.DecimalField(db_column='MIN_MODULATION_PU', max_digits=18, decimal_places=6, blank=True,
                                            null=True)  # Field name made lowercase.
    max_modulation_pu = models.DecimalField(db_column='MAX_MODULATION_PU', max_digits=18, decimal_places=6, blank=True,
                                            null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'MODULATION'


class Seasonal(models.Model):
    id_contract = models.OneToOneField('EnergyContract', models.DO_NOTHING, db_column='ID_CONTRACT', primary_key=True,
                                       related_name='season_energy_contract')  # Field name made lowercase.
    type_seasonality = models.CharField(db_column='TYPE_SEASONALITY', max_length=30, blank=True,
                                        null=True)  # Field name made lowercase.
    season_min_pu = models.DecimalField(db_column='SEASON_MIN_PU', max_digits=18, decimal_places=6, blank=True,
                                        null=True)  # Field name made lowercase.
    season_max_pu = models.DecimalField(db_column='SEASON_MAX_PU', max_digits=18, decimal_places=6, blank=True,
                                        null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'SEASONAL'


class Guarantee(models.Model):
    id_contract = models.OneToOneField('EnergyContract', models.DO_NOTHING, db_column='ID_CONTRACT', primary_key=True,
                                       related_name='guaran_energy_contract')  # Field name made lowercase.
    month_hour = models.DecimalField(db_column='MONTH_HOUR', max_digits=3, decimal_places=0, blank=True,
                                     null=True)  # Field name made lowercase.
    # Calculated field: HOURS
    guaranteed_value = models.DecimalField(db_column='GUARANTEED_VALUE', max_digits=18, decimal_places=9, blank=True,
                                           null=True)  # Field name made lowercase.
    emission_date = models.DateTimeField(db_column='EMISSION_DATE', blank=True, null=True)  # Field name made lowercase.
    effective_date = models.DateTimeField(db_column='EFFECTIVE_DATE', blank=True,
                                          null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'GUARANTEE'


class ContractAttachment(models.Model):
    id_attachment = models.AutoField(db_column="ID_ATTACHMENT", primary_key=True)  # Field name made lowercase.
    id_contract = models.ForeignKey(
        "EnergyContract", models.DO_NOTHING, db_column="ID_CONTRACT", blank=True, null=True
    )  # Field name made lowercase.
    name = models.CharField(db_column="NAME", max_length=100, blank=True, null=True)  # Field name made lowercase.
    revision = models.CharField(
        db_column="REVISION", max_length=10, blank=True, null=True
    )  # Field name made lowercase.
    comments = models.CharField(
        db_column="COMMENTS", max_length=100, blank=True, null=True
    )  # Field name made lowercase.
    path = models.CharField(db_column="PATH", max_length=100, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = "CONTRACT_ATTACHMENT"


class GlobalVariable(models.Model):
    id_global_variable = models.AutoField(db_column='ID_GLOBAL_VARIABLE',
                                          primary_key=True)  # Field name made lowercase.
    id_variable = models.DecimalField(db_column='ID_VARIABLE', max_digits=9, decimal_places=0, blank=True,
                                      null=True)  # Field name made lowercase.
    id_unity = models.DecimalField(db_column='ID_UNITY', max_digits=9, decimal_places=0, blank=True,
                                   null=True)  # Field name made lowercase.
    id_state = models.DecimalField(db_column='ID_STATE', max_digits=9, decimal_places=0, blank=True,
                                   null=True)  # Field name made lowercase.
    value = models.DecimalField(db_column='VALUE', max_digits=18, decimal_places=9, blank=True,
                                null=True)  # Field name made lowercase.
    month = models.DecimalField(db_column='MONTH', max_digits=2, decimal_places=0, blank=True,
                                null=True)  # Field name made lowercase.
    year = models.DecimalField(db_column='YEAR', max_digits=4, decimal_places=0, blank=True,
                               null=True)  # Field name made lowercase.
    marketing_flag = models.CharField(db_column='MARKETING_FLAG', max_length=1, blank=True,
                                      null=True)  # Field name made lowercase.
    status = models.CharField(db_column='STATUS', max_length=1, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'GLOBAL_VARIABLE'
