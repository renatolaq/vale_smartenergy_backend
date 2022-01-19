from rest_framework import serializers
from core.serializers import log, generic_update, generic_validation_status, generic_insert_user_and_observation_in_self
from assets.models import Assets, AssetsComposition, SeasonalityProinfa, Seasonality
from asset_items.models import AssetItems
from energy_composition.models import EnergyComposition
from core.models import Seasonality, CceeDescription 
from locales.translates_function import translate_language_error


class CCEESerializerAssetsPROINFA(serializers.ModelSerializer):
    def validate_type(self, dob):  # valid if type is not different from SIGA or PROINFA
        if dob != 'PROINFA' and dob:
            raise serializers.ValidationError(translate_language_error('error_ccee_type', self.context['request'])+" PROINFA" )
        return dob

    def validate_code_ccee(self, dob):  # check if ccee code has no duplicate
        if int(dob) < 0:
            raise serializers.ValidationError(translate_language_error('error_ccee_not_value_negative', self.context['request']) )

        if CceeDescription.objects.filter(code_ccee=dob, type="PROINFA"):
            ccee = CceeDescription.objects.filter(code_ccee=dob, type="PROINFA")
            if self.instance:
                if ccee[0].pk != self.instance.pk:
                    raise serializers.ValidationError(translate_language_error('error_ccee_exist', self.context['request'])+" PROINFA" )
            else:
                raise serializers.ValidationError(translate_language_error('error_ccee_exist', self.context['request'])+" PROINFA" )
        return dob

    type = serializers.CharField(default='PROINFA', required=False)
    status = serializers.CharField(default='S', required=False)

    class Meta:
        model = CceeDescription
        fields = ('id_ccee', 'code_ccee', 'type', 'name_ccee', 'status')

    def __init__(self, *args, **kwargs):
        generic_insert_user_and_observation_in_self(self, **kwargs)
        super(CCEESerializerAssetsPROINFA, self).__init__(*args, **kwargs)

    def create(self, validated_data):
        ccee = CceeDescription.objects.create(**validated_data)
        log(CceeDescription, ccee.id_ccee, {}, ccee, self.user, self.observation_log, action="INSERT")
        return ccee

    def update(self, instance, validated_data):
        obj = generic_update(CceeDescription, instance.id_ccee, dict(validated_data), self.user, self.observation_log)
        return obj


class CCEESerializerAssetsSIGA(serializers.ModelSerializer):
    def validate_type(self, dob):  # valid if type is not different from SIGA or PROINFA
        if dob != 'SIGA' and dob:
            raise serializers.ValidationError(translate_language_error('error_ccee_type', self.context['request'])+" SIGA" )
        return dob

    def validate_code_ccee(self, dob):  # check if ccee code has no duplicate
        if int(dob) < 0:
            raise serializers.ValidationError(translate_language_error('error_ccee_not_value_negative', self.context['request']) )

        if CceeDescription.objects.filter(code_ccee=dob, type="SIGA"):
            ccee = CceeDescription.objects.filter(code_ccee=dob, type="SIGA")
            if self.instance:
                if ccee[0].pk != self.instance.pk:
                    raise serializers.ValidationError(translate_language_error('error_ccee_exist', self.context['request']) + " SIGA")
            else:
                raise serializers.ValidationError(translate_language_error('error_ccee_exist', self.context['request']) + " SIGA")
        return dob

    type = serializers.CharField(default='SIGA', required=False)
    status = serializers.CharField(default='S', required=False)

    class Meta:
        model = CceeDescription
        fields = ('id_ccee', 'code_ccee', 'type', 'name_ccee', 'status')

    def __init__(self, *args, **kwargs):
        generic_insert_user_and_observation_in_self(self, **kwargs)
        super(CCEESerializerAssetsSIGA, self).__init__(*args, **kwargs)

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
        kwargs = {AssetItems: 'id_assets'}
        status_message = generic_validation_status(pk, 'Asset', kwargs, self)
        if status_message != 'S':
            raise serializers.ValidationError(status_message)
    return status


