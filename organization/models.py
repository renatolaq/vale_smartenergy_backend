from django.db import models

class Segment(models.Model):
    id_segment = models.AutoField(db_column='ID_SEGMENT', primary_key=True)  # Field name made lowercase.
    description = models.CharField(db_column='DESCRIPTION', max_length=30, blank=True,
                                   null=True)  # Field name made lowercase.
    status = models.CharField(db_column='STATUS', max_length=1, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'SEGMENT'

class Business(models.Model):
    id_business = models.AutoField(db_column='ID_BUSINESS', primary_key=True)  # Field name made lowercase.
    description = models.CharField(db_column='DESCRIPTION', max_length=40, blank=True,
                                   null=True)  # Field name made lowercase.
    status = models.CharField(db_column='STATUS', max_length=1, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'BUSINESS'
    
class DirectorBoard(models.Model):
    id_director = models.AutoField(db_column='ID_DIRECTOR', primary_key=True)  # Field name made lowercase.
    description = models.CharField(db_column='DESCRIPTION', max_length=40, blank=True,
                                   null=True)  # Field name made lowercase.
    status = models.CharField(db_column='STATUS', max_length=1, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'DIRECTOR_BOARD'

class AccountantArea(models.Model):
    id_accountant = models.AutoField(db_column='ID_ACCOUNTANT', primary_key=True)  # Field name made lowercase.
    description = models.CharField(db_column='DESCRIPTION', max_length=40, blank=True,
                                   null=True)  # Field name made lowercase.
    status = models.CharField(db_column='STATUS', max_length=1, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'ACCOUNTANT_AREA'

class Product(models.Model):
    id_product = models.AutoField(db_column='ID_PRODUCT', primary_key=True)  # Field name made lowercase.
    description = models.CharField(db_column='DESCRIPTION', max_length=30, blank=True, null=True)  # Field name made lowercase.
    status = models.CharField(db_column='STATUS', max_length=1, blank=True, null=True) 
    class Meta:
        managed = False
        db_table = 'PRODUCT'

class ElectricalGrouping(models.Model):
    id_electrical_grouping = models.AutoField(db_column='ID_ELECTRICAL_GROUPING', primary_key=True)  # Field name made lowercase.
    description = models.CharField(db_column='DESCRIPTION', max_length=50)  # Field name made lowercase.
    status = models.CharField(db_column='STATUS', max_length=1)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'ELECTRICAL_GROUPING'

class ProductionPhase(models.Model):
    id_production_phase = models.AutoField(db_column='ID_PRODUCTION_PHASE', primary_key=True)  # Field name made lowercase.
    description = models.CharField(db_column='DESCRIPTION', max_length=50)  # Field name made lowercase.
    status = models.CharField(db_column='STATUS', max_length=1)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'PRODUCTION_PHASE'

class OrganizationalType(models.Model):
    id_organizational_type = models.AutoField(db_column='ID_ORGANIZATIONAL_TYPE', primary_key=True)  # Field name made lowercase.
    description = models.CharField(db_column='DESCRIPTION', max_length=50)  # Field name made lowercase.
    table_reference = models.CharField(db_column='TABLE_REFERENCE', max_length=128, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'ORGANIZATIONAL_TYPE'