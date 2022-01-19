from rest_framework import serializers
from balance_report_market_settlement.models import Report, Balance, BalanceFields, MacroBalance, HistoryBalance, \
     PriorizedCliq, DetailedBalance, MarketSettlement, CliqContract, SeasonalityCliq
from balance_report_market_settlement.exceptions import EmptySeasonality, NoTransferContractPriorization, \
    NoFlexibilityLimit
from consumption_metering_reports.serializers import ReportType
from energy_contract.models import Flexibilization, Precification
from transfer_contract_priority.models import TransferContractPriority
from .utils import calculate_flexible_proportional_cliq_volume
from datetime import datetime
from decimal import Decimal

from calendar import month_name


class DetailedBalanceSerializer(serializers.ModelSerializer):
    submarket = serializers.SerializerMethodField(read_only=True)
    id_contract_cliq = serializers.IntegerField(read_only=True)

    def get_submarket(self, serialized_object):
        return serialized_object.id_submarket.description

    def get_id_contract_cliq(self, serialized_object):
        return serialized_object.id_contract_cliq.id

    class Meta:
        model = DetailedBalance
        fields = ('id', 'id_contract_cliq', 'contract_name', 'contract_id', 'submarket', 'volume', 'fare', 'amount', 'unity', 'loss', 'gsf')


class MarketSettlementSerializer(serializers.ModelSerializer):

    class Meta:
        model = MarketSettlement
        fields = ('id', 'profile_name', 'amount_seco', 'amount_s', 'amount_ne', 'amount_n', 'saleoff')

class MacroSerializer(serializers.ModelSerializer):

    class Meta:
        model = MacroBalance
        fields = ('id', 'purchase', 'sale', 'consumption', 'generation', 'proinfa')

class ProfileSerializer(serializers.ModelSerializer):
    macro = MacroSerializer(read_only=True, many=False, source='get_macro')
    purchase_detail = DetailedBalanceSerializer(read_only=True, many=True, source='get_purchase_detail')
    sale_detail = DetailedBalanceSerializer(read_only=True, many=True, source='get_sale_detail')
    consumption_detail = DetailedBalanceSerializer(read_only=True, many=True, source='get_consumption_detail')
    generation_detail = DetailedBalanceSerializer(read_only=True, many=True, source='get_generation_detail')
    market_settlement = MarketSettlementSerializer(read_only=True, many=True, source='get_market_settlement')

    class Meta:
        model = Balance
        fields = ('id', 'name', 'value', 'macro','purchase_detail', 'sale_detail', 'consumption_detail', 'generation_detail', 'market_settlement')


class AgentSerializer(serializers.ModelSerializer):
    macro = MacroSerializer(read_only=True, many=False, source='get_macro')
    profiles = ProfileSerializer(read_only=True, many=True, source='get_profile')

    class Meta:
        model = Balance
        fields = ('id', 'name', 'value', 'macro', 'profiles')


class BalanceFieldsSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    month = serializers.IntegerField(read_only=True)
    year = serializers.IntegerField(read_only=True)
    id_rcd = serializers.IntegerField(read_only=True, source='id_report_rcd.id', default=0)
    rcd_name = serializers.CharField(read_only=True, source='id_report_rcd.report_name', default='')
    gsf = serializers.DecimalField(read_only=True, max_digits=18, decimal_places=6)
    pld_n = serializers.DecimalField(read_only=True, max_digits=18, decimal_places=4)
    pld_ne = serializers.DecimalField(read_only=True, max_digits=18, decimal_places=4)
    pld_seco = serializers.DecimalField(read_only=True, max_digits=18, decimal_places=4)
    pld_s = serializers.DecimalField(read_only=True, max_digits=18, decimal_places=4)
    
    class Meta:
        model = BalanceFields
        fields = ('id', 'month', 'year', 'id_rcd', 'rcd_name',  'gsf', 'pld_n', 'pld_ne', 'pld_seco', 'pld_s')


class PriorizedCliqSerializer(serializers.ModelSerializer):

    class Meta:
        model = PriorizedCliq
        fields = ('id', 'contract_name', 'contract_modality', 'contract_cliq', 'buyer_profile', 'vendor_profile', 'cliq_type')


