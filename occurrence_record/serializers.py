from numbers import Number

from django.forms.models import model_to_dict
from SmartEnergy.utils.deep_get_value import deep_get_value
from typing import Dict
from django.core.validators import MinLengthValidator

from django.utils.functional import empty
from SmartEnergy.settings import MEDIA_URL
from os import path
from SmartEnergy.utils.exception.ErroWithCode import ErrorWithCode
from organization.serializersViews import OrganizationAgrupationEletrictSerializerView
from company.serializersViews import CompanySerializerViewBasicData
from gauge_point.models import GaugePoint, SourcePme, MeterType
from usage_contract.serializers import TypeUsageContractSerializer
from consumption_metering_reports.models import Business, Product
from rest_framework import serializers

from occurrence_record.models import EventType, Event, AppliedProtection, ManualEvent, \
    OccurrenceType, OccurrenceCause, Occurrence, OccurrenceBusiness, OccurrenceProduct, OccurrenceAttachment
from core.serializers import log, generic_update, generic_validation_status, \
    generic_insert_user_and_observation_in_self


class GaugePointSourceMeterTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = MeterType
        fields = '__all__'


class GaugePointSourceSerializer(serializers.ModelSerializer):
    meter_type = GaugePointSourceMeterTypeSerializer(source="id_meter_type")

    class Meta:
        model = SourcePme
        exclude = ['id_meter_type']


class GaugePointSerializer(serializers.ModelSerializer):
    source = GaugePointSourceSerializer(source="id_source")
    company = CompanySerializerViewBasicData(source="id_company")
    electrical_grouping = OrganizationAgrupationEletrictSerializerView(
        source="id_electrical_grouping")
    id_ccee = serializers.IntegerField(source='id_ccee_id')

    class Meta:
        model = GaugePoint
        fields = ('id_gauge', 'id_ccee', 'company', 'participation_sepp', 'gauge_type',
                  'electrical_grouping', 'connection_point',
                  'status', 'source')


class EventTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventType
        fields = '__all__'
        read_only_fields = ['name_event_type']


class EventSerializer(serializers.ModelSerializer):
    occurrence = serializers.IntegerField(
        read_only=True, source='occurrence_id')
    gauge_point = GaugePointSerializer(read_only=True)
    event_type = EventTypeSerializer(read_only=True)
    type_usage_contract = TypeUsageContractSerializer(read_only=True)

    class Meta:
        model = Event
        read_only_fields = [
            'id_occurrence', 'gauge_point', 'event_type',
            'utc_events_begin', 'utc_creation', 'events_duration',
            'events_magnitude', 'type_usage_contract']
        fields = '__all__'

class ManualEventSerializer(serializers.ModelSerializer):
    event_type = EventTypeSerializer(read_only=True)
    
    class Meta:
        model = ManualEvent
        read_only_fields = ['id_occurrence']
        fields = '__all__'


class AppliedProtectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppliedProtection
        fields = '__all__'
        read_only_fields = ['description']


class OccurrenceTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = OccurrenceType
        fields = '__all__'
        read_only_fields = ['description']


class OccurrenceCauseSerializer(serializers.ModelSerializer):
    class Meta:
        model = OccurrenceCause
        fields = '__all__'
        read_only_fields = ['description']


class BusinessSerializer(serializers.ModelSerializer):
    class Meta:
        model = Business
        fields = '__all__'
        read_only_fields = ['description', 'status']


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'
        read_only_fields = ['description']


class OccurrenceProductSerializer(serializers.ModelSerializer):
    product = ProductSerializer()

    class Meta:
        model = OccurrenceProduct
        fields = ['id_occurrence_product', 'product',
                  'lost_production', 'financial_loss', 'status']
        read_only_fields = ['status']


class OccurrenceBusinessSerializer(serializers.ModelSerializer):
    business = BusinessSerializer()

    class Meta:
        model = OccurrenceBusiness
        fields = ['id_occurrence_business', 'business', 'status']
        read_only_fields = ['description', 'status']


