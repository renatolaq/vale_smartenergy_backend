from cliq_contract.models import CliqContract, SeasonalityCliq, Seasonality
from core.models import Seasonality, CceeDescription
from core.serializers import log, generic_update, generic_insert_user_and_observation_in_self
from rest_framework import serializers
from locales.translates_function import translate_language_error
from energy_contract.models import EnergyContract
from datetime import date

# class JSONSerializer(serializers.Field):
#     def _init_(self, read_only=False, write_only=False, required=None, default=serializers.empty, 
#         initial=serializers.empty, source=None, label=None, help_text=None, style=None, error_messages=None, validators=None, allow_null=False):
#         super()._init_(read_only=read_only, write_only=write_only, required=required, default=default, initial=initial, source="*",
#                          label=label, help_text=help_text, style=style, error_messages=error_messages, validators=validators, allow_null=allow_null)
#         self.__local_field = source

#     def to_representation(self, obj):
#         if(self.__local_field is None):
#             self.__local_field = self.field_name
#         #Pegar obj e converter para JSON, pois ao ler do banco ele pega o dado como String, então converter para dicionário (pesquisar net)
        
#         return obj

#     def to_internal_value(self, data):
#         #neste caso, ao contrário, converter dicionario para JSON Text
#         return {
#             self.__local_field: data.get("value"),
#             self.__local_field + '_alerts': data.get("value", []),
#             self.__local_field + '_readonly': data.get("readonly", False)
#         }


class SeasonalitySerializerView(serializers.ModelSerializer):
    year = serializers.IntegerField(required=False)
    measure_unity = serializers.CharField(required=False)
    january = serializers.DecimalField(required=False, max_digits=18, decimal_places=9)
    february = serializers.DecimalField(required=False, max_digits=18, decimal_places=9)
    march = serializers.DecimalField(required=False, max_digits=18, decimal_places=9)
    april = serializers.DecimalField(required=False, max_digits=18, decimal_places=9)
    may = serializers.DecimalField(required=False, max_digits=18, decimal_places=9)
    june = serializers.DecimalField(required=False, max_digits=18, decimal_places=9)
    july = serializers.DecimalField(required=False, max_digits=18, decimal_places=9)
    august = serializers.DecimalField(required=False, max_digits=18, decimal_places=9)
    september = serializers.DecimalField(required=False, max_digits=18, decimal_places=9)
    october = serializers.DecimalField(required=False, max_digits=18, decimal_places=9)
    november = serializers.DecimalField(required=False, max_digits=18, decimal_places=9)
    december = serializers.DecimalField(required=False, max_digits=18, decimal_places=9)

    class Meta:
        model = Seasonality
        fields = ('id_seasonality', 'year', 'measure_unity', 'january', 'february', 'march', 'april',
                  'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december')

    def validate(self, data):
        total = data['january'] + data['february'] + data['march'] + data['april'] + data['may'] + data['june']\
            + data['july'] + data['august'] + data['september'] + data['october'] + data['november'] + data['december']

        energy_contract: EnergyContract =  self.context['energy_contract']

        start_month = energy_contract.start_supply.month if energy_contract.start_supply.year == data['year'] else 1
        end_month = energy_contract.end_supply.month if energy_contract.end_supply.year == data['year'] else 12
         
        if (start_month == 1 and end_month == 12 and total != 12):
            raise serializers.ValidationError(translate_language_error('error_total_yearly', self.context['request']))

        if ((start_month > 1 or end_month < 12) and total > 12):
            raise serializers.ValidationError(translate_language_error('error_total_yearly_equal_or_less_12', self.context['request']))  

        return data

    def __init__(self, *args, **kwargs):
        generic_insert_user_and_observation_in_self(self, **kwargs)
        super(SeasonalitySerializerView, self).__init__(*args, **kwargs)

    def create(self, validated_data):
        seasonality = Seasonality.objects.create(**validated_data)
        log(Seasonality, seasonality.id_seasonality, {}, seasonality, self.user, self.observation_log, action="INSERT")
        return seasonality

    def update(self, instance, validated_data):
        obj = generic_update(Seasonality, instance.id_seasonality, dict(validated_data), self.user,
                             self.observation_log)
        return obj


class SeasonalityCliqSerializerView(serializers.ModelSerializer):
    seasonality_detail = SeasonalitySerializerView(read_only=True, source='id_seasonality')

    class Meta:
        model = SeasonalityCliq
        fields = ('id_seasonality_cliq', 'seasonality_detail')
        depth = 2

    def __init__(self, *args, **kwargs):
        generic_insert_user_and_observation_in_self(self, **kwargs)
        super(SeasonalityCliqSerializerView, self).__init__(*args, **kwargs)


class SeasonalityCliqSerializer(serializers.ModelSerializer):
    class Meta:
        model = SeasonalityCliq
        fields = ('id_seasonality_cliq', 'id_contract_cliq', 'id_seasonality')
        depth = 0

    def __init__(self, *args, **kwargs):
        generic_insert_user_and_observation_in_self(self, **kwargs)
        super(SeasonalityCliqSerializer, self).__init__(*args, **kwargs)

    def create(self, validated_data):
        seasonality_cliq = SeasonalityCliq.objects.create(**validated_data)
        log(SeasonalityCliq, seasonality_cliq.id_seasonality_cliq, {}, seasonality_cliq, self.user,
            self.observation_log, action="INSERT")
        return seasonality_cliq

    def update(self, instance, validated_data):
        obj = generic_update(SeasonalityCliq, instance.id_seasonality_cliq, dict(validated_data), self.user,
                             self.observation_log)
        return obj