class CliqContractSerializer(serializers.ModelSerializer):
    contract_id = serializers.IntegerField(read_only=True, source='id_contract.id_contract')
    contract_name = serializers.CharField(read_only=True, source='id_contract.contract_name')
    contract_type = serializers.CharField(read_only=True, source='id_contract.type')
    contract_modality = serializers.CharField(read_only=True, source='id_contract.modality')
    cliq_id = serializers.IntegerField(read_only=True, source='id_contract_cliq')
    contract_cliq = serializers.CharField(read_only=True, source='id_ccee.code_ccee')
    id_buyer_profile = serializers.IntegerField(read_only=True, source='id_buyer_profile.id_profile')
    buyer_profile = serializers.CharField(read_only=True, source='id_buyer_profile.name_profile')
    id_vendor_profile = serializers.IntegerField(read_only=True, source='id_vendor_profile.id_profile')
    id_buyer_assets = serializers.IntegerField(read_only=True, source='id_buyer_assets.id_assets')
    id_buyer_asset_items = serializers.IntegerField(read_only=True, source='id_buyer_asset_items.id_asset_items')
    vendor_profile = serializers.CharField(read_only=True, source='id_vendor_profile.name_profile')
    id_submarket = serializers.IntegerField(read_only=True, source='id_submarket.id_submarket')
    fare = serializers.DecimalField(read_only=True, max_digits=18, decimal_places=6, source='id_contract.precif_energy_contract.active_price_mwh')
    volume = serializers.SerializerMethodField()
    proinfa_flexibility = serializers.CharField(read_only=True, source='id_contract.flexib_energy_contract.proinfa_flexibility')
    cliq_type = serializers.SerializerMethodField()
    seasonality = serializers.SerializerMethodField()
    new = serializers.BooleanField()
    double_status = serializers.CharField()
    priorized_profile_id = serializers.IntegerField(read_only=True)

    def get_cliq_type(self, serialized_object):
        """Returns if the cliq contract is Flat, Flexible or Transference"""
        cliq_type = serialized_object.contract_type
        try:
            if cliq_type.lower() == 'transferencia':
                try:
                    transfer_contract_priority = serialized_object.cliqs_priority.filter(status='S').get()
                    if transfer_contract_priority.priority_number is None:
                        raise NoTransferContractPriorization({'contract_name': serialized_object.id_contract.contract_name})
                except TransferContractPriority.DoesNotExist as e:
                    raise NoTransferContractPriorization({'contract_name': serialized_object.id_contract.contract_name}) from e
            if cliq_type.lower() == 'flexivel':
                try:
                    flexibilization_limits = serialized_object.id_contract.flexib_energy_contract
                    if (flexibilization_limits.min_flexibility_pu_peak is None) or (flexibilization_limits.max_flexibility_pu_peak is None):
                        raise NoFlexibilityLimit({'contract_name': serialized_object.id_contract.contract_name})
                except Flexibilization.DoesNotExist as e:
                    raise NoFlexibilityLimit({'contract_name': serialized_object.id_contract.contract_name}) from e
        except Exception as ex:
            if self.context['request'].query_params.get('validate_contract') != False:
                raise ex
        return cliq_type

    def get_seasonality(self, serialized_object):
        "Gets the seasonality for the specified month and year for the cliq contract"
        try:
            month = int(self.context['request'].query_params.get('month'))
            year = int(self.context['request'].query_params.get('year'))
        except:
            date_now = datetime.today()
            month = date_now.month
            year = date_now.year

        try:
            seasonality = getattr(serialized_object.seasonality_cliq.get(id_seasonality__year=year).id_seasonality, month_name[month].lower())
            if seasonality is None:
                raise EmptySeasonality({'contract_name': serialized_object.id_contract.contract_name})
            return seasonality
        except SeasonalityCliq.DoesNotExist as e:
            if serialized_object.id_contract.season_energy_contract.type_seasonality.lower() == 'sazonalizado':
                raise EmptySeasonality({'contract_name': serialized_object.id_contract.contract_name}) from e
            else:
                return None 

    def get_volume(self, serialized_object):
        """Calculates volume for proportional flexible cliqs"""
        if serialized_object.proportional_flexible:
            id_reference_report = int(self.context['request'].query_params.get('id_rcd'))
            volume = calculate_flexible_proportional_cliq_volume(serialized_object, id_reference_report)
            if volume is None:
                print(serialized_object)
            return volume
        else:
            if serialized_object.mwm_volume is None:
                print(serialized_object)
            return serialized_object.mwm_volume

    class Meta:
        model = CliqContract
        fields = ('contract_id', 'contract_name', 'contract_type', 'contract_modality', 'cliq_id', 'contract_cliq',
                  'id_buyer_profile', 'id_buyer_assets', 'id_buyer_asset_items', 'buyer_profile', 'id_vendor_profile',
                  'vendor_profile', 'id_submarket', 'cliq_type', 'fare', 'volume', 'transaction_type', 'flexibility',
                  'proinfa_flexibility', 'seasonality', 'new', 'double_status', 'priorized_profile_id')


class SortContractsSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True)
    items = CliqContractSerializer(read_only=True, many=True)


