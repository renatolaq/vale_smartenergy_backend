from rest_framework import serializers

from company.models import Company
from core.models import CceeDescription
from core.serializers import log, generic_update, generic_validation_status, \
    generic_validation_changed, generic_insert_user_and_observation_in_self
from gauge_point.models import GaugePoint, UpstreamMeter, SourcePme, GaugeEnergyDealership,\
    GaugeType, MeterType
from energy_composition.models import PointComposition
from locales.translates_function import translate_language_error, translate_language
from organization.serializersViews import OrganizationAgrupationEletrictSerializerView


class CompanySerializerDealershipView(serializers.ModelSerializer):
    class Meta:
        fields = ('id_company', 'company_name')
        model = Company


class SourcePmeSerializer(serializers.ModelSerializer):
    class Meta:
        model = SourcePme
        fields = ('id_source', 'display_name', 'description', 'id_meter_type')


class GaugePointSerializerView(serializers.ModelSerializer):
    source_detail = SourcePmeSerializer(read_only=True, source='id_source')

    class Meta:
        model = GaugePoint
        fields = ('id_gauge', 'source_detail')


class GaugeEnergyDealershipSerializer(serializers.ModelSerializer):
    company_dealership = CompanySerializerDealershipView(read_only=True, source='id_dealership')
    status = serializers.CharField(default='S', required=False)

    class Meta:
        model = GaugeEnergyDealership
        fields = ('id_gauge_energy_dealership', 'id_dealership', 'status', 'company_dealership')


class UpstreamMeterSerializer(serializers.ModelSerializer):
    def validate(self, data):
        if 'testeUnitario' in self._kwargs['data']:
            if self._kwargs['data']['testeUnitario']=='true':
                raise serializers.ValidationError("Erro para teste unitario" ) 
        return data

    gaugedad = GaugePointSerializerView(read_only=True, source='id_upstream_meter')
    gaugechield = GaugePointSerializerView(read_only=True, source='id_gauge')
    status = serializers.CharField(default='S', required=False)

    class Meta:
        model = UpstreamMeter
        fields = ('id_upstream', 'id_upstream_meter', 'id_gauge', 'status',
                  'gaugedad', 'gaugechield')

    def __init__(self, *args, **kwargs):
        generic_insert_user_and_observation_in_self(self, **kwargs)
        super(UpstreamMeterSerializer, self).__init__(*args, **kwargs)

    def create(self, validated_data):
        upstream = UpstreamMeter.objects.create(**validated_data)
        log(UpstreamMeter, upstream.id_upstream, {}, upstream, self.user, self.observation_log, action="INSERT")
        return upstream

    def update(self, instance, validated_data):
        obj = generic_update(UpstreamMeter, instance.id_upstream, dict(validated_data), self.user, self.observation_log)
        return obj

class CCEESerializer(serializers.ModelSerializer):
    type = serializers.CharField(default='METER', required=False)
    status = serializers.CharField(default='S', required=False)
    code_ccee = serializers.CharField(allow_blank=True)

    def validate_type(self, dob):
        if dob != 'METER' and dob:
            raise serializers.ValidationError( translate_language_error('error_ccee_type', self.context['request'])+" METER")
        return dob

    def validate_code_ccee(self, dob):  # check if ccee code has no duplicate
        if (dob!="" and dob!=None) and CceeDescription.objects.filter(code_ccee=dob, type="METER", status='S'):
            ccee = CceeDescription.objects.filter(code_ccee=dob, type="METER", status='S')
            if self.instance:
                if len(ccee) > 0:
                    if ccee[0].pk != self.instance.pk:
                        raise serializers.ValidationError( translate_language_error('error_ccee_exist', self.context['request']) )
            else:
                raise serializers.ValidationError( translate_language_error('error_ccee_exist', self.context['request']) )
        return dob    
    
    class Meta:
        model = CceeDescription
        fields = ('id_ccee', 'code_ccee', 'type', 'name_ccee', 'status')

    def __init__(self, *args, **kwargs):
        generic_insert_user_and_observation_in_self(self, **kwargs)
        super(CCEESerializer, self).__init__(*args, **kwargs)

    def create(self, validated_data):
        ccee = CceeDescription.objects.create(**validated_data)
        log(CceeDescription, ccee.id_ccee, {}, ccee, self.user, self.observation_log, action="INSERT")
        return ccee

    def update(self, instance, validated_data):
        obj = generic_update(CceeDescription, instance.id_ccee, dict(validated_data), self.user, self.observation_log)
        return obj


