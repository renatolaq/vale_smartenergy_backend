from rest_framework import serializers
from agents.models import Agents
from usage_contract.models import UsageContract
from assets.models import Submarket, Assets, AssetsComposition, SeasonalityProinfa, Seasonality
from asset_items.models import AssetItems
from company.models import Company
from profiles.models import Profile
from energy_composition.models import EnergyComposition
from core.models import CceeDescription


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('id_company', 'company_name', 'registered_number', 'type', 'state_number', 'nationality', 'id_sap',
                  'id_address', 'characteristics', 'status', 'create_date')
        model = Company


class AgentsSerializer(serializers.ModelSerializer):
    company_detail = CompanySerializer(source="id_company", read_only=True)
    status = serializers.CharField(default='S', required=False)

    class Meta:
        model = Agents
        fields = ('id_agents', 'id_company', 'vale_name_agent', 'status', 'company_detail')


class submarketAssetsSerializerView(serializers.ModelSerializer):
    class Meta:
        fields = ('id_submarket', 'description', 'status')
        model = Submarket


class CompanyAssetsSerializerView(serializers.ModelSerializer):
    class Meta:
        fields = ('id_company', 'company_name')
        model = Company


class ProfileAssetsSerializerView(serializers.ModelSerializer):
    agents_detail = AgentsSerializer(read_only=True, source='id_agents')

    class Meta:
        fields = ('id_profile', 'name_profile', 'agents_detail', 'status')
        model = Profile


class CCEESerializerAssetsPROINFAView(serializers.ModelSerializer):
    class Meta:
        model = CceeDescription
        fields = ('id_ccee', 'code_ccee', 'type', 'name_ccee')


class CCEESerializerAssetsSigaView(serializers.ModelSerializer):
    class Meta:
        model = CceeDescription
        fields = ('id_ccee', 'code_ccee', 'type', 'name_ccee')


class UsageContractAssetsSerializerView(serializers.ModelSerializer):
    class Meta:
        fields = ('id_usage_contract', 'id_company', 'contract_number')
        model = UsageContract


class EnergyCompositionAssetsSerializerView(serializers.ModelSerializer):
    class Meta:
        fields = ('id_energy_composition', 'composition_name')
        model = EnergyComposition


class AssetsSerializerView(serializers.ModelSerializer):
    id_company = CompanyAssetsSerializerView(write_only=False, many=False, read_only=True)
    id_profile = ProfileAssetsSerializerView(write_only=False, many=False, read_only=False)
    id_submarket = submarketAssetsSerializerView(write_only=False, many=False, read_only=False)
    id_ccee_siga = CCEESerializerAssetsSigaView(write_only=False, many=False, read_only=False)
    id_ccee_proinfa = CCEESerializerAssetsPROINFAView(write_only=False, many=False, read_only=False)
    status = serializers.CharField(default='S', required=False)

    class Meta:
        model = Assets
        fields = ('id_assets', 'id_company', 'id_profile', 'id_submarket', 'id_ccee_siga', 'show_balance', 'status',
                  'id_ccee_proinfa')


class AssetsCompositionSerializerView(serializers.ModelSerializer):
    id_energy_composition = EnergyCompositionAssetsSerializerView(write_only=False, many=False, read_only=True)
    id_assets = AssetsSerializerView(write_only=False, many=False, read_only=True)
    status = serializers.CharField(default='S', required=False)

    class Meta:
        model = AssetsComposition
        fields = ('id_assets_composition', 'id_assets', 'id_energy_composition', 'status')


class SeasonalitySerializerView(serializers.ModelSerializer):
    class Meta:
        model = Seasonality
        fields = (
            'id_seasonality', 'year', 'measure_unity', 'january', 'february', 'march', 'april', 'may', 'june', 'july',
            'august', 'september', 'october', 'november', 'december')


class SeasonalityProinfaSerializerView(serializers.ModelSerializer):
    id_seasonality = SeasonalitySerializerView(write_only=False, many=False, read_only=True)

    class Meta:
        model = SeasonalityProinfa
        fields = ('id_seasonality_proinfa', 'id_ccee', 'id_seasonality')


class AssetsSerializerShowView(serializers.ModelSerializer):
    id_company = CompanyAssetsSerializerView(write_only=False, many=False, read_only=True)
    id_ccee_siga = CCEESerializerAssetsSigaView(write_only=False, many=False, read_only=False)
    status = serializers.CharField(default='S', required=False)

    class Meta:
        model = Assets
        fields = ('id_assets', 'id_company', 'id_ccee_siga', 'id_ccee_proinfa', 'status')


class AssetsItemsSerializer(serializers.ModelSerializer):
    id_company = CompanyAssetsSerializerView(write_only=False, many=False, read_only=True)
    status = serializers.CharField(default='S', required=False)

    class Meta:
        model = AssetItems
        fields = ('id_asset_items', 'status', 'id_company')


class AssetsSerializerWithItems(serializers.ModelSerializer):
    id_company = CompanyAssetsSerializerView(write_only=False, many=False, read_only=True)
    id_ccee_siga = CCEESerializerAssetsSigaView(write_only=False, many=False, read_only=False)
    status = serializers.CharField(default='S', required=False)
    assetitems_asset = AssetsItemsSerializer(many=True)

    class Meta:
        model = Assets
        fields = ('id_assets', 'id_company', 'id_ccee_siga', 'status', 'show_balance', 'assetitems_asset')
