from rest_framework import serializers
from agents.models import Agents
from core.models import CceeDescription
from core.serializers import log, generic_update, generic_validation_status, generic_insert_user_and_observation_in_self
from company.serializers import CompanySerializer
from profiles.models import Profile
from company.models import Company

from locales.translates_function import translate_language_error

class AgentsSerializerView(serializers.ModelSerializer):
    company_detail = CompanySerializer(source="id_company", read_only=True)
    status = serializers.CharField(default='S', required=False)

    class Meta:
        model = Agents
        fields = ('id_agents', 'vale_name_agent', 'status', 'company_detail')

class AgentsSerializerBasicView(serializers.ModelSerializer):
    status = serializers.CharField(default='S', required=False)

    class Meta:
        model = Agents
        fields = ('id_agents', 'id_company', 'vale_name_agent', 'status')

class ProfileSerializerView(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ('id_profile', 'id_agents', 'name_profile', 'alpha', 'status', 'encouraged_energy')


class AgentsSerializer(serializers.ModelSerializer):
    company_detail = CompanySerializer(source="id_company", read_only=True)
    profile_detail = ProfileSerializerView(many=True, source="profile_agent", read_only=True)
    status = serializers.CharField(default='S', required=False)

    class Meta:
        model = Agents
        fields = ('id_agents', 'id_company', 'vale_name_agent', 'status', 'company_detail', 'profile_detail')


def validate_status(pk, object, self):
    if object == 'N':
        kwargs = {Profile: 'id_agents'}
        status_message = generic_validation_status(pk, 'Agent', kwargs, self)
        if status_message != 'S':
            raise serializers.ValidationError(status_message)


class CCEESerializerAgents(serializers.ModelSerializer):
    def validate_type(self, dob):
        if dob != 'A/P' and dob:
            raise serializers.ValidationError(translate_language_error('error_ccee_type', self.context['request'])+" A/P")
        return dob
    def validate_code_ccee(self, dob):  # check if ccee code has no duplicate
        if dob is None:
            raise serializers.ValidationError(translate_language_error('error_ccee_not_null', self.context['request']))
        elif int(dob) < 0:
            raise serializers.ValidationError(translate_language_error('error_ccee_not_value_negative', self.context['request']))

        if CceeDescription.objects.filter(code_ccee=dob, type="A/P"):
            ccee = CceeDescription.objects.filter(code_ccee=dob, type="A/P")
            if self.instance:
                if len(ccee) > 0:
                    if ccee[0].pk != self.instance.pk:
                        raise serializers.ValidationError(translate_language_error('error_ccee_exist', self.context['request']))
            else:
                raise serializers.ValidationError(translate_language_error('error_ccee_exist', self.context['request']))
        return dob

    ccee_agent = AgentsSerializer(write_only=False, many=False, read_only=False)
    type = serializers.CharField(default='A/P', required=False)
    status = serializers.CharField(default='S', required=False)

    class Meta:
        model = CceeDescription
        fields = ('id_ccee', 'code_ccee', 'type', 'name_ccee', 'status', 'ccee_agent')

    def __init__(self, *args, **kwargs):
        generic_insert_user_and_observation_in_self(self, **kwargs)
        super(CCEESerializerAgents, self).__init__(*args, **kwargs)

    def create(self, validated_data):
        ccee_agents_data = validated_data.pop('ccee_agent')
        ccee = CceeDescription.objects.create(**validated_data)
        log(CceeDescription, ccee.id_ccee, {}, ccee, self.user, self.observation_log, action="INSERT")
        agent = Agents.objects.create(id_ccee=ccee, **ccee_agents_data)
        log(Agents, agent.id_agents, {}, agent, self.user, self.observation_log, action="INSERT")
        return ccee

    def update(self, instance, validated_data):
        ccee_agent_data = validated_data.pop('ccee_agent')
        agent = instance.ccee_agent
        validate_status(agent.pk, dict(ccee_agent_data)['status'], self)
        obj = generic_update(CceeDescription, instance.id_ccee, dict(validated_data), self.user)
        generic_update(Agents, agent.id_agents, dict(ccee_agent_data), self.user, self.observation_log)
        return obj


class CCEESerializerAgentsBasic(serializers.ModelSerializer):
    class Meta:
        model = CceeDescription
        fields = ('id_ccee', 'code_ccee', 'type', 'name_ccee', 'status')

class CompanySerializerViewFind(serializers.ModelSerializer):
    class Meta:
        fields = ('id_company', 'company_name', 'registered_number', 'type', 'state_number', 'nationality', 'id_sap',
                  'characteristics', 'status', 'create_date')
        model = Company