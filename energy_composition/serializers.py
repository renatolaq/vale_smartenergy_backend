import json
from datetime import timezone, datetime

from django.core.serializers.json import DjangoJSONEncoder
from rest_framework import serializers
from core.serializers import log, generic_update, generic_validation_status, generic_insert_user_and_observation_in_self
from energy_composition.models import EnergyComposition, AccountantArea, DirectorBoard, Segment, Business, \
    ApportiomentComposition, PointComposition
from company.serializersViews import CompanySerializerView
from assets.models import AssetsComposition
from gauge_point.serializers import GaugePointSerializer, GaugePointSerializerFindBasic, SourcePmeSerializer
from locales.translates_function import translate_language_error
from core.views import insert_virtual_meter, update_virtual_meter


class DirectorBoardSerializerView(serializers.ModelSerializer):
    class Meta:
        model = DirectorBoard
        fields = ('id_director', 'description', 'status')


class SegmentSerializerView(serializers.ModelSerializer):
    class Meta:
        model = Segment
        fields = ('id_segment', 'description', 'status')


class AccountantSerializerAreaView(serializers.ModelSerializer):
    class Meta:
        model = AccountantArea
        fields = ('id_accountant', 'description', 'status')


class BusinessSerializerView(serializers.ModelSerializer):
    class Meta:
        model = Business
        fields = ('id_business', 'description', 'status')


class PointCompositionSerializer(serializers.ModelSerializer):
    id_point_composition = serializers.IntegerField(required=False, allow_null=True)
    gauge_point = GaugePointSerializer(source="id_gauge", read_only=True)
    class Meta:
        model = PointComposition
        fields = ('id_point_composition', 'id_energy_composition', 'id_gauge', 'gauge_point')


class ApportiomentCompositionSerializer(serializers.ModelSerializer):
    id_apport = serializers.IntegerField(required=False, allow_null=True)
    company_detail = CompanySerializerView(many=False, source='id_company', read_only=True)
    status = serializers.CharField(default='S', required=False)

    class Meta:
        model = ApportiomentComposition
        fields = ('id_energy_composition', 'id_apport', 'id_company', 'volume_code',
                  'cost_code', 'status', 'company_detail')
        read_only_fields = ('id_energy_composition', 'id_apport')


def validate_status(pk, status, self):
    if status is None:
        return 'S'
    elif status == 'N':
        kwargs = {ApportiomentComposition: 'id_energy_composition', PointComposition: 'id_energy_composition', AssetsComposition: 'id_energy_composition'}
        status_message = generic_validation_status(pk, 'EnergyComposition', kwargs, self)
        if status_message != 'S':
            raise serializers.ValidationError(status_message)
    return status