def validate_status(pk, status, self):
    if status is None:
        return 'S'
    elif status == 'N':
        kwargs = {UpstreamMeter: 'id_gauge', PointComposition: 'id_gauge', UpstreamMeter:'id_upstream_meter'}
        status_message = generic_validation_status(pk, 'GaugePoint', kwargs, self)
        if status_message != 'S':
            raise serializers.ValidationError(status_message)
    return status

def validate_gauge_type(pk, gauge_type, self):
    if gauge_type != GaugePoint.objects.get(pk=pk).id_gauge_type:
        kwargs = {UpstreamMeter: 'id_gauge', PointComposition: 'id_gauge', UpstreamMeter:'id_upstream_meter'}
        status_message=generic_validation_changed(pk, GaugePoint, kwargs, self.context['request'])
        if status_message != 'S':
            raise serializers.ValidationError(status_message)
    return gauge_type


class GaugePointSerializer(serializers.ModelSerializer): #OS22
    
    def validate(self, data):
            #validators source
        if not data['id_source']:
            raise serializers.ValidationError(translate_language_error('error_source_requerid', self.context['request']) )
        if GaugePoint.objects.filter(id_source=data['id_source'].pk):
            gauge = GaugePoint.objects.filter(id_source=data['id_source'].pk)
            if gauge[0].pk != self.instance.pk:
                raise serializers.ValidationError(translate_language_error('error_source_not_unique', self.context['request']) )

            #validators electrical_grouping
        meter_type_source = int(SourcePme.objects.get(pk=data['id_source'].pk).id_meter_type_id)
        if (meter_type_source != 1 or data['participation_sepp']!='S') and data['id_electrical_grouping'] not in [None, ""]:
            raise serializers.ValidationError(translate_language_error('error_disabled_id_electrical_grouping', self.context['request']) )
        elif  meter_type_source==1 and data['participation_sepp']=='S' and data['id_electrical_grouping'] in [None, ""]:
            raise serializers.ValidationError(translate_language_error('error_required_id_electrical_grouping', self.context['request']) )

            #validators participation_sepp
        if (data['id_gauge_type'].pk not in [1,2] or meter_type_source !=1) and data['participation_sepp']!='N':
            raise serializers.ValidationError(translate_language_error('error_invalid_participation_sepp', self.context['request']) )
        
            #validators gauge_dealership
        if (data['id_gauge_type'].pk!=1 or meter_type_source!=1) and data['gauge_dealership']['id_dealership']:
            raise serializers.ValidationError(translate_language_error('error_disable_gauge_dealership', self.context['request']) )
        elif (data['id_gauge_type'].pk==1 and meter_type_source==1) and data['gauge_dealership']['id_dealership'] is None:
            raise serializers.ValidationError(translate_language_error('error_required_gauge_dealership', self.context['request']) )
        
        return data

    gauge_type = serializers.CharField(required=True)
    gauge_dealership = GaugeEnergyDealershipSerializer(write_only=False, many=False, read_only=False)
    connection_point = serializers.CharField(max_length=150, allow_blank=True)
    participation_sepp = serializers.CharField(default='N')
    status = serializers.CharField(default='S', required=False)

    class Meta:
        model = GaugePoint
        fields = ('id_gauge', 'id_ccee', 'id_source', 'id_company', 'participation_sepp', 'gauge_type',
            'id_gauge_type', 'id_electrical_grouping', 'connection_point', 
            'status','gauge_dealership')

    def __init__(self, *args, **kwargs):
        generic_insert_user_and_observation_in_self(self, **kwargs)
        super(GaugePointSerializer, self).__init__(*args, **kwargs)

    def create(self, validated_data):
        gauge_dealership_data = validated_data.pop('gauge_dealership')
        gauge = GaugePoint.objects.create(**validated_data)
        log(GaugePoint, gauge.id_gauge, {}, gauge, self.user, self.observation_log, action="INSERT")
        gauge_dealership = GaugeEnergyDealership.objects.create(id_gauge_point=gauge,
                                                                id_dealership=gauge_dealership_data['id_dealership'],
                                                                status="S")
        log(GaugeEnergyDealership, gauge_dealership.id_gauge_energy_dealership, {}, gauge_dealership,
                self.user, self.observation_log, action="INSERT")

        return gauge

    def update(self, instance, validated_data):
        gauge_dealership_data = validated_data.pop('gauge_dealership')
        validate_status(instance.id_gauge, dict(validated_data)['status'], self)
        validate_gauge_type(instance.id_gauge, dict(validated_data)['id_gauge_type'], self)
        obj = generic_update(GaugePoint, instance.id_gauge, dict(validated_data), self.user, self.observation_log)
        gauge_dealership = GaugeEnergyDealership.objects.get(id_gauge_point_id=instance.id_gauge)
        generic_update(GaugeEnergyDealership, gauge_dealership.id_gauge_energy_dealership, dict(gauge_dealership_data),
                        self.user, self.observation_log)
        return obj