class CliqContractSerializerViewEnergyContract(serializers.ModelSerializer):
    class Meta:
        model = CliqContract
        fields = ('id_contract_cliq', 'id_contract', 'id_buyer_assets', 'id_buyer_asset_items')


class CliqContractSerializerView(serializers.ModelSerializer):
    ccee_type_contract = serializers.CharField(required=False, default='')
    transaction_type = serializers.CharField(required=False, default='')
    flexibility = serializers.CharField(required=False, default='')
    mwm_volume = serializers.DecimalField(required=False, decimal_places=6, max_digits=18)
    mwm_volume_peak = serializers.DecimalField(required=False, decimal_places=6, max_digits=18)
    mwm_volume_offpeak = serializers.DecimalField(required=False, decimal_places=6, max_digits=18)    
    contractual_loss = serializers.DecimalField(required=False, default=0, decimal_places=6, max_digits=18)
    seasonality_cliq_details = SeasonalityCliqSerializerView(read_only=True, many=True, source='seasonalityCliq_cliqContract')
    cliq_contract = serializers.CharField(read_only=True, source='id_ccee.code_ccee')
    modulation_data = serializers.ListField(allow_null=True,required=False,default=None)


    class Meta:
        model = CliqContract
        fields = ('id_contract_cliq', 'cliq_contract', 'id_vendor_profile', 'id_buyer_profile', 'id_contract',
                  'id_ccee', 'id_buyer_assets', 'id_buyer_asset_items', 'id_submarket',
                  'ccee_type_contract', 'transaction_type', 'flexibility', 'mwm_volume', 'mwm_volume_peak', 'mwm_volume_offpeak', 'contractual_loss',
                  'status', 'seasonality_cliq_details', 'submarket', 'modulation_data'
                  )
        depth = 1

    def __init__(self, *args, **kwargs):
        generic_insert_user_and_observation_in_self(self, **kwargs)
        super(CliqContractSerializerView, self).__init__(*args, **kwargs)


class CCEESerializerCliq(serializers.Serializer):
    id_ccee = serializers.IntegerField(required=False)
    code_ccee = serializers.CharField(allow_blank=True)
    type = serializers.CharField(default='CLIQ', required=False)
    status = serializers.CharField(default='S', required=False)
   
    def validate_type(self, dob):
        if dob != 'CLIQ' and dob:
            raise serializers.ValidationError(translate_language_error('error_ccee_type', self.context['request'])+" CLIQ" )
        return dob

    def validate(self, data):
        if data['code_ccee'] == '':
            return data

        if data['code_ccee'] < '0':
            raise serializers.ValidationError(translate_language_error('error_ccee_not_value_negative', self.context['request']) )

        if 'id_ccee' in data and data['id_ccee']:
            if CceeDescription.objects.filter(code_ccee=data['code_ccee'], type="CLIQ", status="S").exclude(pk=data['id_ccee']):
                raise serializers.ValidationError(translate_language_error('error_ccee_exist', self.context['request']) )

        elif CceeDescription.objects.filter(code_ccee=data['code_ccee'], type="CLIQ", status="S"):
            raise serializers.ValidationError(translate_language_error('error_ccee_exist', self.context['request']) )
        return data

    class Meta:
        model = CceeDescription
        fields = ('id_ccee', 'code_ccee', 'type', 'name_ccee', 'status')

    def __init__(self, *args, **kwargs):
        generic_insert_user_and_observation_in_self(self, **kwargs)
        super(CCEESerializerCliq, self).__init__(*args, **kwargs)

    def create(self, validated_data):
        ccee = CceeDescription.objects.create(**validated_data)
        log(CceeDescription, ccee.id_ccee, {}, ccee, self.user, self.observation_log, action="INSERT")

        return ccee

    def update(self, instance, validated_data):
        obj = generic_update(CceeDescription, instance.id_ccee, dict(validated_data), self.user, self.observation_log)
        return obj


class CliqContractSerializer(serializers.ModelSerializer):
    id_ccee = CCEESerializerCliq()
    submarket = serializers.BooleanField(allow_null=True, default=None, required=False)
    modulation_data = serializers.ListField(allow_null=True,required=False,default=None)

    class Meta:
        model = CliqContract
        fields = ('id_contract_cliq', 'id_vendor_profile', 'id_buyer_profile', 'id_contract',
                  'id_ccee', 'id_buyer_assets', 'id_buyer_asset_items', 'id_submarket',
                  'ccee_type_contract', 'transaction_type', 'flexibility', 'mwm_volume', 'mwm_volume_peak', 'mwm_volume_offpeak', 'contractual_loss',
                  'status', 'submarket', 'modulation_data'
                  )
        depth = 0

    def __init__(self, *args, **kwargs):
        generic_insert_user_and_observation_in_self(self, **kwargs)
        super(CliqContractSerializer, self).__init__(*args, **kwargs)

    def create(self, validated_data):
        validated_data_id_ccee = validated_data.pop('id_ccee')
        ccee_description = CceeDescription.objects.create(**validated_data_id_ccee)
        log(CceeDescription, ccee_description.id_ccee, {}, ccee_description, self.user, self.observation_log,
            action="INSERT")
        cliq_contract = CliqContract.objects.create(**validated_data, id_ccee=ccee_description)
        log(CliqContract, cliq_contract.id_contract_cliq, {}, cliq_contract, self.user, self.observation_log,
            action="INSERT")
        return cliq_contract

    def update(self, instance, validated_data):
        validated_data_id_ccee = validated_data.pop('id_ccee')
        generic_update(CceeDescription, instance.id_ccee.id_ccee, dict(validated_data_id_ccee), self.user,
                       self.observation_log)
        obj = generic_update(CliqContract, instance.id_contract_cliq, dict(validated_data), self.user,
                             self.observation_log)
        return obj
