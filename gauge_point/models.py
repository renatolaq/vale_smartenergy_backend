# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey has `on_delete` set to the desired behavior.
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models
from company.models import Company
from organization.models import ElectricalGrouping


class CceeDescription(models.Model):
    id_ccee = models.AutoField(db_column='ID_CCEE', primary_key=True)  # Field name made lowercase.
    code_ccee = models.CharField(db_column='CODE_CCEE', max_length=40, blank=True)  # Field name made lowercase.
    type = models.CharField(db_column='TYPE', max_length=40)  # Field name made lowercase.
    name_ccee = models.CharField(db_column='NAME_CCEE', max_length=30, blank=True,
                                 null=True)  # Field name made lowercase.
    status = models.CharField(db_column='STATUS', max_length=1)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'CCEE_DESCRIPTION'


class SourcePme(models.Model):
    id_source = models.AutoField(db_column='ID_SOURCE', primary_key=True)  # Field name made lowercase.
    display_name = models.CharField(db_column='DISPLAY_NAME', max_length=30)  # Field name made lowercase.
    description = models.CharField(db_column='DESCRIPTION', max_length=30)  # Field name made lowercase.
    id_meter_type = models.ForeignKey('MeterType', models.DO_NOTHING, db_column='ID_METER_TYPE', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'SOURCE_PME'


class Measurements(models.Model):
    id_measurements = models.AutoField(db_column='ID_MEASUREMENTS', primary_key=True)
    unity = models.CharField(db_column='UNITY', max_length=8, blank=True, null=True)
    frequency = models.CharField(db_column='FREQUENCY', max_length=30, blank=True, null=True)
    measurement_name = models.CharField(db_column='MEASUREMENT_NAME', max_length=400, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'MEASUREMENTS'


class ImportSource(models.Model):
    id_import_source = models.AutoField(db_column='ID_IMPORT_SOURCE', primary_key=True)  # Field name made lowercase.
    import_type = models.CharField(db_column='IMPORT_TYPE', max_length=30)  # Field name made lowercase.
    # status = models.CharField(db_column='STATUS', max_length=1)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'IMPORT_SOURCE'


class GaugePoint(models.Model):
    id_gauge = models.AutoField(db_column='ID_GAUGE', primary_key=True)  # Field name made lowercase.
    id_ccee = models.ForeignKey(CceeDescription, models.DO_NOTHING, db_column='ID_CCEE', blank=True,
                                null=True, related_name='gauge_ccee')  # Field name made lowercase.
    id_company = models.ForeignKey(Company, models.DO_NOTHING, db_column='ID_COMPANY', blank=True,
                                   null=True, related_name='gauge_company')  # Field name made lowercase.
    id_source = models.OneToOneField(SourcePme, models.DO_NOTHING, db_column='ID_SOURCE', unique=True, blank=True,
                                     null=True, related_name='gauge_source')  # Field name made lowercase.
    participation_sepp = models.CharField(db_column='PARTICIPATION_SEPP', max_length=1, blank=True,
                                          null=True)  # Field name made lowercase.
    gauge_type = models.CharField(db_column='GAUGE_TYPE', max_length=30, blank=True,
                                  null=True)  # Field name made lowercase.                               
    status = models.CharField(db_column='STATUS', max_length=1, 
                                blank=True, null=True)  # Field name made lowercase.
    id_gauge_type = models.ForeignKey('GaugeType', models.DO_NOTHING, db_column='ID_GAUGE_TYPE', 
                                        blank=True, null=True)  # Field name made lowercase.
    id_electrical_grouping = models.ForeignKey(ElectricalGrouping, models.DO_NOTHING, db_column='ID_ELECTRICAL_GROUPING', 
                                                blank=True, null=True, related_name='electrical_grouping_gaugePoint')  # Field name made lowercase.
    connection_point = models.CharField(db_column='CONNECTION_POINT', max_length=150, 
                                                blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'gauge_point'

class GaugeData(models.Model):
    id_gauge_data = models.AutoField(db_column='ID_GAUGE_DATA', primary_key=True)  # Field name made lowercase.
    id_measurements = models.ForeignKey(Measurements, models.DO_NOTHING,
                                        db_column='ID_MEASUREMENTS')  # Field name made lowercase.
    id_import_source = models.ForeignKey(ImportSource, models.DO_NOTHING,
                                         db_column='ID_IMPORT_SOURCE')  # Field name made lowercase.
    id_gauge = models.ForeignKey(GaugePoint, models.DO_NOTHING, db_column='ID_GAUGE')  # Field name made lowercase.
    utc_creation = models.DateTimeField(db_column='UTC_CREATION', blank=True, null=True)  # Field name made lowercase.
    utc_gauge = models.DateTimeField(db_column='UTC_GAUGE', blank=True, null=True)  # Field name made lowercase.
    value = models.DecimalField(db_column='VALUE', max_digits=18, decimal_places=9, blank=True,
                                null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'GAUGE_DATA'


class GaugeEnergyDealership(models.Model):
    id_gauge_energy_dealership = models.AutoField(db_column='ID_GAUGE_ENERGY_DEALERSHIP',
                                                  primary_key=True)  # Field name made lowercase.
    id_gauge_point = models.OneToOneField(GaugePoint, models.DO_NOTHING, db_column='ID_GAUGE_POINT',
                                          unique=True, related_name='gauge_dealership')  # Field name made lowercase.
    id_dealership = models.ForeignKey(Company, models.DO_NOTHING, db_column='ID_DEALERSHIP', blank=True,
                                      null=True, related_name='company_dealership')  # Field name made lowercase.
    status = models.CharField(db_column='STATUS', max_length=1, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'GAUGE_ENERGY_DEALERSHIP'





class UpstreamMeter(models.Model):
    id_upstream = models.AutoField(db_column='ID_UPSTREAM',
                                   primary_key=True)  # Field name made lowercase.
    id_upstream_meter = models.ForeignKey(GaugePoint, models.DO_NOTHING,
                                          db_column='ID_UPSTREAM_METER',
                                          related_name='gauge_dad')  # Field name made lowercase.
    id_gauge = models.ForeignKey(GaugePoint, models.DO_NOTHING, db_column='ID_GAUGE',
                                 related_name='gauge_chield')  # Field name made lowercase.
    status = models.CharField(db_column='STATUS', max_length=1, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'UPSTREAM_METER'

class GaugeType(models.Model):
    id_gauge_type = models.AutoField(db_column='ID_GAUGE_TYPE', primary_key=True)  # Field name made lowercase.
    description = models.CharField(db_column='DESCRIPTION', max_length=50, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'GAUGE_TYPE'

class MeterType(models.Model):
    id_meter_type = models.AutoField(db_column='ID_METER_TYPE', primary_key=True)  # Field name made lowercase.
    description = models.CharField(db_column='DESCRIPTION', max_length=50, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'METER_TYPE'