from django.db import models

# Create your models here.
from company.models import Company
from organization.models import AccountantArea, Business, DirectorBoard, Product, Segment, ProductionPhase
from gauge_point.models import GaugePoint


class EnergyComposition(models.Model):
    id_energy_composition = models.AutoField(db_column='ID_ENERGY_COMPOSITION',
                                             primary_key=True)  # Field name made lowercase.
    id_director = models.ForeignKey(DirectorBoard, models.DO_NOTHING, db_column='ID_DIRECTOR', blank=True,
                                    null=True, related_name='director_energyComposition')  # Field name made lowercase.
    id_segment = models.ForeignKey(Segment, models.DO_NOTHING, db_column='ID_SEGMENT', blank=True,
                                   null=True, related_name='segment_energyComposition')  # Field name made lowercase.
    id_accountant = models.ForeignKey(AccountantArea, models.DO_NOTHING, db_column='ID_ACCOUNTANT', blank=True,
                                      null=True, related_name='accountant_energyComposition')  # Field name made lowercase.
    id_company = models.ForeignKey(Company, models.DO_NOTHING, db_column='ID_COMPANY', blank=True,
                                   null=True, related_name='energyComposition_company')  # Field name made lowercase.
    id_business = models.ForeignKey(Business, models.DO_NOTHING, db_column='ID_BUSINESS', blank=True,
                                    null=True, related_name='business_energyComposition')  # Field name made lowercase.
    composition_name = models.CharField(db_column='COMPOSITION_NAME', unique=True,
                                        max_length=30)  # Field name made lowercase.
    cost_center = models.CharField(db_column='COST_CENTER', max_length=30, blank=True,
                                   null=True)  # Field name made lowercase.
    profit_center = models.CharField(db_column='PROFIT_CENTER', max_length=30, blank=True,
                                     null=True)  # Field name made lowercase.
    kpi_formulae = models.TextField(db_column='KPI_FORMULAE', blank=True,
                                    null=True)  # Field name made lowercase.
    save_date = models.DateTimeField(db_column='SAVE_DATE', blank=True, null=True)  # Field name made lowercase.
    status = models.CharField(db_column='STATUS', max_length=1, blank=True, null=True, default='S')  # Field name made lowercase.
    composition_loss = models.DecimalField(db_column='COMPOSITION_LOSS', max_digits=18,
                                           decimal_places=9, blank=True,
                                           null=True)  # Field name made lowercase. Obs.: 2 decimals in documentation
    description = models.CharField(db_column='DESCRIPTION', max_length=100, blank=True,
                                   null=True)  # Field name made lowercase.
    id_gauge_point_destination = models.ForeignKey(GaugePoint, models.DO_NOTHING, db_column='ID_GAUGE_POINT_DESTINATION',
                                        blank=True, null=True)  # Field name made lowercase.
    id_production_phase = models.ForeignKey(ProductionPhase, models.DO_NOTHING, db_column='ID_PRODUCTION_PHASE',
                                        blank=True, null=True)  # Field name made lowercase.
    data_source = models.CharField(db_column='DATA_SOURCE', max_length=4, blank=True, null=True, default='CCEE')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'ENERGY_COMPOSITION'

class ApportiomentComposition(models.Model):
    id_energy_composition = models.ForeignKey(EnergyComposition, models.DO_NOTHING, db_column='ID_ENERGY_COMPOSITION',
                                    related_name='apport_energy_composition')  # Field name made lowercase.
    id_apport = models.AutoField(db_column='ID_APPORT', primary_key=True)  # Field name made lowercase.
    id_company = models.ForeignKey(Company, models.DO_NOTHING, db_column='ID_COMPANY', blank=True,
                                    null=True,
                                    related_name='comp_energy_composition')  # Field name made lowercase.
    volume_code = models.CharField(db_column='VOLUME_CODE', max_length=10, blank=True,
                                null=True)  # Field name made lowercase.
    cost_code = models.CharField(db_column='COST_CODE', max_length=10, blank=True,
                                null=True)  # Field name made lowercase.
    status = models.CharField(db_column='STATUS', max_length=1, blank=True,
                                null=True,default = 'S')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'APPORTIOMENT_COMPOSITION'

class PointComposition(models.Model):
    id_point_composition = models.AutoField(db_column='ID_POINT_COMPOSITION',
                                            primary_key=True)  # Field name made lowercase.
    id_energy_composition = models.ForeignKey('EnergyComposition', models.DO_NOTHING, db_column='ID_ENERGY_COMPOSITION',
                                              blank=True, null=True,
                                              related_name='point_energy_composition')  # Field name made lowercase.
    id_gauge = models.ForeignKey(GaugePoint, models.DO_NOTHING, db_column='ID_GAUGE', blank=True,
                                 null=True, related_name='point_gauge')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'POINT_COMPOSITION'