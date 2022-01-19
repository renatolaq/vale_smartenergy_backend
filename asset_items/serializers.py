from rest_framework import serializers
from core.models import Seasonality, CceeDescription

from company.models import Company
from assets.models import Assets
from core.serializers import log, generic_update, generic_insert_user_and_observation_in_self
from asset_items.models import AssetItems, SeazonalityAssetItemDepreciation, \
    SeasonalityAssetItem, SeasonalityAssetItemCost
from energy_composition.models import EnergyComposition


class CCEEDescriptionSerializer(serializers.ModelSerializer):
    status = serializers.CharField(default='S', required=False)
    type = serializers.CharField(required=False)

    class Meta:
        fields = ['id_ccee', 'name_ccee', 'code_ccee', 'type',
                  'status']  # o que está aparecendo no GETtela  (recuperar o recurso)
        model = CceeDescription


class EnergyCompositionSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ['id_energy_composition', 'composition_name', 'id_company', 'cost_center']
        model = EnergyComposition


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        fields = ['id_company', 'company_name',
                  'characteristics','type']  # o que está aparecendo no GETtela  (recuperar o recurso)
        model = Company


class AssetsSerializer(serializers.ModelSerializer):
    cceedescription_detail = CCEEDescriptionSerializer(many=False, source="id_ccee_siga", read_only=True)
    company = CompanySerializer(read_only=True, source='id_company')

    class Meta:
        fields = ['id_assets', 'id_ccee_siga',
                  'cceedescription_detail', 
                  'company']  # o que está aparecendo no GETtela  (recuperar o recurso)
        model = Assets


class AssetItemsSerializer(serializers.ModelSerializer):
    status = serializers.CharField(default='S', required=False)
    assets_detail = AssetsSerializer(many=False, source="id_assets", read_only=True)
    company_detail = CompanySerializer(read_only=True, source='id_company')
    energycomposition_detail = EnergyCompositionSerializer(read_only=True, source='id_energy_composition')

    class Meta:
        fields = ['id_asset_items', 'status', 'id_company', 'company_detail', 'id_energy_composition',
                  'energycomposition_detail', 'id_assets',
                  'assets_detail']  # o que está aparecendo no GET tela (recuperar o recurso)
        model = AssetItems

    def __init__(self, *args, **kwargs):
        generic_insert_user_and_observation_in_self(self, **kwargs)
        super(AssetItemsSerializer, self).__init__(*args, **kwargs)

    def create(self, validated_data):
        asset_item = AssetItems.objects.create(**validated_data)
        log(asset_item, asset_item.id_asset_items, {}, asset_item, self.user, self.observation_log, action="INSERT")
        return asset_item

    def update(self, instance, validated_data):
        obj = generic_update(AssetItems, instance.id_asset_items, dict(validated_data), self.user, self.observation_log)
        return obj


# possibility of using the SeasonalitySerializer from Assets
class SeasonalitySerializerAssetItems(serializers.ModelSerializer):
    measure_unity = serializers.CharField(default='MWh')

    class Meta:
        model = Seasonality
        fields = (
        'id_seasonality', 'year', 'measure_unity', 'january', 'february', 'march', 'april', 'may', 'june', 'july',
        'august', 'september', 'october', 'november', 'december')

    def __init__(self, *args, **kwargs):
        generic_insert_user_and_observation_in_self(self, **kwargs)
        super(SeasonalitySerializerAssetItems, self).__init__(*args, **kwargs)

    def create(self, validated_data):
        seasonality = Seasonality.objects.create(**validated_data)
        log(Seasonality, seasonality.id_seasonality, {}, seasonality, self.user,
            self.observation_log, action="INSERT")
        return seasonality

    def update(self, instance, validated_data):
        obj = generic_update(Seasonality, instance.id_seasonality, dict(validated_data), self.user,
                             self.observation_log)
        return obj


