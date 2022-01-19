import re
from rest_framework import serializers
from django.conf import settings
from agents.models import Agents
from profiles.models import Profile
from core.serializers import log, generic_update,\
     generic_validation_status, generic_insert_user_and_observation_in_self
from energy_contract.models import EnergyContract, Precification, Flexibilization, FlexibilizationType, Modulation, Seasonal, Guarantee, \
    EnergyProduct, \
    ContractAttachment, Variable, VariableType
from cliq_contract.models import CliqContract
from locales.translates_function import translate_language_error
from datetime import datetime, timezone, timedelta


def validate_status(pk, status, self):
    if status is None:
        return 'S'
    elif status == 'N':
        kwargs = {CliqContract: 'id_contract'}
        status_message = generic_validation_status(pk, 'EnergyContract', kwargs, self)
        if status_message != 'S':
            raise serializers.ValidationError(status_message)
    return status


class AgentsSerializerView(serializers.ModelSerializer):
    class Meta:
        model = Agents
        fields = ('id_agents', 'vale_name_agent')


class ProfileSerializerView(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ('id_profile', 'name_profile')


class EnergyProductSerializerView(serializers.ModelSerializer):
    class Meta:
        model = EnergyProduct
        fields = ('id_energy_product', 'description')


class PrecificationSerializer(serializers.ModelSerializer):
    base_price_mwh = serializers.DecimalField(required=False, default=0, decimal_places=6, max_digits=18, allow_null=True)
    active_price_mwh = serializers.DecimalField(required=False, default=0, decimal_places=6, max_digits=18, allow_null=True)
    base_price_date = serializers.DateTimeField(format="%d/%m/%Y", input_formats=["%d/%m/%Y", ], required=False, allow_null=True)
    birthday_date = serializers.DateTimeField(format="%d/%m/%Y", input_formats=["%d/%m/%Y", ], required=False, allow_null=True)
    last_updated_current_price = serializers.DateTimeField(format="%d/%m/%Y", input_formats=["%d/%m/%Y", ], required=False, allow_null=True)

    class Meta:
        model = Precification
        fields = ('id_contract', 'base_price_mwh', 'base_price_date', 'birthday_date',
                  'id_variable', 'active_price_mwh', 'retusd', 'last_updated_current_price')

    def __init__(self, *args, **kwargs):
        generic_insert_user_and_observation_in_self(self, **kwargs)
        super(PrecificationSerializer, self).__init__(*args, **kwargs)

    def create(self, validated_data):
        precification = Precification.objects.create(**validated_data)
        log(Precification, precification.id_contract_id, {}, precification, self.user, self.observation_log,
            action="INSERT")
        return precification

    def update(self, instance, validated_data):
        return generic_update(Precification, instance.id_contract_id, dict(validated_data), self.user,
                              self.observation_log)

class FlexibilizationTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = FlexibilizationType
        fields = ('id_flexibilization_type', 'flexibilization')

class FlexibilizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Flexibilization
        fields = ('id_contract', 'flexibility_type', 'id_flexibilization_type', 'min_flexibility_pu_offpeak', 
                    'max_flexibility_pu_offpeak', 'min_flexibility_pu_peak', 'max_flexibility_pu_peak',
                    'proinfa_flexibility')

    def __init__(self, *args, **kwargs):
        generic_insert_user_and_observation_in_self(self, **kwargs)
        super(FlexibilizationSerializer, self).__init__(*args, **kwargs)

    def create(self, validated_data):
        instance = super().create(validated_data)
        log(Flexibilization, instance.id_contract_id, {}, instance, self.user, self.observation_log, action="INSERT")
        return instance

    def update(self, instance, validated_data):
        return generic_update(Flexibilization, instance.id_contract_id, validated_data, self.user,
                              self.observation_log)


class ModulationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Modulation
        fields = ('id_contract', 'modulation_type', 'min_modulation_pu', 'max_modulation_pu')

    def __init__(self, *args, **kwargs):
        generic_insert_user_and_observation_in_self(self, **kwargs)
        super(ModulationSerializer, self).__init__(*args, **kwargs)

    def create(self, validated_data):
        instance = super().create(validated_data)
        log(Modulation, instance.id_contract_id, {}, instance, self.user, self.observation_log, action="INSERT")
        return instance

    def update(self, instance, validated_data):
        return generic_update(Modulation, instance.id_contract_id, validated_data, self.user,
                              self.observation_log)


class SeasonalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Seasonal
        fields = ('id_contract', 'type_seasonality', 'season_min_pu', 'season_max_pu')

    def __init__(self, *args, **kwargs):
        generic_insert_user_and_observation_in_self(self, **kwargs)
        super(SeasonalSerializer, self).__init__(*args, **kwargs)

    def create(self, validated_data):
        instance = super().create(validated_data)
        log(Seasonal, instance.id_contract_id, {}, instance, self.user, self.observation_log, action="INSERT")
        return instance

    def update(self, instance, validated_data):
        return generic_update(Seasonal, instance.id_contract_id, validated_data, self.user,
                              self.observation_log)


class GuaranteeSerializer(serializers.ModelSerializer):
    guaranteed_value = serializers.DecimalField(required=False, default=0, decimal_places=6, max_digits=18, allow_null=True)
    emission_date = serializers.DateTimeField(format="%d/%m/%Y", input_formats=["%d/%m/%Y", ], required=False, allow_null=True)
    effective_date = serializers.DateTimeField(format="%d/%m/%Y", input_formats=["%d/%m/%Y", ], required=False, allow_null=True)

    class Meta:
        model = Guarantee
        fields = ('id_contract', 'month_hour', 'guaranteed_value', 'emission_date',
                  'effective_date')

    def __init__(self, *args, **kwargs):
        generic_insert_user_and_observation_in_self(self, **kwargs)
        super(GuaranteeSerializer, self).__init__(*args, **kwargs)

    def create(self, validated_data):
        instance = super().create(validated_data)
        log(Guarantee, instance.id_contract_id, {}, instance, self.user, self.observation_log, action="INSERT")
        return instance

    def update(self, instance, validated_data):
        return generic_update(Guarantee, instance.id_contract_id, validated_data, self.user,
                              self.observation_log)


class EnergyContractSerializerView(serializers.ModelSerializer):
    precif_energy_contract = PrecificationSerializer(write_only=False, many=False, read_only=False)
    flexib_energy_contract = FlexibilizationSerializer(write_only=False, many=False, read_only=False)
    modulation_energy_contract = ModulationSerializer(write_only=False, many=False, read_only=False,
                                                      source='modul_energy_contract')
    season_energy_contract = SeasonalSerializer(write_only=False, many=False, read_only=False)
    guaran_energy_contract = GuaranteeSerializer(write_only=False, many=False, read_only=False)
    modality = serializers.CharField(required=True)
    status = serializers.CharField(default='S', required=False)
    start_supply = serializers.DateTimeField(format="%d/%m/%Y", input_formats=["%d/%m/%Y", ], required=True)
    end_supply = serializers.DateTimeField(format="%d/%m/%Y", input_formats=["%d/%m/%Y", ], required=True)
    signing_data = serializers.DateTimeField(format="%d/%m/%Y", input_formats=["%d/%m/%Y", ], required=False)
    contract_name = serializers.CharField(required=True)
    buyer_agents_detail = AgentsSerializerView(many=False, source='id_buyer_agents', read_only=True)
    seller_agents_detail = AgentsSerializerView(many=False, source='id_seller_agents', read_only=True)
    buyer_profile_detail = ProfileSerializerView(many=False, source='id_buyer_profile', read_only=True)
    seller_profile_detail = ProfileSerializerView(many=False, source='id_seller_profile', read_only=True)
    product = EnergyProductSerializerView(many=False, source='id_energy_product', read_only=True)
    market = serializers.BooleanField(allow_null=True, default=None, required=False)

    class Meta:
        model = EnergyContract
        fields = ('id_contract', 'id_buyer_agents', 'id_seller_agents', 'id_buyer_profile', 'id_seller_profile',
                  'id_energy_product', 'modality', 'sap_contract', 'type', 'start_supply',
                  'end_supply', 'contract_status', 'signing_data', 'volume_mwm', 'volume_mwh', 'contract_name',
                  'status', 'buyer_agents_detail', 'seller_agents_detail', 'buyer_profile_detail',
                  'seller_profile_detail',
                  'product', 'precif_energy_contract', 'flexib_energy_contract', 'modulation_energy_contract',
                  'season_energy_contract', 'guaran_energy_contract', 'market')

    def __init__(self, *args, **kwargs):
        generic_insert_user_and_observation_in_self(self, **kwargs)
        super(EnergyContractSerializerView, self).__init__(*args, **kwargs)


class EnergyContractSerializer(serializers.ModelSerializer):
    def validate_contract_name(self, name):
        if self.instance:
            validateType= (1 if self.instance.contract_name != name else 0)
        else:
            validateType=1

        if validateType==1 :
            valid_name, message_function = function_valid_contract_name(self.context['request'], name)
            if valid_name:
                return name
            else:
                raise serializers.ValidationError( message_function )
        return name            

    modality = serializers.CharField(required=True)
    status = serializers.CharField(default='T', required=False)
    start_supply = serializers.DateTimeField(format="%d/%m/%Y", input_formats=["%d/%m/%Y", ], required=True)
    end_supply = serializers.DateTimeField(format="%d/%m/%Y", input_formats=["%d/%m/%Y", ], required=True)
    signing_data = serializers.DateTimeField(format="%d/%m/%Y", input_formats=["%d/%m/%Y", ], required=False, allow_null=True)
    contract_name = serializers.CharField(required=True)
    buyer_agents_detail = AgentsSerializerView(many=False, source='id_buyer_agents', read_only=True)
    seller_agents_detail = AgentsSerializerView(many=False, source='id_seller_agents', read_only=True)
    buyer_profile_detail = ProfileSerializerView(many=False, source='id_buyer_profile', read_only=True)
    seller_profile_detail = ProfileSerializerView(many=False, source='id_seller_profile', read_only=True)
    product = EnergyProductSerializerView(many=False, source='id_energy_product', read_only=True)
    market = serializers.BooleanField(allow_null=True, default=None, required=False)

    class Meta:
        model = EnergyContract
        fields = ('id_contract', 'id_buyer_agents', 'id_seller_agents', 'id_buyer_profile', 'id_seller_profile',
                  'id_energy_product', 'modality', 'sap_contract', 'type', 'start_supply',
                  'end_supply', 'contract_status', 'signing_data', 'volume_mwm', 'volume_mwh', 'contract_name',
                  'status', 'buyer_agents_detail', 'seller_agents_detail', 'buyer_profile_detail',
                  'seller_profile_detail', 'product', 'market')

    def __init__(self, *args, **kwargs):
        generic_insert_user_and_observation_in_self(self, **kwargs)
        super(EnergyContractSerializer, self).__init__(*args, **kwargs)

    def create(self, validated_data):
        validated_data['status'] = 'T'
        validated_data['temporary_expire_time'] = datetime.now(tz=timezone.utc) + timedelta(days=1)
        energy = EnergyContract.objects.create(**validated_data)
        energy.status = 'S'
        log(EnergyContract, energy.id_contract, {}, energy, self.user, self.observation_log, action="INSERT")
        energy.status = 'T'
        return energy

    def update(self, instance, validated_data):
        validate_status(instance.id_contract, dict(validated_data)['status'], self)
        return generic_update(EnergyContract, instance.id_contract, dict(validated_data), self.user,
                              self.observation_log, dict(validated_data)['status'] != 'T')


class ContractAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContractAttachment
        fields = "__all__"
        extra_kwargs = {field: {"required": True} for field in ["name", "revision", "comments"]}

    def to_representation(self, obj):
        data = super().to_representation(obj)
        path = data['path']
        data['path'] = f'media/{path}'
        return data

    def __init__(self, *args, **kwargs):
        generic_insert_user_and_observation_in_self(self, **kwargs)
        super().__init__(*args, **kwargs)

    def create(self, validated_data):
        instance = super().create(validated_data)
        log(ContractAttachment, instance.id_attachment, {}, instance, self.user, self.observation_log, action="INSERT")
        return instance

    def update(self, instance, validated_data):
        return generic_update(ContractAttachment, instance.id_attachment, validated_data, self.user,
                              self.observation_log)


class VariableTypeSerializerView(serializers.ModelSerializer):
    class Meta:
        model = VariableType
        fields = ('id_variable', 'name')


class VariableSerializerView(serializers.ModelSerializer):
    type_id_variable = VariableTypeSerializerView(many=False)

    class Meta:
        model = Variable
        fields = ('id_variable', 'type_id_variable', 'name')


class EnergyContractSerializerBasicView(serializers.ModelSerializer):
    modality = serializers.CharField(required=True)
    status = serializers.CharField(default='S', required=False)
    start_supply = serializers.DateTimeField(format="%d/%m/%Y", input_formats=["%d/%m/%Y", ], required=True)
    end_supply = serializers.DateTimeField(format="%d/%m/%Y", input_formats=["%d/%m/%Y", ], required=True)
    signing_data = serializers.DateTimeField(format="%d/%m/%Y", input_formats=["%d/%m/%Y", ], required=False)
    contract_name = serializers.CharField(required=True)
    market = serializers.BooleanField(allow_null=True, default=None, required=False)

    class Meta:
        model = EnergyContract
        fields = ('id_contract', 'id_buyer_agents', 'id_seller_agents', 'id_buyer_profile', 'id_seller_profile',
                  'id_energy_product', 'modality', 'sap_contract', 'type', 'start_supply',
                  'end_supply', 'contract_status', 'signing_data', 'volume_mwm', 'volume_mwh', 'contract_name',
                  'status', 'market')

def function_valid_contract_name(request, name):  # if no id returns 0
    # CTE_9,5_JOSE DA SILVA_MARIA_1119_1220_20 -> contract format example (With id)
    # CTE_9,5_JOSE DA SILVA_MARIA_1119_1220 -> contract format example (No id)
    def return_number(self):  # function responsible for removing the final contract number
        valueName = self
        id_contract = ""
        count = 0
        for item in range(len(valueName), 0, -1):  # traverse the string from back to front
            if valueName[item - 1] == "_":  # check if id is over
                if count >= 4: return 0  # if it has passed 3 digits it means that the contract has no id
                break  # if not stop rotating the string and return the id found
            id_contract += valueName[item - 1]
            count += 1
        try:  # tests if the retrieved values ​​are numeric
            int(id_contract)
        except:
            return 0

        id_contract_formatted = ""
        for item in range(len(id_contract), 0, -1):  # inverts id format
            id_contract_formatted += id_contract[item - 1]
        return id_contract_formatted  # Returns formatted contract id

    text = name
    if int(return_number(name)) != 0:  # check if the contractor has id 0
        text = ""
        # remove id from search contract
        for item in range(0, (len(name) - (len(return_number(name)) + 1)), +1):
            text += name[item]
    energy = EnergyContract.objects.filter(contract_name__contains=text)  # whether the contract exists
    value = None
    if energy:  # if this contract_name exists check the last id
        value = 0
        for item in energy:
            number = int(return_number(item.contract_name))
            if value <= number:
                value = number
        if int(return_number(name)) < value and not EnergyContract.objects.filter(contract_name=name):
            #Checks if the id that the user is adding manually is to adjust the sequence of contracts
            return True, {'validate': "False"}

        if int(return_number(name)) <= value: #Checks if the user is trying to add an ID out of sequence (less than the last one)
            return False, {'Error': translate_language_error('error_last_record', request) , 'validate': "True", 'last_Id': value}

    if not value and int(return_number(name)) > 1: 
        #If "VALUE" does not exist it is because there is no contract, so its id is 0. But the user is trying to add a higher id
        return False, {'Error': translate_language_error('error_value_sequential', request), 'validate': "True", 'last_Id': 0}

    elif value and int(return_number(name)) != (value + 1):
        #Checks if the user is trying to add an id out of sequence (Higher than last)
        return False, {'Error': translate_language_error('error_value_sequential', request), 'validate': "True", 'last_Id': value}
    return True, {'validate': "False"}