class GaugeCompanyView(serializers.ModelSerializer):
    company = CompanySerializerDealershipView(source="id_company", read_only=True)

    class Meta:
        model = GaugePoint
        fields = ('id_company', 'company')


#FindBasic
class GaugePointSerializerFindBasic(serializers.ModelSerializer):
    status = serializers.CharField(default='S', required=False)

    class Meta:
        model = GaugePoint
        fields = ('id_gauge', 'id_ccee', 'id_source', 'id_company', 'participation_sepp', 'gauge_type', 'status',
                'id_gauge_type', 'id_electrical_grouping', 'connection_point')

class GaugeEnergyDealershipSerializerFindBasic(serializers.ModelSerializer):
    status = serializers.CharField(default='S', required=False)

    class Meta:
        model = GaugeEnergyDealership
        fields = ('id_gauge_energy_dealership', 'id_dealership', 'status')

class UpstreamMeterSerializerFindBasic(serializers.ModelSerializer):
    status = serializers.CharField(default='S', required=False)

    class Meta:
        model = UpstreamMeter
        fields = ('id_upstream', 'id_upstream_meter', 'id_gauge', 'status')


class CCEESerializerFindBasic(serializers.ModelSerializer):
    type = serializers.CharField(default='METER', required=False)
    status = serializers.CharField(default='S', required=False)
    code_ccee = serializers.CharField(allow_blank=True)
    class Meta:
        model = CceeDescription
        fields = ('id_ccee', 'code_ccee', 'type', 'name_ccee', 'status')


class GaugeTypeSerializer(serializers.ModelSerializer):
    def to_representation(self, data):
        data = super().to_representation(data)
        if self._context:
            data['description']=translate_language(data['description'], (self._context._request) if self._context._request else (self._context)) 
        else:
            data['description']=translate_language(data['description'], self.parent._context['request'])
        return data
    class Meta:
        model = GaugeType
        fields = '__all__'

class MeterTypeSerializer(serializers.ModelSerializer):
    def to_representation(self, data):
        data = super().to_representation(data)
        if self._context:
            data['description']=translate_language(data['description'], (self._context._request) if self._context._request else (self._context)) 
        else:
            data['description']=translate_language(data['description'], self.parent._context['request'])
        return data

    class Meta:
        model = MeterType
        fields = '__all__'


class GaugePointSerializerViewDetail(serializers.ModelSerializer): #OS22
    gauge_dealership = GaugeEnergyDealershipSerializer(write_only=False, many=False, read_only=False)
    company_detail = CompanySerializerDealershipView(read_only=True, source='id_company')
    source_detail = SourcePmeSerializer(read_only=True, source='id_source')
    ccee_gauge = CCEESerializer(read_only=True, source='id_ccee')
    upstream = UpstreamMeterSerializer(read_only=True, many=True, source='gauge_chield')

    gauge_type_detail = GaugeTypeSerializer(read_only=False, source="id_gauge_type")
    electrical_grouping_detail =OrganizationAgrupationEletrictSerializerView(read_only=True, source="id_electrical_grouping")
    status = serializers.CharField(default='S', required=False)

    class Meta:
        model = GaugePoint
        fields = ('id_gauge', 'id_ccee', 'id_source', 'id_company', 'participation_sepp', 'gauge_type',
                'id_gauge_type', 'id_electrical_grouping', 'connection_point', 
                'gauge_type_detail', 'electrical_grouping_detail',
                'status', 'gauge_dealership', 'upstream', 'company_detail',
                'source_detail', 'ccee_gauge')