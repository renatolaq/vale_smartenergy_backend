from company.models import Company
from django.utils import timezone
from django.db import models
from organization.models import Business, ElectricalGrouping, Product
from gauge_point.models import GaugePoint
from usage_contract.models import TypeUsageContract

class Occurrence(models.Model):
    id_occurrence = models.AutoField(db_column='ID_OCCURRENCE', primary_key=True)  
    applied_protection = models.ForeignKey('AppliedProtection', models.DO_NOTHING, db_column='ID_PROTECTION_APPLIED', null=True)
    occurrence_type = models.ForeignKey('OccurrenceType', models.DO_NOTHING, db_column='ID_OCCURRENCE_TYPE', null=False)
    occurrence_cause = models.ForeignKey('OccurrenceCause', models.DO_NOTHING, db_column='ID_OCCURRENCE_CAUSE', null=True)
    additional_information = models.CharField(db_column='ADDITIONAL_INFORMATION', null=True, blank=False, max_length=100)
    company = models.ForeignKey(Company, models.DO_NOTHING, db_column='ID_COMPANY', null=False)
    electrical_grouping = models.ForeignKey(ElectricalGrouping, models.DO_NOTHING, db_column='ID_ELECTRICAL_GROUPING', null=False)
    responsible = models.CharField(db_column='RESPONSIBLE', max_length=100, null=False)
    phone = models.CharField(db_column='PHONE', max_length=30, blank=True, null=True)
    cellphone = models.CharField(db_column='CELLPHONE', max_length=30, blank=True, null=True)  
    carrier = models.CharField(db_column='CARRIER', max_length=4, blank=True, null=True)  
    occurrence_date = models.DateTimeField(db_column='OCCURRENCE_DATE', null=False)  
    occurrence_duration = models.IntegerField(db_column='OCCURRENCE_DURATION', null=True)  
    key_circuit_breaker_identifier = models.CharField(db_column='KEY_CIRCUIT_BREAKER_IDENTIFIER', max_length=100, blank=True, null=True)  
    total_stop_time = models.IntegerField(db_column='TOTAL_STOP_TIME', null=True)  
    description = models.CharField(db_column='DESCRIPTION', max_length=1000, null=False)  
    created_date = models.DateTimeField(db_column='CREATED_DATE', null=False, default=timezone.now)  
    status = models.CharField(db_column='STATUS', max_length=1, null=False)  
    situation = models.CharField(db_column='SITUATION', max_length=15, null=False) 

    class Meta:
        managed = False
        db_table = 'OCCURRENCE'

class AppliedProtection(models.Model):
    id_applied_protection = models.IntegerField(db_column='ID_PROTECTION_APPLIED', primary_key=True)  
    description = models.CharField(db_column='DESCRIPTION', max_length=50)  

    class Meta:
        managed = False
        db_table = 'PROTECTION_APPLIED'

class OccurrenceType(models.Model):
    id_occurrence_type = models.IntegerField(db_column='ID_OCCURRENCE_TYPE', primary_key=True)  
    description = models.CharField(db_column='DESCRIPTION', max_length=50)  

    class Meta:
        managed = False
        db_table = 'OCCURRENCE_TYPE'

class OccurrenceCause(models.Model):
    id_occurrence_cause = models.IntegerField(db_column='ID_OCCURRENCE_CAUSE', primary_key=True)  
    description = models.CharField(db_column='DESCRIPTION', max_length=100)  

    class Meta:
        managed = False
        db_table = 'OCCURRENCE_CAUSE'

class OccurrenceBusiness(models.Model):
    id_occurrence_business = models.AutoField(db_column='ID_OCCURRENCE_BUSINESS', primary_key=True)  
    occurrence = models.ForeignKey('Occurrence', models.DO_NOTHING, db_column='ID_OCCURRENCE', related_name='occurrence_business', null=False)  
    business = models.ForeignKey(Business, models.DO_NOTHING, db_column='ID_BUSINESS', related_name='business_occurrenceBusiness', null=False)  
    status = models.CharField(db_column='STATUS', max_length=1, null=False, blank=False, default='S')  

    class Meta:
        managed = False
        db_table = 'OCCURRENCE_BUSINESS'