# custo da geração
class SazonalityAssetItemCostSerializer(serializers.ModelSerializer):
    id_seasonality_detail = SeasonalitySerializerAssetItems(source="id_seazonality_asset", write_only=False, many=False,
                                                            read_only=True)

    class Meta:
        model = SeasonalityAssetItemCost
        fields = ('id_seasonality_asset_item_cost', 'id_asset_items', 'id_seasonality_detail', 'id_seazonality_asset')

    def __init__(self, *args, **kwargs):
        generic_insert_user_and_observation_in_self(self, **kwargs)
        super(SazonalityAssetItemCostSerializer, self).__init__(*args, **kwargs)

    def create(self, validated_data):
        sazonalityItemCost = SeasonalityAssetItemCost.objects.create(**validated_data)
        log(SeasonalityAssetItemCost, sazonalityItemCost.id_seasonality_asset_item_cost, {}, sazonalityItemCost,
            self.user,
            self.observation_log, action="INSERT")
        return sazonalityItemCost

    def update(self, instance, validated_data):
        obj = generic_update(SeasonalityAssetItemCost, instance.id_seasonality_asset_item_cost, dict(validated_data),
                             self.user,
                             self.observation_log)
        return obj


# sazonalidade da geração
class SeasonalityAssetItemSerializer(serializers.ModelSerializer):
    id_seasonality_detail = SeasonalitySerializerAssetItems(source="id_seasonality", write_only=False, many=False,
                                                            read_only=True)

    class Meta:
        model = SeasonalityAssetItem
        fields = ('id_seasonality_asset_item', 'id_seasonality_detail', 'id_seasonality', 'id_asset_items')

    def __init__(self, *args, **kwargs):
        generic_insert_user_and_observation_in_self(self, **kwargs)
        super(SeasonalityAssetItemSerializer, self).__init__(*args, **kwargs)

    def create(self, validated_data):
        sazonalityAssetItem = SeasonalityAssetItem.objects.create(**validated_data)
        log(SeasonalityAssetItem, sazonalityAssetItem.id_seasonality_asset_item, {}, sazonalityAssetItem, self.user,
            self.observation_log, action="INSERT")
        return sazonalityAssetItem

    def update(self, instance, validated_data):
        obj = generic_update(SeasonalityAssetItem, instance.id_seasonality_asset_item, dict(validated_data), self.user,
                             self.observation_log)
        return obj


# depreciação
class SeazonalityAssetItemDepreciationSerializer(serializers.ModelSerializer):
    id_seasonality_detail = SeasonalitySerializerAssetItems(source="id_seasonality", write_only=False, many=False,
                                                            read_only=True)

    class Meta:
        model = SeazonalityAssetItemDepreciation
        fields = ('seazonality_asset_depreciation', 'id_seasonality_detail', 'id_seasonality', 'id_asset_items')

    def __init__(self, *args, **kwargs):
        generic_insert_user_and_observation_in_self(self, **kwargs)
        super(SeazonalityAssetItemDepreciationSerializer, self).__init__(*args, **kwargs)
    def create(self, validated_data):
        sazonalityAssetItemDepreciation = SeazonalityAssetItemDepreciation.objects.create(**validated_data)
        log(SeazonalityAssetItemDepreciation, sazonalityAssetItemDepreciation.seazonality_asset_depreciation, {},
            sazonalityAssetItemDepreciation, self.user, self.observation_log, action="INSERT")
        return sazonalityAssetItemDepreciation

    def update(self, instance, validated_data):
        obj = generic_update(SeazonalityAssetItemDepreciation, instance.seazonality_asset_depreciation,
                             dict(validated_data), self.user, self.observation_log)
        return obj


# FindBasic
class AssetItemsSerializerFindBasic(serializers.ModelSerializer):
    class Meta:
        model = AssetItems
        fields = ['id_asset_items', 'id_company', 'id_energy_composition', 'id_assets', 'status']

class AssetsSerializerFindBasic(serializers.ModelSerializer):
    class Meta:
        model = Assets
        fields = ['id_assets', 'id_ccee_siga', 'id_ccee_proinfa', 'status']  

class CCEEDescriptionSerializerFindBasic(serializers.ModelSerializer):
    class Meta:
        model = CceeDescription
        fields = ['id_ccee', 'name_ccee', 'code_ccee', 'type', 'status'] 
        
class CompanySerializerFindBasic(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ['id_company', 'company_name', 'characteristics','type']

class EnergyCompositionSerializerFindBasic(serializers.ModelSerializer):
    class Meta:
        model = EnergyComposition
        fields = ['id_energy_composition', 'composition_name', 'id_company', 'cost_center']
        