class SortProfileSerializer(serializers.Serializer):
    profile_id = serializers.CharField(read_only=True)
    profile_name = serializers.CharField(read_only=True)
    contracts = SortContractsSerializer(read_only=True, many=True)


class ReportsSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    report_name = serializers.CharField(read_only=True)
    id_reference = serializers.IntegerField(read_only=True, source='id_reference.id')
    reference_name = serializers.CharField(read_only=True, source='id_reference.report_name')
    creation_date = serializers.DateTimeField(read_only=True)
    status = serializers.CharField(read_only=True)
    month = serializers.CharField(read_only=True)
    year = serializers.CharField(read_only=True)
    balance_fields = BalanceFieldsSerializer(read_only=True, many=False, source='get_balance_fields')
    priorized_cliq = PriorizedCliqSerializer(read_only=True, many=True, source='get_priorized_cliq')
    agents = AgentSerializer(read_only=True, many=True, source='get_balance')

    class Meta:
        model = Report
        fields = ('id', 'report_name', 'id_reference', 'reference_name', 'creation_date', 'status', 'month', 'year',
                  'balance_fields', 'priorized_cliq', 'agents')


class ReportsSerializerGet(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    report_name = serializers.CharField(read_only=True)
    id_reference = serializers.IntegerField(read_only=True, source='id_reference.id')
    reference_name = serializers.CharField(read_only=True, source='id_reference.report_name')
    creation_date = serializers.DateTimeField(read_only=True)
    status = serializers.CharField(read_only=True)
    month = serializers.CharField(read_only=True)
    year = serializers.CharField(read_only=True)
    balance_fields = BalanceFieldsSerializer(read_only=True, many=False, source='get_balance_fields')
    priorized_cliq = SortProfileSerializer(read_only=True, many=True)
    agents = AgentSerializer(read_only=True, many=True, source='get_balance')


class HistoryBalancesSerializer(serializers.ModelSerializer):
    id_history_balance = serializers.IntegerField(read_only=True)
    id_report = serializers.IntegerField(read_only=True, source='id_report.id')
    month = serializers.BooleanField(default=False)
    year = serializers.BooleanField(default=False)
    id_rcd = serializers.BooleanField(default=False)
    id_rcd_value = serializers.CharField(default=False, source='id_report.id_reference.report_name')
    status = serializers.BooleanField(default=False)
    status_value = serializers.SerializerMethodField()
    gsf = serializers.BooleanField(default=False)
    gsf_value = serializers.DecimalField(read_only=True, max_digits=18, decimal_places=6, source='id_report.get_balance_fields.gsf')
    pld_n = serializers.BooleanField(default=False)
    pld_n_value = serializers.DecimalField(read_only=True, max_digits=18, decimal_places=4, source='id_report.get_balance_fields.pld_n')
    pld_ne = serializers.BooleanField(default=False)
    pld_ne_value = serializers.DecimalField(read_only=True, max_digits=18, decimal_places=4, source='id_report.get_balance_fields.pld_ne')
    pld_seco = serializers.BooleanField(default=False)
    pld_seco_value = serializers.DecimalField(read_only=True, max_digits=18, decimal_places=4, source='id_report.get_balance_fields.pld_seco')
    pld_s = serializers.BooleanField(default=False)
    pld_s_value = serializers.DecimalField(read_only=True, max_digits=18, decimal_places=4, source='id_report.get_balance_fields.pld_s')
    priorized_cliq = serializers.BooleanField(default=False)
    username = serializers.CharField(read_only=True)
    justification = serializers.CharField(required=True, max_length=300)
    create_date = serializers.DateTimeField(required=True)

    def get_status_value(self, serialized_object):
        justification_word_list = serialized_object.justification.split()
        status_from_justification = justification_word_list[-1][0]
        return status_from_justification if status_from_justification in ['S', 'C'] else ''

    class Meta:
        model = HistoryBalance
        fields = ('id_history_balance', 'id_report', 'month', 'year', 'id_rcd', 'id_rcd_value', 'status', 'status_value', 
        'gsf', 'gsf_value', 'pld_n', 'pld_n_value', 'pld_ne', 'pld_ne_value', 'pld_seco', 'pld_seco_value', 'pld_s', 
        'pld_s_value', 'priorized_cliq', 'username', 'justification', 'create_date')


class LastBalancesSerializer(serializers.ModelSerializer):
    reference_report_name = serializers.SerializerMethodField()

    def get_reference_report_name(self, serialized_object):
        return serialized_object.id_reference.report_name


    class Meta:
        model = Report
        fields = ('id', 'month', 'year', 'report_name', 'id_reference', 'reference_report_name',
        'creation_date', 'status')


class DetailedConsumptionReferenceSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    report_name = serializers.CharField(read_only=True)