class OccurrenceProduct(models.Model):
    id_occurrence_product = models.AutoField(db_column='ID_OCCURRENCE_PRODUCT', primary_key=True)  
    occurrence = models.ForeignKey('Occurrence', models.DO_NOTHING, db_column='ID_OCCURRENCE', related_name='occurrence_product', null=False)  
    product = models.ForeignKey(Product, models.DO_NOTHING, db_column='ID_PRODUCT', related_name='product_occurrenceProduct', null=False)  
    lost_production = models.DecimalField(db_column='LOST_PRODUCTION', null=False, max_digits=18, decimal_places=9)  
    financial_loss = models.DecimalField(db_column='FINANCIAL_LOSS', null=False, max_digits=18, decimal_places=9)  
    status = models.CharField(db_column='STATUS', max_length=1, null=False, blank=False, default='S')  

    class Meta:
        managed = False
        db_table = 'OCCURRENCE_PRODUCT'

class OccurrenceAttachment(models.Model):
    id_occurrence_attachment = models.AutoField(db_column='ID_OCCURRENCE_ATTACHMENT', primary_key=True)  
    occurrence = models.ForeignKey('Occurrence', models.DO_NOTHING, db_column='ID_OCCURRENCE')  
    attachment_name = models.CharField(db_column='ATTACHMENT_NAME', max_length=100, blank=False, null=False)  
    attachment_revision = models.CharField(db_column='ATTACHMENT_REVISION', max_length=10, blank=False, null=False)  
    attachment_comments = models.CharField(db_column='ATTACHMENT_COMMENTS', max_length=100, blank=False, null=False)  
    attachment_path = models.CharField(db_column='ATTACHMENT_PATH', max_length=100, blank=False, null=False)  

    class Meta:
        managed = False
        db_table = 'OCCURRENCE_ATTACHMENT'

class EventType(models.Model):
    id_event_type = models.AutoField(db_column='ID_EVENT_TYPE', primary_key=True)  
    name_event_type = models.CharField(db_column='NAME_EVENT_TYPE', max_length=100, blank=True, null=True)  

    class Meta:
        managed = False
        db_table = 'EVENT_TYPE'

class Event(models.Model):
    id_event = models.IntegerField(db_column='ID_EVENT', primary_key=True)  
    occurrence = models.ForeignKey(Occurrence, models.DO_NOTHING, db_column='ID_OCCURRENCE', related_name='events', null=True)  
    gauge_point = models.ForeignKey(GaugePoint, models.DO_NOTHING, db_column='ID_GAUGE_POINT', blank=True, null=True, related_name='gaugePoint_pqEvents')  
    event_type = models.ForeignKey(EventType, models.DO_NOTHING, db_column='ID_EVENT_TYPE', blank=True, null=True)  
    utc_events_begin = models.DateTimeField(db_column='UTC_EVENTS_BEGIN', blank=True, null=True)  
    utc_creation = models.DateTimeField(db_column='UTC_CREATION', blank=True, null=True)  
    events_duration = models.FloatField(db_column='EVENTS_DURATION', blank=True, null=True)  
    events_magnitude = models.FloatField(db_column='EVENTS_MAGNITUDE', blank=True, null=True)  
    type_usage_contract = models.ForeignKey(TypeUsageContract, models.DO_NOTHING, db_column='ID_USAGE_CONTRACT_TYPE', blank=True, null=True, )  

    class Meta:
        managed = False
        db_table = 'PQ_EVENTS'

class ManualEvent(models.Model):
    id_manual_event = models.AutoField(db_column='ID_EVENT_MANUAL', primary_key=True)  
    occurrence = models.ForeignKey(Occurrence, models.DO_NOTHING, db_column='ID_OCCURRENCE', related_name='manual_events', null=True)  
    gauge_point = models.CharField(db_column='GAUGE_NAME', max_length=100, blank=True, null=True)  
    event_type = models.ForeignKey(EventType, models.DO_NOTHING, db_column='ID_EVENT_TYPE', blank=True, null=True)  
    date = models.DateTimeField(db_column='UTC_EVENTS_BEGIN', blank=True, null=True)  
    duration = models.FloatField(db_column='EVENTS_DURATION', blank=True, null=True)  
    magnitude = models.FloatField(db_column='EVENTS_MAGNITUDE', blank=True, null=True)
    status = models.CharField(db_column='STATUS', max_length=1, null=False, blank=False, default='S')  

    class Meta:
        managed = False
        db_table = 'PQ_EVENTS_MANUAL'