class EnergyCompositionSerializer(serializers.ModelSerializer):
    composition_name = serializers.CharField(required=True, max_length=30)
    point_energy_composition = PointCompositionSerializer(allow_null=True, many=True, read_only=False, write_only=False)
    apport_energy_composition = ApportiomentCompositionSerializer(allow_null=True, write_only=False, many=True, read_only=False)
    director = DirectorBoardSerializerView(allow_null=True, source="id_director", read_only=True)
    segment = SegmentSerializerView(allow_null=True, source="id_segment", read_only=True)
    company = CompanySerializerView(source="id_company", read_only=True)
    accountantarea = AccountantSerializerAreaView(allow_null=True, source="id_accountant", read_only=True)
    business = BusinessSerializerView(allow_null=True, source="id_business", read_only=True)
    composition_loss = serializers.DecimalField(max_digits=18, decimal_places=9, allow_null=True)
    gauge_point_destination_details = GaugePointSerializerFindBasic(source="id_gauge_point_destination", read_only=True)

    def validate_composition_name(self, dob):  # check if compostion name has no duplicate
        composition_name = EnergyComposition.objects.filter(composition_name=dob)
        if EnergyComposition.objects.filter(composition_name=dob):
            composition_name = EnergyComposition.objects.filter(composition_name=dob)
            if self.instance:
                if composition_name[0].pk != self.instance.pk:
                    raise serializers.ValidationError(translate_language_error('error_composition_name_exist', self.context['request'] ) )
            else:
                raise serializers.ValidationError(translate_language_error('error_composition_name_exist', self.context['request'] ) )
        return dob

    def validate_save_date(self, dob):
        return datetime.now(tz=timezone.utc)

    def to_representation(self, instance):
        apport = []
        for a in ApportiomentComposition.objects.filter(id_energy_composition=instance.id_energy_composition,status='S'):
            try:
                apport.append({
                    'id_apport': a.id_apport,
                    'id_company': a.id_company.id_company,
                    'company_name': a.id_company.company_name,
                    'volume_code': a.volume_code,
                    'cost_code': a.cost_code,
                    'status': a.status
                })
            except:
                pass
        point_composition = []
        for a in PointComposition.objects.filter(id_energy_composition=instance.id_energy_composition):
            try:
                point_composition.append({'id_point_composition': a.id_point_composition, 'id_gauge': a.id_gauge_id, 'display_name': a.id_gauge.id_source.display_name})
            except:
                pass
        
        obj_gauge_destination={}
        if instance.id_gauge_point_destination:
            obj_gauge_destination = GaugePointSerializerFindBasic(instance.id_gauge_point_destination, many=False, context=self).data
            obj_gauge_destination['source_details'] = SourcePmeSerializer(instance.id_gauge_point_destination.id_source, many=False, context=self).data
            obj_gauge_destination['display_name']=instance.id_gauge_point_destination.id_source.display_name

        return {
            'id_energy_composition': instance.id_energy_composition,
            "composition_name": instance.composition_name,
            "cost_center": instance.cost_center,
            "profit_center": instance.profit_center,
            "kpi_formulae": instance.kpi_formulae,
            "status": instance.status,
            "save_date": instance.save_date,
            "composition_loss": instance.composition_loss,
            "description": instance.description,
            "id_company": instance.id_company.id_company,
            "id_accountant": instance.id_accountant and instance.id_accountant.id_accountant,
            "id_director": instance.id_director and instance.id_director.id_director,
            "id_segment": instance.id_segment and instance.id_segment.id_segment,
            "id_business": instance.id_business and instance.id_business.id_business,
            'id_production_phase': instance.id_production_phase and instance.id_production_phase.id_production_phase,
            "energy_detail": {
                "id_company": instance.id_company.id_company,
                'company_name': instance.id_company.company_name,
                "id_accountant": instance.id_accountant and instance.id_accountant.id_accountant,
                'accountantarea': instance.id_accountant and instance.id_accountant.description,
                "id_director": instance.id_director and instance.id_director.id_director,
                'director': instance.id_director and instance.id_director.description,
                "id_segment": instance.id_segment and instance.id_segment.id_segment,
                'segment': instance.id_segment and instance.id_segment.description,
                "id_business": instance.id_business and instance.id_business.id_business,
                'business': instance.id_business and instance.id_business.description,
                'id_production_phase': instance.id_production_phase and instance.id_production_phase.id_production_phase,
                'production_phase': instance.id_production_phase and instance.id_production_phase.description,
            },
            'apport_energy_composition': apport,
            'point_energy_composition': point_composition,
            'id_gauge_point_destination': instance.id_gauge_point_destination_id,
            'gauge_point_destination': obj_gauge_destination,
            'data_source': instance.data_source,
        }

    class Meta:
        model = EnergyComposition
        
        fields = ('id_energy_composition', 'composition_name', 'cost_center', 'profit_center', 'kpi_formulae',
                  'status', 'save_date', 'composition_loss', 'id_company', 'id_business', 'id_director',
                  'id_segment', 'id_accountant', 'description', 'point_energy_composition', 'apport_energy_composition',
                  'business', 'accountantarea', 'company', 'segment', 'director', 'id_gauge_point_destination', 'gauge_point_destination_details', "id_production_phase", "data_source")
                         
    def __init__(self, *args, **kwargs):
        generic_insert_user_and_observation_in_self(self, **kwargs)
        super(EnergyCompositionSerializer, self).__init__(*args, **kwargs)

    def create(self, validated_data):
        apport_data = validated_data.pop('apport_energy_composition', [])
        point_composition = validated_data.pop('point_energy_composition', [])
        energy_composition = EnergyComposition.objects.create(**validated_data)
        log(EnergyComposition, energy_composition.id_energy_composition, {}, energy_composition, self.user,
            self.observation_log, action="INSERT")

        for data in apport_data:
            apport = ApportiomentComposition.objects.create(id_energy_composition=energy_composition,
                                                            **data)
            log(ApportiomentComposition, apport.id_apport, {}, apport, self.user,
                self.observation_log, action="INSERT")

        for data in point_composition:
            pointcomposition = PointComposition.objects.create(id_energy_composition=energy_composition,
                                                               **data)
            log(PointComposition, pointcomposition.id_point_composition, {}, pointcomposition, self.user,
                self.observation_log, action="INSERT")

        id_energy_composition = energy_composition.id_energy_composition
        kpi_formulae = energy_composition.kpi_formulae
        id_destination = energy_composition.id_gauge_point_destination_id
        insert_virtual_meter(kpi_formulae, id_destination, id_energy_composition)

        return energy_composition

    def update(self, instance, validated_data):
        apport_data = validated_data.pop('apport_energy_composition')
        point_composition = validated_data.pop('point_energy_composition')
        validate_status(instance.id_energy_composition, dict(validated_data)['status'], self)
        obj = generic_update(EnergyComposition, instance.id_energy_composition, validated_data, self.user,
                             self.observation_log)
        energy_composition = EnergyComposition.objects.get(pk=instance.id_energy_composition)

        for data in apport_data:
            if data.get('id_apport'):
                generic_update(ApportiomentComposition, data.get('id_apport'), dict(data), self.user,
                               self.observation_log)
            else:
                apport = ApportiomentComposition.objects.create(id_energy_composition=energy_composition,
                                                                **data)
                log(ApportiomentComposition, apport.id_apport, {}, apport, self.user,
                    self.observation_log, action="INSERT")

        for data in point_composition:
            if data.get('id_point_composition'):
                generic_update(PointComposition, data.get('id_point_composition'), dict(data), self.user,
                               self.observation_log)
            else:
                point = PointComposition.objects.create(id_energy_composition=energy_composition,
                                                        **data)
                log(PointComposition, point.id_point_composition, {}, point, self.user,
                    self.observation_log, action="INSERT")

        id_energy_composition = energy_composition.id_energy_composition
        kpi_formulae = energy_composition.kpi_formulae
        id_destination = energy_composition.id_gauge_point_destination_id
        update_virtual_meter(kpi_formulae, id_destination, id_energy_composition)

        return obj


class EnergyCompositionSerializerViewBasic(serializers.ModelSerializer):
    composition_name = serializers.CharField(required=True, max_length=30)
    composition_loss = serializers.DecimalField(max_digits=18, decimal_places=9, allow_null=True)
    class Meta:
        model = EnergyComposition
        
        fields = ('id_energy_composition', 'composition_name', 'cost_center', 'profit_center', 'kpi_formulae',
                  'status', 'save_date', 'composition_loss', 'id_company', 'id_business', 'id_director',
                  'id_segment', 'id_accountant', 'description', 'id_gauge_point_destination', "id_production_phase", "data_source")

class PointCompositionSerializerViewBasic(serializers.ModelSerializer):
    class Meta:
        model = PointComposition
        fields = ('id_point_composition', 'id_energy_composition', 'id_gauge')

class ApportiomentCompositionSerializerViewBasic(serializers.ModelSerializer):
    id_apport = serializers.IntegerField(required=False, allow_null=True)
    status = serializers.CharField(default='S', required=False)

    class Meta:
        model = ApportiomentComposition
        fields = ('id_energy_composition', 'id_apport', 'id_company', 'volume_code',
                  'cost_code', 'status')