class AssetsSerializer(serializers.ModelSerializer):
    def validate_show_balance(self, dob):  # valid if show balance is not different from Assets or Assets items
        if dob != 'Assets' and dob != 'Asset items':
            raise serializers.ValidationError(translate_language_error('error_show_balance_invalid', self.context['request']) + " SIGA")
        return dob
    status = serializers.CharField(default='S', required=False)
    show_balance = serializers.CharField(default='Asset items', required=False)

    class Meta:
        model = Assets
        fields = ('id_assets', 'id_ccee_siga', 'id_submarket', 'id_company', 'id_profile', 'show_balance', 'status',
                  'id_ccee_proinfa')

    def __init__(self, *args, **kwargs):
        generic_insert_user_and_observation_in_self(self, **kwargs)
        super(AssetsSerializer, self).__init__(*args, **kwargs)

    def create(self, validated_data):
        assets = Assets.objects.create(**validated_data)
        log(Assets, assets.id_assets, {}, assets, self.user, self.observation_log, action="INSERT")
        return assets

    def update(self, instance, validated_data):
        validate_status(instance.id_assets, dict(validated_data)['status'], self)
        obj = generic_update(Assets, instance.id_assets, dict(validated_data), self.user, self.observation_log)
        return obj


class AssetsCompositionSerializerAssets(serializers.ModelSerializer):
    status = serializers.CharField(default='S', required=False)

    class Meta:
        model = AssetsComposition
        fields = ('id_assets_composition', 'id_assets', 'id_energy_composition', 'status')

    def __init__(self, *args, **kwargs):
        generic_insert_user_and_observation_in_self(self, **kwargs)
        super(AssetsCompositionSerializerAssets, self).__init__(*args, **kwargs)

    def create(self, validated_data):
        assetsComposition = AssetsComposition.objects.create(**validated_data)
        log(AssetsComposition, assetsComposition.id_assets_composition, {}, assetsComposition, self.user,
            self.observation_log, action="INSERT")
        return assetsComposition

    def update(self, instance, validated_data):
        obj = generic_update(AssetsComposition, instance.id_assets_composition, dict(validated_data), self.user,
                             self.observation_log)
        return obj


class SeasonalityProinfaSerializerAssets(serializers.ModelSerializer):
    class Meta:
        model = SeasonalityProinfa
        fields = ('id_seasonality_proinfa', 'id_seasonality', 'id_ccee')

    def __init__(self, *args, **kwargs):
        generic_insert_user_and_observation_in_self(self, **kwargs)
        super(SeasonalityProinfaSerializerAssets, self).__init__(*args, **kwargs)

    def create(self, validated_data):
        seasonalityProinfa = SeasonalityProinfa.objects.create(**validated_data)
        log(SeasonalityProinfa, seasonalityProinfa.id_seasonality_proinfa, {}, seasonalityProinfa, self.user,
            self.observation_log, action="INSERT")
        return seasonalityProinfa

    def update(self, instance, validated_data):
        obj = generic_update(SeasonalityProinfa, instance.id_seasonality_proinfa, dict(validated_data), self.user,
                             self.observation_log)
        return obj


class SeasonalitySerializerAssets(serializers.ModelSerializer):
    measure_unity = serializers.CharField(default='MWh')

    class Meta:
        model = Seasonality
        fields = (
            'id_seasonality', 'year', 'measure_unity', 'january', 'february', 'march', 'april', 'may', 'june', 'july',
            'august', 'september', 'october', 'november', 'december')

    def __init__(self, *args, **kwargs):
        generic_insert_user_and_observation_in_self(self, **kwargs)
        super(SeasonalitySerializerAssets, self).__init__(*args, **kwargs)

    def create(self, validated_data):
        seasonality = Seasonality.objects.create(**validated_data)
        log(Seasonality, seasonality.id_seasonality, {}, seasonality, self.user,
            self.observation_log, action="INSERT")
        return seasonality

    def update(self, instance, validated_data):
        obj = generic_update(Seasonality, instance.id_seasonality, dict(validated_data), self.user,
                             self.observation_log)
        return obj
