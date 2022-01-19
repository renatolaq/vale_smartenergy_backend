from django.db import models
from datetime import datetime
from decimal import Decimal


class ImportSource(models.Model):
    id_import_source = models.AutoField(db_column='ID_IMPORT_SOURCE', primary_key=True)  # Field name made lowercase.
    import_type = models.CharField(db_column='IMPORT_TYPE', max_length=30)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'IMPORT_SOURCE'


class Log(models.Model):
    id = models.AutoField(db_column='ID_LOG', primary_key=True)
    field_pk = models.DecimalField(db_column='FIELD_PK', max_digits=9, decimal_places=0, null=True)
    table_name = models.CharField(db_column='TABLE_NAME', max_length=30, blank=True, null=True)
    action_type = models.CharField(db_column='ACTION_TYPE', max_length=30, blank=True, null=True)
    old_value = models.TextField(db_column='OLD_VALUE', blank=True, null=True)
    new_value = models.TextField(db_column='NEW_VALUE', blank=True, null=True)
    observation = models.TextField(db_column='OBSERVATION', blank=True, null=True)
    date = models.DateTimeField(db_column='DATE', blank=True, null=True)
    user = models.TextField(db_column='USER', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'LOG'


class CceeDescription(models.Model):
    id_ccee = models.AutoField(db_column='ID_CCEE', primary_key=True)  # Field name made lowercase.
    code_ccee = models.CharField(db_column='CODE_CCEE', max_length=40)  # Field name made lowercase.
    type = models.CharField(db_column='TYPE', max_length=40)  # Field name made lowercase.
    name_ccee = models.CharField(db_column='NAME_CCEE', max_length=30, blank=True, null=True)  # Field name made lowercase.
    status = models.CharField(db_column='STATUS', max_length=1)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'CCEE_DESCRIPTION'


class Address(models.Model):
    id_address = models.AutoField(db_column='ID_ADDRESS', primary_key=True)  # Field name made lowercase.
    id_city = models.ForeignKey('City', models.DO_NOTHING, db_column='ID_CITY', blank=True, null=True)  # Field name made lowercase.
    street = models.CharField(db_column='STREET', max_length=100, blank=True, null=True)  # Field name made lowercase.
    number = models.DecimalField(db_column='NUMBER', max_digits=9, decimal_places=0, blank=True, null=True)  # Field name made lowercase.
    zip_code = models.CharField(db_column='ZIP_CODE', max_length=40, blank=True, null=True)  # Field name made lowercase.
    complement = models.CharField(db_column='COMPLEMENT', max_length=30, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'ADDRESS'


class Company(models.Model):
    id_company = models.AutoField(db_column='ID_COMPANY', primary_key=True)  # Field name made lowercase.
    id_address = models.ForeignKey(Address, models.DO_NOTHING, db_column='ID_ADDRESS', blank=True, null=True, related_name="address_company")  # Field name made lowercase.
    company_name = models.CharField(db_column='COMPANY_NAME', max_length=250)  # Field name made lowercase.
    legal_name = models.CharField(db_column='LEGAL_NAME', max_length=250)  # Field name made lowercase.
    registered_number = models.CharField(db_column='REGISTERED_NUMBER', max_length=12, blank=True, null=True)  # Field name made lowercase.
    type = models.CharField(db_column='TYPE', max_length=5)  # Field name made lowercase.
    state_number = models.CharField(db_column='STATE_NUMBER', max_length=18)  # Field name made lowercase.
    nationality = models.CharField(db_column='NATIONALITY', max_length=3)  # Field name made lowercase.
    id_sap = models.CharField(db_column='ID_SAP', unique=True, max_length=18)  # Field name made lowercase.
    characteristics = models.CharField(db_column='CHARACTERISTICS', max_length=30, blank=True, null=True)  # Field name made lowercase.
    status = models.CharField(db_column='STATUS', max_length=1)  # Field name made lowercase.
    create_date = models.DateTimeField(db_column='CREATE_DATE', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'COMPANY'


class Report(models.Model):
    id = models.AutoField(db_column='ID_REPORT', primary_key=True)
    report_type = models.ForeignKey('ReportType', related_name='report_type', on_delete=models.DO_NOTHING, db_column='ID_REPORT_TYPE', null=True)
    id_reference = models.ForeignKey('self', related_name='related_report', on_delete=models.DO_NOTHING, db_column='ID_REFERENCE', null=True)
    creation_date = models.DateTimeField(db_column='CREATION_DATE', null=False, default=datetime.now)
    report_name = models.CharField(db_column='REPORT_NAME', max_length=50, unique=True, null=False, blank=False)
    status = models.CharField(db_column='STATUS', max_length=1, null=False, blank=False, default=None)
    month = models.CharField(db_column='MONTH', max_length=2, null=False, blank=False, default=None)
    year = models.CharField(db_column='YEAR', max_length=4, null=False, blank=False, default=None)
    limit_value = models.DecimalField(db_column='LIMIT_VALUE', max_digits=18, decimal_places=9, null=True)
    class Meta:
        managed = False
        db_table = 'REPORT_TABLE'


class MeteringReportData(models.Model):
    id = models.AutoField(db_column='ID_METERING_REPORT_DATA', primary_key=True)
    id_company = models.ForeignKey('Company', related_name='company_related', on_delete=models.DO_NOTHING, db_column='ID_COMPANY', null=True)
    report = models.ForeignKey(Report, related_name='metering_report_data', on_delete=models.CASCADE, db_column='ID_REPORT')
    ccee_code = models.CharField(max_length=40, null=True)
    gauge_tag = models.CharField(max_length=50, null=True)
    id_company = models.ForeignKey('Company', related_name='metering_report_data_company', on_delete=models.DO_NOTHING, db_column='ID_COMPANY')
    id_assets = models.ForeignKey("Assets", on_delete=models.DO_NOTHING, db_column='ID_ASSETS')
    id_asset_items = models.ForeignKey("AssetItems", on_delete=models.DO_NOTHING, db_column='ID_ASSET_ITEMS')
    associated_company = models.CharField(max_length=100)
    director_board = models.CharField(max_length=40, null=True)
    business = models.CharField(max_length=40, null=True)
    data_source = models.CharField(max_length=4, null=True)
    loss_type = models.CharField(max_length=1, null=True)
    updated_consumption = models.BooleanField(db_column="UPDATED_CONSUMPTION", null=True)

    class Meta:
        managed = False
        db_table = 'METERING_REPORT_DATA'
 

class MeteringReportValue(models.Model):
    id = models.AutoField(db_column='ID_METERING_VALUE', primary_key=True)
    metering_report_data = models.ForeignKey(MeteringReportData, related_name='consumption_values', on_delete=models.CASCADE, db_column='ID_METERING_REPORT_DATA')
    off_peak_consumption_value = models.DecimalField(max_digits=18, decimal_places=9, null=True)
    on_peak_consumption_value = models.DecimalField(max_digits=18, decimal_places=9, null=True)
    ccee_consumption_value = models.DecimalField(max_digits=18, decimal_places=9, null=True)
    ccee_metering_days = models.DecimalField(max_digits=18, decimal_places=9)
    vale_consumption_value = models.DecimalField(max_digits=18, decimal_places=9, null=True)
    vale_metering_days = models.DecimalField(max_digits=18, decimal_places=9)
    loss = models.DecimalField(max_digits=18, decimal_places=9, null=True, default=Decimal('0.0'))
    total_consumption_loss = models.DecimalField(max_digits=18, decimal_places=9, null=True)

    class Meta:
        managed = False
        db_table = 'METERING_REPORT_VALUE'


class ReportType(models.Model):
    id = models.AutoField(db_column='ID_REPORT_TYPE', primary_key=True)  # Field name made lowercase.
    name = models.CharField(db_column='REPORT_NAME', max_length=50)  # Field name made lowercase.
    initials = models.CharField(db_column='REPORT_INITIALS', max_length=3)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'REPORT_TYPE'


class Country(models.Model):
    id_country = models.AutoField(db_column='ID_COUNTRY', primary_key=True)  # Field name made lowercase.
    name = models.CharField(db_column='NAME', max_length=30)  # Field name made lowercase.
    initials = models.CharField(db_column='INITIALS', max_length=4, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'COUNTRY'


class City(models.Model):
    id_city = models.AutoField(db_column='ID_CITY', primary_key=True)  # Field name made lowercase.
    id_state = models.ForeignKey('State', models.DO_NOTHING, db_column='ID_STATE', blank=True, null=True)  # Field name made lowercase.
    city_name = models.CharField(db_column='CITY_NAME', max_length=40, blank=True, null=True)  # Field name made lowercase.
    initials = models.CharField(db_column='INITIALS', max_length=40, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'CITY'


class State(models.Model):
    id_state = models.AutoField(db_column='ID_STATE', primary_key=True)  # Field name made lowercase.
    id_country = models.ForeignKey(Country, models.DO_NOTHING, db_column='ID_COUNTRY', blank=True, null=True)  # Field name made lowercase.
    name = models.CharField(db_column='NAME', max_length=100, blank=True, null=True)  # Field name made lowercase.
    initials = models.CharField(db_column='INITIALS', max_length=4, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'STATE'


class SourcePme(models.Model):
    id_source = models.AutoField(db_column='ID_SOURCE', primary_key=True)  # Field name made lowercase.
    display_name = models.CharField(db_column='DISPLAY_NAME', max_length=50)  # Field name made lowercase.
    description = models.CharField(db_column='DESCRIPTION', max_length=50)  # Field name made lowercase.
    id_meter_type = models.ForeignKey('MeterType', models.DO_NOTHING, db_column='ID_METER_TYPE', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'SOURCE_PME'


class MeterType(models.Model):
    id_meter_type = models.AutoField(db_column='ID_METER_TYPE', primary_key=True)  # Field name made lowercase.
    description = models.CharField(db_column='DESCRIPTION', max_length=50)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'METER_TYPE'


class Measurements(models.Model):
    id_measurements = models.AutoField(db_column='ID_MEASUREMENTS', primary_key=True)  # Field name made lowercase.
    measurement_name = models.CharField(db_column='MEASUREMENT_NAME', max_length=40, blank=True, null=True)  # Field name made lowercase.
    unity = models.CharField(db_column='UNITY', max_length=8, blank=True, null=True)  # Field name made lowercase.
    frequency = models.CharField(db_column='FREQUENCY', max_length=30)

    class Meta:
        managed = False
        db_table = 'MEASUREMENTS'


class GaugePoint(models.Model):
    id_gauge = models.AutoField(db_column='ID_GAUGE', primary_key=True)  # Field name made lowercase.
    id_ccee = models.ForeignKey(CceeDescription, models.DO_NOTHING, db_column='ID_CCEE', blank=True, null=True)  # Field name made lowercase.
    id_company = models.ForeignKey(Company, related_name='gauge_points', on_delete=models.CASCADE, db_column='ID_COMPANY')  # Field name made lowercase.
    id_source = models.ForeignKey('SourcePme', related_name='gauge_points', on_delete=models.CASCADE, db_column='ID_SOURCE')  # Field name made lowercase.
    participation_sepp = models.CharField(db_column='PARTICIPATION_SEPP', max_length=1, blank=True, null=True)  # Field name made lowercase.
    gauge_type = models.CharField(db_column='GAUGE_TYPE', max_length=30, blank=True, null=True)  # Field name made lowercase.
    status = models.CharField(db_column='STATUS', max_length=1, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'GAUGE_POINT'


class GaugeData(models.Model):
    id_gauge_data = models.AutoField(db_column='ID_GAUGE_DATA', primary_key=True)  # Field name made lowercase.
    id_measurements = models.ForeignKey('Measurements', models.DO_NOTHING, db_column='ID_MEASUREMENTS')  # Field name made lowercase.
    id_import_source = models.ForeignKey('ImportSource', models.DO_NOTHING, db_column='ID_IMPORT_SOURCE')  # Field name made lowercase.
    id_gauge = models.ForeignKey('GaugePoint', related_name='gauge_data', db_column='ID_GAUGE', on_delete=models.CASCADE)
    utc_creation = models.DateTimeField(db_column='UTC_CREATION', blank=True, null=True)  # Field name made lowercase.
    utc_gauge = models.DateTimeField(db_column='UTC_GAUGE', blank=True, null=True)  # Field name made lowercase.
    value = models.DecimalField(db_column='VALUE', max_digits=18, decimal_places=9, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'GAUGE_DATA'


class DirectorBoard(models.Model):
    id_director = models.AutoField(db_column='ID_DIRECTOR', primary_key=True)  # Field name made lowercase.
    description = models.CharField(db_column='DESCRIPTION', max_length=40, blank=True, null=True)  # Field name made lowercase.
    status = models.CharField(db_column='STATUS', max_length=1, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'DIRECTOR_BOARD'


class Submarket(models.Model):
    id_submarket = models.AutoField(db_column='ID_SUBMARKET', primary_key=True)  # Field name made lowercase.
    description = models.CharField(db_column='DESCRIPTION', max_length=5)  # Field name made lowercase.
    status = models.CharField(db_column='STATUS', max_length=1)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'SUBMARKET'


class Agents(models.Model):
    id_agents = models.AutoField(db_column='ID_AGENTS', primary_key=True)  # Field name made lowercase.
    id_company = models.ForeignKey('Company', models.DO_NOTHING, db_column='ID_COMPANY')  # Field name made lowercase.
    id_ccee = models.OneToOneField('CceeDescription', models.DO_NOTHING, db_column='ID_CCEE')  # Field name made lowercase.
    vale_name_agent = models.CharField(db_column='VALE_NAME_AGENT', max_length=40)  # Field name made lowercase.
    status = models.CharField(db_column='STATUS', max_length=1)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'AGENTS'


class Profile(models.Model):
    id_profile = models.AutoField(db_column='ID_PROFILE', primary_key=True)  # Field name made lowercase.
    id_agents = models.ForeignKey(Agents, models.DO_NOTHING, db_column='ID_AGENTS', blank=True, null=True)  # Field name made lowercase.
    id_ccee = models.OneToOneField(CceeDescription, models.DO_NOTHING, db_column='ID_CCEE')  # Field name made lowercase.
    name_profile = models.CharField(db_column='NAME_PROFILE', max_length=40)  # Field name made lowercase.
    alpha = models.CharField(db_column='ALPHA', max_length=1)  # Field name made lowercase.
    status = models.CharField(db_column='STATUS', max_length=1)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'PROFILE'


class Assets(models.Model):
    id_assets = models.AutoField(db_column='ID_ASSETS', primary_key=True)  # Field name made lowercase.
    id_submarket = models.ForeignKey('Submarket', models.DO_NOTHING, db_column='ID_SUBMARKET')  # Field name made lowercase.
    id_company = models.ForeignKey('Company', related_name='assets', on_delete=models.CASCADE, db_column='ID_COMPANY')  # Field name made lowercase.
    id_profile = models.ForeignKey('Profile', models.DO_NOTHING, db_column='ID_PROFILE')  # Field name made lowercase.
    id_ccee_proinfa = models.ForeignKey('CceeDescription', related_name='proinfa', on_delete=models.CASCADE, db_column='ID_CCEE_PROINFA', null=True)  # Field name made lowercase.
    id_ccee_siga = models.OneToOneField('CceeDescription', models.DO_NOTHING, db_column='ID_CCEE_SIGA')  # Field name made lowercase.
    show_balance = models.CharField(db_column='SHOW_BALANCE', max_length=30)  # Field name made lowercase.
    status = models.CharField(db_column='STATUS', max_length=1)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'ASSETS'


class AssetsComposition(models.Model):
    id_assets_composition = models.AutoField(db_column='ID_ASSETS_COMPOSITION', primary_key=True)  # Field name made lowercase.
    id_assets = models.ForeignKey(Assets, related_name='asset_composition', on_delete=models.CASCADE, db_column='ID_ASSETS', null=True)  # Field name made lowercase.
    id_energy_composition = models.ForeignKey('EnergyComposition', on_delete=models.CASCADE, db_column='ID_ENERGY_COMPOSITION', null=True)  # Field name made lowercase.
    status = models.CharField(db_column='STATUS', max_length=1, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'ASSETS_COMPOSITION'


class AssetItems(models.Model):
    id_asset_items = models.AutoField(db_column='ID_ASSET_ITEMS', primary_key=True)  # Field name made lowercase.
    id_assets = models.ForeignKey(Assets, related_name='asset_items', on_delete=models.CASCADE, db_column='ID_ASSETS', null=True)  # Field name made lowercase.
    id_company = models.OneToOneField('Company', on_delete=models.CASCADE, db_column='ID_COMPANY')  # Field name made lowercase.
    id_energy_composition = models.ForeignKey('EnergyComposition', on_delete=models.CASCADE, db_column='ID_ENERGY_COMPOSITION', blank=True, null=True)  # Field name made lowercase.
    status = models.CharField(db_column='STATUS', max_length=1, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'ASSET_ITEMS'


class Segment(models.Model):
    id_segment = models.AutoField(db_column='ID_SEGMENT', primary_key=True)  # Field name made lowercase.
    description = models.CharField(db_column='DESCRIPTION', max_length=30, blank=True, null=True)  # Field name made lowercase.
    status = models.CharField(db_column='STATUS', max_length=1, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'SEGMENT'


class Product(models.Model):
    id_product = models.AutoField(db_column='ID_PRODUCT', primary_key=True)  # Field name made lowercase.
    description = models.CharField(db_column='DESCRIPTION', max_length=30, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'PRODUCT'


class AccountantArea(models.Model):
    id_accountant = models.AutoField(db_column='ID_ACCOUNTANT', primary_key=True)  # Field name made lowercase.
    description = models.CharField(db_column='DESCRIPTION', max_length=40, blank=True, null=True)  # Field name made lowercase.
    status = models.CharField(db_column='STATUS', max_length=1, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'ACCOUNTANT_AREA'


class Business(models.Model):
    id_business = models.AutoField(db_column='ID_BUSINESS', primary_key=True)  # Field name made lowercase.
    description = models.CharField(db_column='DESCRIPTION', max_length=40, blank=True, null=True)  # Field name made lowercase.
    status = models.CharField(db_column='STATUS', max_length=1, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'BUSINESS'


class EnergyComposition(models.Model):
    id_energy_composition = models.AutoField(db_column='ID_ENERGY_COMPOSITION', primary_key=True)
    id_director = models.ForeignKey(DirectorBoard, models.DO_NOTHING, db_column='ID_DIRECTOR', blank=True, null=True)
    id_segment = models.ForeignKey('Segment', models.DO_NOTHING, db_column='ID_SEGMENT', blank=True, null=True)
    id_accountant = models.ForeignKey(AccountantArea, models.DO_NOTHING, db_column='ID_ACCOUNTANT', blank=True, null=True)
    id_company = models.ForeignKey(Company, related_name='energy_compositions', on_delete=models.CASCADE, db_column='ID_COMPANY', blank=True, null=True)  # Field name made lowercase.
    id_business = models.ForeignKey(Business, models.DO_NOTHING, db_column='ID_BUSINESS', blank=True, null=True)  # Field name made lowercase.
    composition_name = models.CharField(db_column='COMPOSITION_NAME', unique=True, max_length=30)  # Field name made lowercase.
    cost_center = models.CharField(db_column='COST_CENTER', max_length=30, blank=True, null=True)  
    profit_center = models.CharField(db_column='PROFIT_CENTER', max_length=30, blank=True, null=True)  # Field name made lowercase.
    kpi_formulae = models.TextField(db_column='KPI_FORMULAE', blank=True, null=True)  # Field name made lowercase.
    save_date = models.DateTimeField(db_column='SAVE_DATE', blank=True, null=True)  # Field name made lowercase.
    composition_loss = models.DecimalField(db_column='COMPOSITION_LOSS', max_digits=18, decimal_places=9, blank=True, null=True)  # Field name made lowercase.
    status = models.CharField(db_column='STATUS', max_length=1, blank=True, null=True)  # Field name made lowercase.
    description = models.CharField(db_column='DESCRIPTION', max_length=100, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'ENERGY_COMPOSITION'
