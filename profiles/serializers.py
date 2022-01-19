from rest_framework import serializers

from agents.models import CceeDescription, Agents
from agents.serializers import AgentsSerializer
from assets.models import Assets
from assets.serializersViews import AssetsSerializerView
from core.serializers import log, generic_update, generic_validation_status, generic_insert_user_and_observation_in_self
from profiles.models import Profile
from locales.translates_function import translate_language_error

def validate_status(pk, object, self):
    if object == 'N':
        kwargs = {Assets: 'id_profile'}
        status_message = generic_validation_status(pk, 'Profile', kwargs, self)
        if status_message != 'S':
            raise serializers.ValidationError(status_message)


class ProfileSerializer(serializers.ModelSerializer):
    status = serializers.CharField(default='S', required=False)
    agents_detail = AgentsSerializer(read_only=True, source='id_agents')
    assets_detail = AssetsSerializerView(read_only=True, many=True, source='assets_profile')

    class Meta:
        model = Profile
        fields = ('id_profile', 'id_agents', 'name_profile', 'alpha', "encouraged_energy", 'status', 'agents_detail', 'assets_detail', 'id_ccee')

    def __init__(self, *args, **kwargs):
        generic_insert_user_and_observation_in_self(self, **kwargs)
        super(ProfileSerializer, self).__init__(*args, **kwargs)

    def create(self, validated_data):
        profile = Profile.objects.create(**validated_data)
        log(Profile, profile.pk, {}, profile, self.user, self.observation_log, action="INSERT")
        return profile

    def update(self, instance, validated_data):
        validate_status(instance.pk, dict(validated_data).get('status'), self)
        return generic_update(Profile, instance.pk, dict(validated_data), self.user, self.observation_log)


class CCEESerializer(serializers.Serializer):
    def validate_type(self, dob):
        if dob != 'A/P' and dob:
            raise serializers.ValidationError(translate_language_error('error_ccee_type', self.context['request'] )+" A/P")
        return dob
    def validate(self, data):
        if data['code_ccee'] < 0:
            raise serializers.ValidationError( translate_language_error('error_ccee_not_value_negative', self.context['request'] ))

        if 'id_ccee' in data:
            if CceeDescription.objects.filter(code_ccee=data['code_ccee'], type="A/P", status="S").exclude(
                    pk=data['id_ccee'] ):
                raise serializers.ValidationError(translate_language_error('error_ccee_exist', self.context['request']))

        else :
            if CceeDescription.objects.filter(code_ccee=data['code_ccee'], type="A/P", status="S").count() > 0:
                raise serializers.ValidationError(translate_language_error('error_ccee_exist', self.context['request']))
        return data

    id_ccee = serializers.IntegerField(required=False, initial=0, allow_null=True)
    code_ccee = serializers.IntegerField(required=True)
    name_ccee=serializers.CharField(required=False)
    type = serializers.CharField(default='A/P', required=False)
    status = serializers.CharField(default='S', required=False)

    class Meta:
        model = CceeDescription
        fields = ('id_ccee', 'code_ccee', 'type', 'name_ccee', 'status')

    def __init__(self, *args, **kwargs):
        generic_insert_user_and_observation_in_self(self, **kwargs)
        super(CCEESerializer, self).__init__(*args, **kwargs)

    def create(self, validated_data):
        ccee = CceeDescription.objects.create(**validated_data)
        log(CceeDescription, ccee.pk, {}, ccee, self.user, self.observation_log, action="INSERT")
        return ccee

    def update(self, instance, validated_data):
        return generic_update(CceeDescription, instance.pk, validated_data, self.user, self.observation_log)

class CCEESerializerProfile(serializers.ModelSerializer):
    profile_ccee = ProfileSerializer(write_only=False, many=False, read_only=False)

    class Meta:
        model = CceeDescription
        fields = ('id_ccee', 'code_ccee', 'type', 'name_ccee', 'status', 'profile_ccee')

##Find Basic
class AgentsSerializerFindBasic(serializers.ModelSerializer):
    status = serializers.CharField(default='S', required=False)
    class Meta:
        model = Agents
        fields = ('id_agents', 'vale_name_agent', 'status')

class ProfileSerializerFindBasic(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ('id_profile', 'id_agents', 'name_profile', 'alpha', 'encouraged_energy', 'status', 'id_ccee')    

class CCEESerializerProfileFindBasic(serializers.ModelSerializer):
    class Meta:
        model = CceeDescription
        fields = ('id_ccee', 'code_ccee', 'type', 'name_ccee', 'status')