class OccurrenceSerializer(serializers.ModelSerializer):
    events = EventSerializer(many=True, read_only=True)
    manual_events = ManualEventSerializer(many=True, read_only=True)
    applied_protection = AppliedProtectionSerializer(read_only=True)
    occurrence_type = OccurrenceTypeSerializer(read_only=True)
    occurrence_cause = OccurrenceCauseSerializer(read_only=True)
    occurrence_business = OccurrenceBusinessSerializer(
        many=True, read_only=True)
    occurrence_duration = serializers.FloatField(
        allow_null=True, required=False, default=None)
    total_stop_time = serializers.FloatField(
        allow_null=True, required=False, default=None)
    occurrence_product = OccurrenceProductSerializer(many=True, read_only=True)
    company = CompanySerializerViewBasicData(read_only=True)
    created_date = serializers.DateTimeField(read_only=True)
    electrical_grouping = OrganizationAgrupationEletrictSerializerView(
        read_only=True)
    additional_information = serializers.CharField(required=False, default=None, allow_null=True, validators=[MinLengthValidator(15)])

    def __init__(self, *args, **kwargs):
        self.user = ""
        self.observation_log = ""
        generic_insert_user_and_observation_in_self(self, **kwargs)
        super().__init__(*args, **kwargs)

    def to_internal_value(self, data: Dict):
        events = data.pop('events', []) or []
        manual_events = data.pop('manual_events', []) or []
        if not isinstance(events, list):
            raise ErrorWithCode.from_error(
                "INCORRECT_FIELD_FORMAT", "Incorrect field format", "/events")
        if not isinstance(manual_events, list):
            raise ErrorWithCode.from_error(
                "INCORRECT_FIELD_FORMAT", "Incorrect field format", "/manual_events")

        self.extra_data = {
            'events': list(map(lambda event: event['id_event'], events)),
            'applied_protection': deep_get_value(data, 'applied_protection.id_applied_protection'),
            'occurrence_type': deep_get_value(data, 'occurrence_type.id_occurrence_type'),
            'occurrence_cause': deep_get_value(data, 'occurrence_cause.id_occurrence_cause'),
            'occurrence_business': deep_get_value(data, 'occurrence_business') or [],
            'occurrence_product': deep_get_value(data, 'occurrence_product') or [],
            'manual_events':  manual_events,
            'company': deep_get_value(data, 'company.id_company'),
            'electrical_grouping': deep_get_value(data, 'electrical_grouping.id_electrical_grouping')
        }
        return super().to_internal_value(data)

    def validate(self, data):
        if data['situation'] == 'consolidate' and not self.extra_data['occurrence_cause']:
            raise serializers.ValidationError(
                {"occurrence_cause": {"id_occurrence_cause": ["id_occurrence_cause empty when situation is consolidate"]}})

        if self.extra_data['occurrence_cause'] == 24:  # others
            if not data.get('additional_information'):
                raise serializers.ValidationError(
                    {"additional_information": ["additional_information empty when occurrence cause is others"]})

        if self.extra_data['occurrence_type'] != 3:
            if not isinstance(data.get('occurrence_duration'), Number):
                raise serializers.ValidationError(
                    {"occurrence_duration": ["occurrence_duration empty when occurrence type is not 'Perturbação'"]})

        if not self.extra_data.get('company'):
            raise serializers.ValidationError(
                {'company': {'id_company': ["company not informed"]}})

        if not self.extra_data.get('electrical_grouping'):
            raise serializers.ValidationError({'electrical_grouping': {
                                              'id_electrical_grouping': ["id_electrical_grouping not informed"]}})

        data['applied_protection_id'] = self.extra_data['applied_protection']
        data['occurrence_type_id'] = self.extra_data['occurrence_type']
        data['occurrence_cause_id'] = self.extra_data['occurrence_cause']
        data['company_id'] = self.extra_data['company']
        data['electrical_grouping_id'] = self.extra_data['electrical_grouping']

        return super().validate(data)

    def __update_manual_event(self, occurrence, manual_event_datas):
        new_registers = list(filter(lambda data: not data.get(
            'id_manual_event'), manual_event_datas))
        update_registers = list(filter(lambda data: data.get(
            'id_manual_event'), manual_event_datas))
        disable_registers = list(occurrence.manual_events.exclude(id_manual_event__in=[
                                 update['id_manual_event'] for update in update_registers]))

        for manual_event_data in new_registers:
            manual_event = ManualEvent.objects.create(**{
                'occurrence': occurrence,
                'gauge_point': manual_event_data.get('gauge_point'),  
                'event_type_id': (manual_event_data.get('event_type') or {}).get('id_event_type'),  
                'date': manual_event_data['date'],  
                'duration': manual_event_data['duration'],  
                'magnitude': manual_event_data['magnitude']
            })
            log(manual_event, manual_event.id_manual_event, {},
                manual_event, self.user, self.observation_log, action="INSERT")

        for manual_event_data in update_registers:
            manual_event_data['occurrence'] = occurrence
            manual_event_data['gauge_point'] = \
                manual_event_data.pop('gauge_point')
            manual_event_data['event_type_id'] = (manual_event_data.pop('event_type', {}) or {}).get('id_event_type')
            generic_update(ManualEvent, manual_event_data['id_manual_event'],
                           manual_event_data, self.user, self.observation_log)

        for to_disable in disable_registers:
            generic_update(ManualEvent, to_disable.id_manual_event,
                           {'status': 'N'}, self.user, self.observation_log)

    def __update_occurrence_business(self, occurrence, occurrence_business_datas):
        new_registers = list(filter(lambda data: not data.get(
            'id_occurrence_business'), occurrence_business_datas))
        update_registers = list(filter(lambda data: data.get(
            'id_occurrence_business'), occurrence_business_datas))
        disable_registers = list(occurrence.occurrence_business.exclude(id_occurrence_business__in=[
                                 update['id_occurrence_business'] for update in update_registers]))

        for occurrence_business_data in new_registers:
            occurrence_business = OccurrenceBusiness.objects.create(**{
                'occurrence': occurrence,
                'business_id': occurrence_business_data['business']['id_business']
            })
            log(occurrence_business, occurrence_business.id_occurrence_business, {},
                occurrence_business, self.user, self.observation_log, action="INSERT")

        for occurrence_business_data in update_registers:
            occurrence_business_data['business_id'] = \
                occurrence_business_data.pop('business')['id_business']
            generic_update(OccurrenceBusiness, occurrence_business_data['id_occurrence_business'],
                           occurrence_business_data, self.user, self.observation_log)

        for to_disable in disable_registers:
            generic_update(OccurrenceBusiness, to_disable.id_occurrence_business,
                           {'status': 'N'}, self.user, self.observation_log)

    def __update_occurrence_product(self, occurrence, occurrence_product_datas):
        new_registers = list(filter(lambda data: not data.get(
            'id_occurrence_product'), occurrence_product_datas))
        update_registers = list(filter(lambda data: data.get(
            'id_occurrence_product'), occurrence_product_datas))
        disable_registers = list(occurrence.occurrence_product.exclude(id_occurrence_product__in=[
                                 update['id_occurrence_product'] for update in update_registers]))

        for occurrence_product_data in new_registers:
            occurrence_product = OccurrenceProduct.objects.create(**{
                'occurrence': occurrence,
                'product_id': occurrence_product_data['product']['id_product'],
                'lost_production': occurrence_product_data['lost_production'],
                'financial_loss': occurrence_product_data['financial_loss']
            })
            log(occurrence_product, occurrence_product.id_occurrence_product, {},
                occurrence_product, self.user, self.observation_log, action="INSERT")

        for occurrence_product_data in update_registers:
            occurrence_product_data['product_id'] = \
                occurrence_product_data.pop('product')['id_product']
            generic_update(OccurrenceProduct, occurrence_product_data['id_occurrence_product'],
                           occurrence_product_data, self.user, self.observation_log)

        for to_disable in disable_registers:
            generic_update(OccurrenceProduct, to_disable.id_occurrence_product,
                           {'status': 'N'}, self.user, self.observation_log)

    def create(self, validated_data):
        occurrence = super().create(validated_data)
        log(occurrence, occurrence.id_occurrence, {}, {**model_to_dict(occurrence), "events": self.extra_data['events']},
            self.user, self.observation_log, action="INSERT")

        events_errors = {}
        for index, event in enumerate(self.extra_data['events']):
            if not event or not Event.objects.filter(pk=event).exists():
                events_errors[str(index)] = {'id_event': ["Event not found"]}
        if events_errors:
            raise serializers.ValidationError({'events': events_errors})

        query_event = Event.objects.filter(pk__in=self.extra_data['events'])

        events_aready_associated = query_event.filter(occurrence__isnull=False)
        if events_aready_associated:
            events_errors = {}
            for event in events_aready_associated:
                events_errors[str(self.extra_data['events'].index(event.id_event))] = {
                    'id_event': ["Event has already been used in another occurrence"]}
            raise serializers.ValidationError({'events': events_errors})

        query_event.update(occurrence=occurrence)

        self.__update_occurrence_business(
            occurrence, self.extra_data['occurrence_business'])
        self.__update_occurrence_product(
            occurrence, self.extra_data['occurrence_product'])
        self.__update_manual_event(occurrence, self.extra_data['manual_events'])

        return occurrence

    def update(self, instance, validated_data):
        if instance.situation == 'consolidate':
            raise ErrorWithCode.from_error(
                "OCCORRENCE_CONSOLIDATED", "Occurrence already consolidated, it`s not possible to make changes", "/situation")
        status_message = generic_validation_status(
            instance.id_occurrence, instance._meta.db_table, {}, self)
        if status_message != 'S' and validated_data['status'] == 'N':
            raise serializers.ValidationError(status_message)

        query_event = Event.objects.filter(occurrence=instance)
        old_events = list(query_event.values_list("id_event", flat=True))
        query_event.update(occurrence=None)
        query_event = Event.objects.filter(pk__in=self.extra_data['events'])

        events_aready_associated = query_event.filter(occurrence__isnull=False)
        if events_aready_associated:
            events_errors = {}
            for event in events_aready_associated:
                events_errors[str(self.extra_data['events'].index(event.id_event))] = {
                    'id_event': ["Event has already been used in another occurrence"]}
            raise serializers.ValidationError({'events': events_errors})

        query_event.update(occurrence=instance)

        occurrence = generic_update(Occurrence, instance.id_occurrence, dict(
            validated_data), self.user, self.observation_log, 
                extra_data_new={"events": self.extra_data['events']}, 
                extra_data_old={"events": old_events})

        self.__update_occurrence_business(
            occurrence, self.extra_data['occurrence_business'])
        self.__update_occurrence_product(
            occurrence, self.extra_data['occurrence_product'])
        self.__update_manual_event(
            occurrence, self.extra_data['manual_events'])

        return occurrence

    class Meta:
        model = Occurrence
        fields = '__all__'


class OccurrenceAttachmentSerializer(serializers.ModelSerializer):
    occurrence = serializers.IntegerField(
        required=True, source='occurrence_id')

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['attachment_path'] = path.join(
            MEDIA_URL, representation['attachment_path'])
        return representation

    def __init__(self, *args, **kwargs):
        generic_insert_user_and_observation_in_self(self, **kwargs)
        super().__init__(*args, **kwargs)

    def create(self, validated_data):
        instance = super().create(validated_data)
        log(instance, instance.id_occurrence_attachment, {},
            instance, self.user, self.observation_log, action="INSERT")
        return instance

    def update(self, instance, validated_data):
        return generic_update(OccurrenceAttachment, instance.id_occurrence_attachment, validated_data, self.user,
                              self.observation_log)

    class Meta:
        model = OccurrenceAttachment
        fields = '__all__'
