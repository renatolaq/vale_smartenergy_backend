from django.db import transaction
from django.db.models import Sum, Case, When, Value, BooleanField, CharField, DecimalField, Q, F, Value as V
from django.db.models.functions import Coalesce
from rest_framework.response import Response
from .exceptions import *
from .models import Report, BalanceFields, PriorizedCliq, Balance, DetailedBalance, MacroBalance, MarketSettlement, \
    BalanceType, DetailedBalanceType, ReportType, CliqContract, Profile
from .utils import is_before_or_equal_nth_brazilian_workday, gen_report_name, mwm_to_mwh, clamp, none_to_zero, \
    get_last_month_date, get_local_timezone, get_one_by_property_value
from .serializers import BalanceFieldsSerializer, SortProfileSerializer
from .history_service import HistoryService
from .cache_balance import CacheBalance
from assets.models import Assets, Submarket, SeasonalityProinfa
from agents.models import Agents
from asset_items.models import AssetItems, SeasonalityAssetItem
from balance_report_market_settlement.models import MeteringReportData, MeteringReportValue
from decimal import Decimal
from datetime import datetime, timezone, timedelta, date
from calendar import monthrange, month_name
from collections import namedtuple
from copy import deepcopy
from SmartEnergy.handler_logging import HandlerLog
import re

WORK_DAY_LIMIT = 8


class BalanceService:
    logger = HandlerLog()
    cache = None
    PURCHASE = 'label_purchase'
    SALE = 'label_sale'

    def __init__(self):
        super().__init__()
        self.executed_cliqs = {}

    @transaction.atomic
    def generate_balance(self, balance_data):

        market_settlement_id_list = []
        self.cache = CacheBalance.get_instance()
        new_balance_report = self.generate_balance_wrapper(balance_data, market_settlement_id_list)
        self.calculate_balance(new_balance_report, market_settlement_id_list)
        self.calculate_market_settlement(new_balance_report, market_settlement_id_list)
        self.update_profile_macro_balance(new_balance_report)
        self.save_agent_macro_balance(new_balance_report)
        self.update_balance_value(new_balance_report)
        return new_balance_report

    def generate_balance_wrapper(self, balance_data, market_settlement_id_list):
        """Separates the arguments from request and sends them to correct function"""
        # Fetching the associated detailed consumption report from the database
        detailed_consumption_report = Report(id=balance_data['balance_fields']['id_rcd'])

        # Generating a new temporary balance (with status 'T')
        new_balance_report = self.generate_balance_report(balance_data['balance_fields'], detailed_consumption_report)

        # Saving the balance fields
        ## Removing dict keys that are not saved to the database
        balance_fields = {key: balance_data['balance_fields'][key] for key in balance_data['balance_fields'] if key not in ['id_rcd', 'rcd_name']}
        self.save_balance_fields(balance_fields, new_balance_report, detailed_consumption_report)

        # Saving the priorized cliqs
        self.save_priorized_cliq_list(balance_data['priorized_cliq'], new_balance_report)

        # Saving the agents balance:
        self.save_agent_balance(new_balance_report, market_settlement_id_list)

        return new_balance_report

    def generate_balance_report(self, report_fields, detailed_consumption_report):
        """Generates a new balance report, receives report_fields a dict with the necesssary model args
        and detailed_consumption_report a report object which is associated with the balance"""

        new_balance_report = Report()
        new_balance_report.report_name = gen_report_name('BDE', report_fields['month'], report_fields['year'])
        report_type = get_one_by_property_value(self.cache.report_types, 'initials', 'BDE')
        new_balance_report.report_type = ReportType(id=report_type.id)
        new_balance_report.id_reference = detailed_consumption_report
        new_balance_report.creation_date = datetime.now(timezone.utc)
        new_balance_report.status = 'T'
        new_balance_report.month = report_fields['month']
        new_balance_report.year = report_fields['year']

        # Saving the new balance
        new_balance_report.save()
        return new_balance_report
    
    def save_balance_fields(self, balance_fields, new_balance_report, detailed_consumption_report):
        """Extracts balance fields data from the request data and saves it to the BALANCE FIELDS table with
        the new balance report id"""

        new_balance_fields = BalanceFields(**balance_fields)
        new_balance_fields.id = None
        new_balance_fields.id_report = new_balance_report
        new_balance_fields.id_report_rcd = detailed_consumption_report

        # Saving the balance fields
        new_balance_fields.save(force_insert=True)
        return new_balance_fields
    
    def save_priorized_cliq_list(self, profile_list, new_balance_report):
        """Saves a list of priorized cliqs"""
        new_priorized_cliq_list = []
        priorized_cliq_list = self.normalizer_profile_list(profile_list)
        for priorized_cliq in priorized_cliq_list:
            # Converting volume from MWm to MWh
            priorized_cliq['volume'] = mwm_to_mwh(new_balance_report.year, new_balance_report.month, float(priorized_cliq['volume']))
            # Setting id_buyer_profile when the buyer is an asset or asset item:
            if priorized_cliq.get('id_buyer_assets', None):
                buyer_asset = get_one_by_property_value(self.cache.assets, 'id_assets', priorized_cliq['id_buyer_assets'])
                priorized_cliq['id_buyer_profile'] = buyer_asset.id_profile_id
            elif priorized_cliq.get('id_buyer_asset_items', None):
                buyer_asset_item = self.cache.queryset_asset_items.get(id_asset_items=priorized_cliq['id_buyer_asset_items'])
                priorized_cliq['id_buyer_profile'] = buyer_asset_item.id_assets.id_profile.id_profile
            priorized_cliq_cleaned = {key: priorized_cliq[key] for key in priorized_cliq if key not in ['contract_id', 'contract_type']}
            new_priorized_cliq_list.append(self.save_priorized_cliq(priorized_cliq_cleaned, new_balance_report))
        return new_priorized_cliq_list

    def normalizer_profile_list(self, profile_list):
        priorized_cliq_list = []
        for profile in profile_list:
            for contract in profile['contracts']:
                for item in contract['items']:
                    del item['new']
                    priorized_cliq_list.append(item)
        return priorized_cliq_list

    def save_priorized_cliq(self, priorized_cliq, new_balance_report):
        """Saves a new priorized cliq, receives a dict with the model's fields and the report object which
        is associated with it"""
        new_priorized_cliq = PriorizedCliq(**priorized_cliq)
        new_priorized_cliq.id_report = new_balance_report
        new_priorized_cliq.clean()
        new_priorized_cliq.save()
        return new_priorized_cliq

    def save_agent_balance(self, balance_report, market_settlement_id_list):
        """Saves a balance for every agent in the system"""
        agent_list = self.cache.queryset_agent
        balance_type = get_one_by_property_value(self.cache.balance_types, 'description', 'AGENT')
        agent_balance_type = BalanceType(id=balance_type.id)

        for agent in agent_list:
            new_agent_balance = self.record_balance(agent.vale_name_agent, balance_report, agent_balance_type, None, agent.id_company.type == 'I')
            new_profiles_balance = self.save_profile_balance(balance_report, new_agent_balance, agent, market_settlement_id_list)
            # new_macro_agent_balance = self.save_macro_balance(new_agent_balance, self.calculate_agent_volume)

    def save_profile_balance(self, balance_report, agent_balance, agent, market_settlement_id_list):
        """Saves a balance for every agent's profile in the system"""
        profile_list = agent.profile_agent.exclude(status__in=['0', 'n', 'N'])
        balance_type = get_one_by_property_value(self.cache.balance_types, 'description', 'PROFILE')
        profile_balance_type = BalanceType(id=balance_type.id)

        for profile in profile_list:
            new_profile_balance = self.record_balance(profile.name_profile, balance_report, profile_balance_type, agent_balance, None)
            new_detailed_balance = self.generate_detailed_generation_and_consumption_balance(new_profile_balance, balance_report, profile)
            new_macro_profile_balance = self.save_macro_balance(new_profile_balance, self.calculate_profile_volume)
            new_market_settlement = self.save_initial_market_settlement(new_profile_balance, market_settlement_id_list)
    
    def record_balance(self, name, balance_report, balance_type, id_agente=None, internal_company=None):
        new_balance = Balance()
        new_balance.name = name
        new_balance.value = None
        new_balance.id_balance_type = balance_type
        new_balance.id_agente = id_agente
        new_balance.id_report = balance_report
        new_balance.internal_company = internal_company

        # Saving the balance
        new_balance.save()
        return new_balance

    def generate_detailed_generation_and_consumption_balance(self, profile_balance, balance_report, profile):
        """Generates detailed balance for purchase, sale, consumption and generation"""

        # Detailed balance for generation:
        asset_list = profile.assets_profile.exclude(status__in=['0', 'n', 'N'])
        generation_type = get_one_by_property_value(self.cache.detailed_balance_types, 'description', 'GENERATION')
        generation_balance_type = DetailedBalanceType(id=generation_type.id)
        consumption_type = get_one_by_property_value(self.cache.detailed_balance_types, 'description', 'CONSUMPTION')
        consumption_balance_type = DetailedBalanceType(id=consumption_type.id)

        for asset in asset_list:
            if asset.id_company.characteristics.lower() in 'consumidora':
                # Saving proinfa for detailed profile balance:
                new_profile_proinfa = self.save_profile_proinfa(asset, profile_balance)

            # Checking if asset has balance flag checked:
            if asset.show_balance == 'Assets':
                # Consumption for assets:
                if asset.id_company.characteristics.lower() in 'consumidora':
                    volume, loss = self.get_consumed_volume_and_loss(balance_report.id_reference.id, asset.id_company.id_company)

                    new_detailed_balance = self.save_detailed_balance(profile_balance, consumption_balance_type,
                    asset.id_submarket.id_submarket, volume, unity=asset.id_company.company_name, loss=loss)
            else:
                asset_item_list = asset.assetitems_asset.exclude(status__in=['0', 'n', 'N'])

                for asset_item in asset_item_list:                    
                    # Checking if the asset item is a generating unit
                    if asset_item.id_company.characteristics.lower() in 'geradora':
                        gsf = balance_report.report_balance.get().gsf
                        volume = self.calculate_generated_volume(balance_report, asset_item)

                        new_detailed_balance = self.save_detailed_balance(profile_balance, generation_balance_type,
                        asset.id_submarket.id_submarket, volume, unity=asset_item.id_company.company_name, gsf=gsf)
                    elif asset_item.id_company.characteristics.lower() in 'consumidora':
                        # Consumption for asset itens:
                        volume, loss = self.get_consumed_volume_and_loss(balance_report.id_reference.id, asset_item.id_company.id_company)

                        new_detailed_balance = self.save_detailed_balance(profile_balance, consumption_balance_type,
                        asset.id_submarket.id_submarket, volume, unity=asset_item.id_company.company_name, loss=loss)

    def calculate_generated_volume(self, balance_report, asset_item):
        """Calculates the volume generated for generating units (asset items)""" 
        month = int(balance_report.report_balance.get().month)
        year = int(balance_report.report_balance.get().year)
        physical_guarantee = asset_item.id_company.id_company_eletric.guaranteed_power
        try: # Trying to fetch generating asset item seasonality
            generation_seasonalization = getattr(asset_item.assetitem_seasonality.filter(id_seasonality__year=year).get().id_seasonality, month_name[month].lower())
        except SeasonalityAssetItem.DoesNotExist as e:
            raise NoGenerationSeasonality({'generating_unit': asset_item.id_company.company_name}) from e
        hours_in_month = 24*monthrange(year, month)[1]
        transmission_loss = asset_item.id_company.id_company_eletric.transmission_loss
        internal_loss = asset_item.id_company.id_company_eletric.internal_loss
        if (transmission_loss is None) or (internal_loss is None):
            raise NoGenerationLoss({'generating_unit': asset_item.id_company.company_name})
        gsf = balance_report.report_balance.get().gsf

        return physical_guarantee*generation_seasonalization*hours_in_month*(1-transmission_loss/100)*(1-internal_loss/100)*(1-max(0, gsf/100))
    
    def get_consumed_volume_and_loss(self, id_report, id_company):
        """Fetches the total consumed volume from detailed consumption report related to the asset or asset item that is a
        consuming unit, return Null if the volume doesn't exist"""
        try:
            volume = self.cache.queryset_metering_report_data.get(report__id=id_report, id_company__id_company=id_company).consumption_values.get().total_consumption_loss
            loss = self.cache.queryset_metering_report_data.get(report__id=id_report, id_company__id_company=id_company).consumption_values.get().loss
        except MeteringReportData.DoesNotExist:
            volume = None
            loss = None
        except Exception:
            self.logger.error('Attempting to get lost volume consumed failed.')
            volume = None
            loss = None
        return volume, loss

    def save_profile_proinfa(self, asset, profile_balance):
        proinfa_type = get_one_by_property_value(self.cache.detailed_balance_types, 'description', 'PROINFA')
        proinfa_detailed_balance_type = DetailedBalanceType(id=proinfa_type.id)
        month = profile_balance.id_report.month
        year = profile_balance.id_report.year

        try:
            # Reverting to queryset for best performance
            proinfa_volume = getattr(asset.id_ccee_proinfa.id_ccee_SeasonalityProinfa.get(id_seasonality__year=year).id_seasonality, month_name[month].lower())
        except (SeasonalityProinfa.DoesNotExist, AttributeError):
            proinfa_volume = None
        except Exception as e:
            proinfa_volume = None
            self.logger.error('Failed to save profile\'s proinfa')

        # The PROINFA unity is set to the profile's name because it is used as a filter on market settlement
        profile = get_one_by_property_value(self.cache.profiles, 'id_profile', asset.id_profile_id)
        new_profile_detailed_balance = self.save_detailed_balance(profile_balance, proinfa_detailed_balance_type,
        asset.id_submarket_id, proinfa_volume, contract_name='PROINFA', unity=profile.name_profile)
    
    def save_detailed_balance(self,
                              profile_balance,
                              balance_type,
                              submarket,
                              volume,
                              unity = None,
                              contract_cliq = None,
                              contract_name = None,
                              fare = None,
                              amount = None,
                              loss = None,
                              gsf = None):
        """Saves a new Detailed Balance, it's parameters are generic because there are four possible detailed balance types"""
        new_detailed_balance = DetailedBalance()
        new_detailed_balance.id_contract_cliq = contract_cliq.id if contract_cliq else None
        new_detailed_balance.contract_name = contract_name
        new_detailed_balance.contract_id = contract_cliq.contract_cliq if contract_cliq else None
        new_detailed_balance.id_submarket = Submarket(id_submarket=submarket)
        new_detailed_balance.volume = volume
        new_detailed_balance.fare = fare
        new_detailed_balance.amount = amount
        new_detailed_balance.unity = unity
        new_detailed_balance.loss = loss
        new_detailed_balance.gsf = gsf
        new_detailed_balance.id_balance = profile_balance
        new_detailed_balance.id_detailed_balance_type = balance_type

        # Saving the new detailed balance
        new_detailed_balance.save()
        return new_detailed_balance

    def save_macro_balance(self, balance, calculate_volume):
        """Saves a new macro balance, works for profile or agent balances"""
        new_macro_balance = MacroBalance()
        new_macro_balance.consumption = calculate_volume(balance, 'CONSUMPTION')
        new_macro_balance.generation = calculate_volume(balance, 'GENERATION')
        new_macro_balance.proinfa = calculate_volume(balance, 'PROINFA')
        new_macro_balance.id_balance = balance

        if balance.id_balance_type.description == 'AGENT':
            new_macro_balance.purchase = calculate_volume(balance, 'PURCHASE')
            new_macro_balance.sale = calculate_volume(balance, 'SALE')

        # Saving the new macro balance
        new_macro_balance.save()
        return new_macro_balance

    def calculate_profile_volume(self, profile_balance, balance_type_description):
        """Sums the volume, of specified balance_type_description, for profiles macro balance"""
        balance_type_description = balance_type_description.upper()
        return profile_balance.detailed_balance.filter(id_detailed_balance_type__description__iexact=balance_type_description).aggregate(total_volume=Sum('volume'))['total_volume']

    def calculate_agent_volume(self, agent_balance, column_to_sum):
        """Sums the volume, of the specified column_to_sum, for agents macro balance"""
        column_to_sum = column_to_sum.lower()
        return agent_balance.agent_balance.aggregate(total_volume=Sum(f'macro_balance__{column_to_sum}'))['total_volume']

    def save_initial_market_settlement(self, profile_balance, market_settlement_id_list):
        """Saves an the sum of consumption and generation for market settlement for each submarket as an initial value, those
        values will be updated later by another method that calculates the final market settlment"""

        new_market_settlement = MarketSettlement()
        new_market_settlement.profile_name = profile_balance.name
        new_market_settlement.id_balance = profile_balance
        new_market_settlement.amount_seco = self.calculate_market_initial_value(profile_balance, 'SE/CO')
        new_market_settlement.amount_s = self.calculate_market_initial_value(profile_balance, 'S')
        new_market_settlement.amount_ne = self.calculate_market_initial_value(profile_balance, 'NE')
        new_market_settlement.amount_n = self.calculate_market_initial_value(profile_balance, 'N')

        # Saving the new market settlement
        new_market_settlement.save()
        market_settlement_id_list.append(new_market_settlement.id)
        return new_market_settlement

    def calculate_market_initial_value(self, profile_balance, submarket):
        """Calculates the difference between generation and consumption for each submarket given a profile 
        balance"""
        generation = none_to_zero(self.fetch_detailed_volume_by_submarket(profile_balance, submarket, 'GENERATION'))
        consumption = none_to_zero(self.fetch_detailed_volume_by_submarket(profile_balance, submarket, 'CONSUMPTION'))
        return generation - consumption

    def fetch_detailed_volume_by_submarket(self, profile_balance, submarket, detailed_balance_type):
        return profile_balance.detailed_balance.filter(id_detailed_balance_type__description__iexact=detailed_balance_type,
        id_submarket__description__iexact=submarket).aggregate(total_volume=Coalesce(Sum('volume'), V(0)))['total_volume']
   
    def calculate_balance(self, balance_report, market_settlement_id_list):
        market_settlement_list = self.cache.queryset_market_settlement.filter(id__in=market_settlement_id_list)
        
        for market_settlement in market_settlement_list:
            self.executed_cliqs[market_settlement.profile_name] = {
                'N': Decimal('0.0'),
                'NE': Decimal('0.0'),
                'SE/CO': Decimal('0.0'),
                'S': Decimal('0.0')
            }

        priorized_cliq_list = balance_report.cliq_report.exclude(double_status='I')
        
        for cliq in priorized_cliq_list:
            try:
                buyer_balance = market_settlement_list.get(profile_name__iexact=cliq.buyer_profile)
            except MarketSettlement.DoesNotExist:
                buyer_profile = get_one_by_property_value(self.cache.profiles, 'id_profile', cliq.id_buyer_profile)
                buyer_balance = market_settlement_list.get(profile_name__iexact=buyer_profile.name_profile)
            vendor_balance = market_settlement_list.get(profile_name__iexact=cliq.vendor_profile)
            submarket = get_one_by_property_value(self.cache.submarkets, 'id_submarket', cliq.id_submarket)
            submarket_description = submarket.description
            volume = self.calculate_cliq_volume(cliq, buyer_balance, vendor_balance, submarket_description)
            
             # The calculated volume is negative
            contract_volume = volume.copy_abs() if volume is not None else Decimal('0.0')
            try:
                self.save_cliq_detailed_balance(balance_report, cliq.buyer_profile, cliq, contract_volume, 'PURCHASE')
            except Balance.DoesNotExist:
                self.save_cliq_detailed_balance(balance_report, buyer_profile.name_profile, cliq, contract_volume, 'PURCHASE')
            self.save_cliq_detailed_balance(balance_report, cliq.vendor_profile, cliq, contract_volume, 'SALE')
            self.update_market_settlement_amount(buyer_balance, submarket_description, contract_volume)
            self.update_market_settlement_amount(vendor_balance, submarket_description, contract_volume.copy_negate() if contract_volume is not Decimal('0.0') else Decimal('0.0'))

    def save_cliq_detailed_balance(self, balance_report, profile_name: str, cliq, volume, detailed_balance_type: str):
        cliq_submarket = get_one_by_property_value(self.cache.submarkets, 'id_submarket', cliq.id_submarket)
        detailed_type = get_one_by_property_value(self.cache.detailed_balance_types, 'description', detailed_balance_type)
        detailed_balance_type = DetailedBalanceType(id=detailed_type.id)
        profile_balance = self.cache.queryset_balance.get(id_report=balance_report, id_balance_type__description__iexact='PROFILE', name__iexact=profile_name)

        if cliq.cliq_type.lower() not in 'transferencia':
            amount = volume*cliq.fare
        else:
            amount = None

        new_detailed_balance = self.save_detailed_balance(profile_balance, detailed_balance_type, cliq_submarket.id_submarket, volume,
        contract_cliq=cliq, contract_name=cliq.contract_name, fare=cliq.fare, amount=amount)

    def calculate_cliq_volume(self, cliq, buyer_balance, vendor_balance, submarket):

        cliq_instance = CliqContract.objects.get(pk=cliq.cliq_id)
        consider_submarket = cliq_instance.submarket

        if cliq.cliq_type.lower() in 'flat':
            cliq_volume = self.calculate_cliq_seasonalization(cliq, cliq_instance)
            contract_volume = cliq_volume.copy_negate() # flat volume must be negative to match flexible volume results
            self.update_executed_cliqs(buyer_balance.profile_name, submarket, contract_volume.copy_negate())
            self.update_executed_cliqs(vendor_balance.profile_name, submarket, contract_volume)
        elif cliq.cliq_type.lower() in 'flexivel':
            contract_volume = self.calculate_flexible_volume(cliq, cliq_instance, buyer_balance, vendor_balance, consider_submarket)
        elif cliq.cliq_type.lower() in 'transferencia':
            contract_volume = self.calculate_transference_volume(cliq, buyer_balance, vendor_balance, submarket, consider_submarket)
        return contract_volume

    def calculate_transference_volume(self, cliq, buyer_balance, vendor_balance, submarket, consider_submarket):
        """Calculates a transference cliq volume."""
        if 'comprador' in cliq.transaction_type.lower():
            transfer_volume = self.calculate_zero_buyer(cliq, buyer_balance, consider_submarket)
        elif 'vendedor' in cliq.transaction_type.lower():
            transfer_volume = self.calculate_zero_vendor(cliq, vendor_balance, consider_submarket)
        elif 'balanceado' in cliq.transaction_type.lower():
            transfer_volume = self.calculate_balanced(cliq, buyer_balance, vendor_balance, consider_submarket)
        elif 'volume_fixo' in cliq.transaction_type.lower():
            transfer_volume = self.calculate_fixed_transfer_volume(cliq)
        return transfer_volume

    def calculate_cliq_seasonalization(self, cliq, cliq_instance):
        """Calculates cliq volume if it has seasonalization. If a cliq flexibility is 'PONTA E FORA PONTA'
        this function returns a tuple because, for this specific contract, this values are treated separately"""
        if cliq.flexibility_type_is_conventional:
            volume = cliq.volume
        elif cliq.flexibility_is_peak_or_off_peak:
            year = int(cliq.id_report.year)
            month = int(cliq.id_report.month)
            if cliq.flexibility == 'PONTA':
                volume_mwm = cliq_instance.mwm_volume_peak
            elif cliq.flexibility == 'FORA PONTA':
                volume_mwm = cliq_instance.mwm_volume_offpeak
            elif cliq.flexibility == 'PONTA E FORA PONTA':
                peak_volume_mwm = mwm_to_mwh(year, month, cliq_instance.mwm_volume_peak)
                off_peak_volume = mwm_to_mwh(year, month, cliq_instance.mwm_volume_offpeak)
                return (peak_volume_mwm, off_peak_volume)
            volume = mwm_to_mwh(year, month, volume_mwm)
        else: # cliq is flat
            volume = cliq.volume
        return volume*cliq.seasonality if cliq.seasonality is not None else volume

    def update_executed_cliqs(self, profile_name, submarket, volume):
        self.executed_cliqs[profile_name][submarket] += none_to_zero(volume)

    def update_market_settlement_amount(self, market_settlement, submarket: str, volume):
        """Updates the market settlement amount given a submarket and a volume to be added"""
        amount_submarket = self.generate_market_settlement_submarket_name(submarket)
        current_volume = getattr(market_settlement, amount_submarket)
        setattr(market_settlement, amount_submarket, current_volume + volume if volume is not None else Decimal(0.0))
        market_settlement.save()

    def generate_market_settlement_submarket_name(self, submarket: str) -> str:
        """Generates the name of the MarketSettlment field given a string with the submarket description (from the 
        description field of the Submarket model)"""
        regex = re.compile('[^a-zA-Z]')
        cleaned_submarket = regex.sub('', submarket).lower()
        return f'amount_{cleaned_submarket}'

    def calculate_flexible_volume(self, cliq, cliq_instance, buyer_balance, vendor_balance, consider_submarket):
        """Calculates a flexible cliq volume taking into consideration its transaction type"""
        if cliq.flexibility == 'PONTA E FORA PONTA':
            reference_volume = self.calculate_peak_and_off_peak_volume(cliq, buyer_balance, vendor_balance, consider_submarket)
            contract_volume = self.calculate_flexible_contract_volume(reference_volume, cliq, cliq_instance, buyer_balance, vendor_balance)
            return contract_volume
        if cliq.transaction_type.upper() == 'VOLUME_FIXO':
            reference_volume = self.calculate_fixed_volume(cliq, buyer_balance, vendor_balance, consider_submarket)
        elif cliq.transaction_type.upper() in ['ZERAR_COMPRADOR', 'ZERAR_VENDEDOR', 'BALANCEADO']:
            reference_volume = self.calculated_non_fixed_volume(cliq, buyer_balance, vendor_balance, consider_submarket)
        contract_volume = self.calculate_flexible_contract_volume(reference_volume, cliq, cliq_instance, buyer_balance, vendor_balance)
        return contract_volume
    
    def calculate_fixed_volume(self, cliq, buyer_balance, vendor_balance, consider_submarket):
        """Calculates a flexible cliq reference volume when its transaction type is 'VOLUME_FIXO'"""
        profile_consumed_volume = self.calculate_custom_volume(cliq, buyer_balance, False, 'CONSUMPTION')
        consumer_volume = self.calculate_consumer_volume(cliq, buyer_balance, consider_submarket, profile_consumed_volume)
        executed_cliqs = self.calculate_executed_cliqs(cliq, buyer_balance, consider_submarket)
        proinfa = self.calculate_proinfa_volume(cliq, buyer_balance, consider_submarket)
        generation = self.calculate_custom_volume(cliq, buyer_balance, consider_submarket, 'GENERATION')

        reference_volume = self.generic_reference_volume_equation(consumer_volume, profile_consumed_volume, \
            executed_cliqs, proinfa, generation)
        return reference_volume

    def generic_reference_volume_equation(self, consumer_volume, profile_consumed_volume, executed_cliqs, proinfa, generation):
        """Generic equation for flexible cliqs with transaction type set to 'VOLUME_FIXO'"""
        consumption_ratio = consumer_volume/profile_consumed_volume if profile_consumed_volume != Decimal('0.0') else Decimal('0.0')
        reference_volume = -consumer_volume + consumption_ratio*(executed_cliqs + proinfa + generation)
        return reference_volume

    def calculate_custom_volume(self, cliq, buyer_balance, consider_submarket, type_description: str):
        """Calculates the sum of a given DETAILED_BALANCE filtering by submarket given the consider_submarket
        flag and the DETAILED_BALANCE type description for the buyer_balance"""
        calculate_partial_balance = self.calculate_partial_balance_by_submarket if consider_submarket \
            else self.calculate_profile_partial_balance
        return calculate_partial_balance(buyer_balance, type_description, cliq.id_submarket)
    
    def calculate_consumer_volume(self, cliq, buyer_balance, consider_submarket, profile_consumed_volume):
        """Calculates de consumer volume based on the consider_submarket flag. The consumer might be a profile,
        asset or asset item. If the consumer is an asset or asset item the flexibility might be 'CONVENTIONAL',
        'PEAK', 'OFF PEAK' or 'PEAK AND OFF PEAK' """
        if cliq.buyer_is_a_profile:
            # if the buyer is a profile we return the profile volume that was calculated previously
            return profile_consumed_volume
        else:
            return self.calculate_consumption_from_projected_report(cliq)
    
    def calculate_consumption_from_projected_report(self, cliq):
        """Calculates the consumption depending on the cliq's flexibility option. The consumption is fetched from the
        projected report referenced on the balance report. If the flexibility is 'PONTA' or 'FORA PONTA' losses are 
        applied."""
        if cliq.id_buyer_assets:
            buyer_asset = Assets.objects.get(pk=cliq.id_buyer_assets) 
            company_id_list = [buyer_asset.id_company.id_company] if buyer_asset.show_balance == 'Assets' \
                else buyer_asset.assetitems_asset.all().values_list('id_company')
        elif cliq.id_buyer_asset_items:
            buyer_asset_item = AssetItems.objects.get(pk=cliq.id_buyer_asset_items)
            company_id_list = [buyer_asset_item.id_company.id_company]
        
        projected_report = cliq.id_report.id_reference
        metering_report_data_ids = MeteringReportData.objects.filter(
            report__id=projected_report.id, 
            id_company__in=company_id_list
        ).values_list('id')

        consumption_values = MeteringReportValue.objects.filter(
            metering_report_data__in=metering_report_data_ids
        )

        if cliq.flexibility_type_is_conventional:
            consumer_volume = consumption_values.aggregate(
                consumer_volume=Sum('total_consumption_loss')
            )['consumer_volume'] or Decimal('0.0')
        else:
            if cliq.flexibility == 'PONTA':
                consumer_volume = self.calculate_peak_volume(consumption_values)
            elif cliq.flexibility == 'FORA PONTA':
                consumer_volume = self.calculate_off_peak_volume(consumption_values)
            elif cliq.flexibility == 'PONTA E FORA PONTA':
                peak_consumption = self.calculate_peak_volume(consumption_values)
                off_peak_consumption = self.calculate_off_peak_volume(consumption_values)
                return (peak_consumption, off_peak_consumption)
        return consumer_volume

    def calculate_peak_volume(self, metering_report_value_queryset):
        return self.calculate_peak_or_off_peak_volume('on_peak_consumption_value', metering_report_value_queryset)

    def calculate_off_peak_volume(self, metering_report_value_queryset):
        return self.calculate_peak_or_off_peak_volume('off_peak_consumption_value', metering_report_value_queryset)

    def calculate_peak_or_off_peak_volume(self, flexibility_type: str, metering_report_value_queryset):
        consumer_volume = metering_report_value_queryset.annotate(
                loss_type=F('metering_report_data__loss_type'), 
                flexible_volume=F(flexibility_type),
                flexible_volume_with_losses=Case(
                    When(loss_type='1', then=(F('flexible_volume')*(1.0 + F('loss')/100.0))),
                    When(loss_type='2', then=(F('flexible_volume')/(1.0 - F('loss')/100.0)))
                )
            ).values_list(
                'flexible_volume_with_losses'
            ).aggregate(
                consumer_volume=Sum('flexible_volume_with_losses')
            )['consumer_volume'] or Decimal('0.0')
        return consumer_volume

    def calculate_peak_and_off_peak_volume(self, cliq, buyer_balance, vendor_balance, consider_submarket):
        """Calculates a flexible cliq reference volume when its transaction type is 'VOLUME_FIXO'"""
        profile_consumed_volume = self.calculate_custom_volume(cliq, buyer_balance, False, 'CONSUMPTION')
        executed_cliqs = self.calculate_executed_cliqs(cliq, buyer_balance, consider_submarket)
        proinfa = self.calculate_proinfa_volume(cliq, buyer_balance, consider_submarket)
        generation = self.calculate_custom_volume(cliq, buyer_balance, consider_submarket, 'GENERATION')

        peak_consumption, off_peak_consumption = self.calculate_consumption_from_projected_report(cliq)
        peak_reference_volume = self.generic_reference_volume_equation(peak_consumption, profile_consumed_volume, \
                                                                        executed_cliqs, proinfa, generation)
        off_peak_reference_volume = self.generic_reference_volume_equation(off_peak_consumption, profile_consumed_volume, \
                                                                        executed_cliqs, proinfa, generation)
        return (peak_reference_volume, off_peak_reference_volume)

    def calculate_proinfa_volume(self, cliq, buyer_balance, consider_submarket):
        """Returns the proinfa volume by submarket if the consider_submarket flat is True else returns 
        the proinfa for the entire profile. If the buyer is a profile. If the proinfa felixibility flag
        is set to 'N' the proinfa volume won't be considered"""
        consider_proinfa = cliq.proinfa_flexibility == 'S'
        if consider_proinfa:
            proinfa = self.calculate_custom_volume(cliq, buyer_balance, consider_submarket, 'PROINFA')
        else:
            proinfa = Decimal('0.0')
        return proinfa
    
    def calculate_executed_cliqs(self, cliq, buyer_balance, consider_submarket):
        """Calculates the executed cliqs volume for flexible contracts"""
        # If the buyer is an asset or asset item the executed cliq volume should only consider flat, sazonalized and
        # flex contracts which are the lower bound 
        if not cliq.buyer_is_a_profile:
            submarket = self.get_submarket_description_by_cliq(cliq)
            if consider_submarket:
                return self.executed_cliqs[buyer_balance.profile_name][submarket]
            else:
                return sum(self.executed_cliqs[buyer_balance.profile_name].values())
        else:
            # For profiles all cliq contracts should be considered
            sale_contracts_executed_volume = self.calculate_custom_volume(cliq, buyer_balance, consider_submarket, 'SALE')
            purchase_contracts_executed_volume = self.calculate_custom_volume(cliq, buyer_balance, consider_submarket, 'PURCHASE')
            return purchase_contracts_executed_volume - sale_contracts_executed_volume

    def calculated_non_fixed_volume(self, cliq, buyer_balance, vendor_balance, consider_submarket):
        """Calculates a flexible cliq reference volume when its transaction type is 'ZERAR_COMPRADOR',
        'ZERAR_VENDEDOR' or 'BALANCEADO'"""
        if cliq.transaction_type.upper() == 'ZERAR_COMPRADOR':
            transfer_volume = self.calculate_zero_buyer(cliq, buyer_balance, consider_submarket)
        elif cliq.transaction_type.upper() == 'ZERAR_VENDEDOR':
            transfer_volume = self.calculate_zero_vendor(cliq, vendor_balance, consider_submarket) 
        elif cliq.transaction_type.upper() == 'BALANCEADO':
            transfer_volume = self.calculate_balanced(cliq, buyer_balance, vendor_balance, consider_submarket) 
        return transfer_volume

    def calculate_zero_buyer(self, cliq, buyer_balance, consider_submarket):
        """Checks if the transfer volume is less than zero, if so returns zero."""
        transfer_volume = self.calculate_transfer_volume(cliq, buyer_balance, True)
        if not consider_submarket:
            profile_balance = self.calculate_transfer_volume(cliq, buyer_balance, False)
            profile_needs_energy = profile_balance <= Decimal('0.0')
            transfer_volume = transfer_volume if profile_needs_energy else Decimal('0.0')

        return min(transfer_volume, Decimal('0.0'))

    def calculate_zero_vendor(self, cliq, vendor_balance, consider_submarket):
        """Checks if the transfer volume e less than zero, if so returns zero."""
        transfer_volume = self.calculate_transfer_volume(cliq, vendor_balance, True)
        if not consider_submarket:
            profile_balance = self.calculate_transfer_volume(cliq, vendor_balance, False)
            profile_needs_energy = profile_balance >= Decimal('0.0')
            transfer_volume = transfer_volume if profile_needs_energy else Decimal('0.0')

        # The sign of the transfer volume for zero vendor should be flipped for the later logic work and the
        # vendor volume be turned to zero
        transfer_volume = max(transfer_volume,  Decimal('0.0'))
        if transfer_volume != Decimal('0.0'):
            transfer_volume = transfer_volume.copy_negate()
        return transfer_volume
    
    def calculate_balanced(self, cliq, buyer_balance, vendor_balance, consider_submarket):
        """Calculates the transfer volume for the cases 'ZERAR_COMPRADOR' and 'ZERAR_VENDEDOR' and returns the 
        lowest volume. In this case we use max because the transfer volume is negative"""
        vendor_has_energy = self.calculate_transfer_volume(cliq, vendor_balance, consider_submarket) > Decimal('0.0')
        if not vendor_has_energy:
            return Decimal('0.0')

        buyer_needs_energy = self.calculate_transfer_volume(cliq, buyer_balance, consider_submarket) < Decimal('0.0')
        if not buyer_needs_energy:
            return Decimal('0.0')

        # Since we validated if the vendor and buyer balances we don't need to execute the verifications again
        # So we call the following function with the filter_submarket flag equal to False
        zero_buyer = self.calculate_transfer_volume(cliq, buyer_balance, False)
        zero_vendor = self.calculate_transfer_volume(cliq, vendor_balance, False).copy_negate()
        return max(zero_buyer, zero_vendor)

    def calculate_transfer_volume(self, cliq, profile_balance, filter_submarket):
        """Calculates the transfer volume for contracts given the buyer or vendor profile."""
        id_submarket = cliq.id_submarket
        calculate_partial_balance = self.calculate_partial_balance_by_submarket if filter_submarket \
            else self.calculate_profile_partial_balance

        consumption = calculate_partial_balance(profile_balance, 'CONSUMPTION', id_submarket)
        sale = calculate_partial_balance(profile_balance, 'SALE', id_submarket)
        generation = calculate_partial_balance(profile_balance, 'GENERATION', id_submarket)
        purchase = calculate_partial_balance(profile_balance, 'PURCHASE', id_submarket)
        
        consider_proinfa = cliq.proinfa_flexibility == 'S'
        if consider_proinfa:
            proinfa = calculate_partial_balance(profile_balance, 'PROINFA', id_submarket)
        else:
            proinfa = Decimal('0.0')

        transfer_volume = generation + purchase + proinfa - consumption - sale
        return transfer_volume

    def calculate_fixed_transfer_volume(self, cliq):
        """Returns the cliq volume."""
        return none_to_zero(cliq.volume)

    def calculate_partial_balance_by_submarket(self, profile_market_settlement, consumption_type_description: str, id_submarket: int):
        """Calculates the total profile volume given a submarket id and consumption type. This functions receives a 
        market settlement and uses it to get a balance and filter its detailed balances by type and submarket id."""
        profile_volume_by_submarket = profile_market_settlement.id_balance.detailed_balance.filter(
            id_detailed_balance_type__description=consumption_type_description, 
            id_submarket=id_submarket
        ).aggregate(
            total_volume=Sum('volume')
        )['total_volume']
        return none_to_zero(profile_volume_by_submarket)

    def calculate_profile_partial_balance(self, profile_market_settlement, consumption_type_description: str, id_submarket: int):
        """Calculates the partial balance for a profile without considering the submarket given a consumption type. 
        This functions receives a market settlement and uses it to get a balance and filter its detailed balances by type."""
        profile_partial_balance = profile_market_settlement.id_balance.detailed_balance.filter(
            id_detailed_balance_type__description=consumption_type_description, 
        ).aggregate(
            total_volume=Sum('volume')
        )['total_volume']
        return none_to_zero(profile_partial_balance)
   
    def calculate_flexible_contract_volume(self, reference_volume, cliq, cliq_instance, buyer_balance, vendor_balance):
        contract_volume, should_add_to_executed_cliqs = self.compare_volume_with_limits(reference_volume, cliq, cliq_instance)

        if should_add_to_executed_cliqs:
            # If the contract volume is equal do the upper bound (taking into consideration that the limits are flipped)
            # its volume should be added to the executed cliqs term
            submarket = self.get_submarket_description_by_cliq(cliq)
            self.update_executed_cliqs(buyer_balance.profile_name, submarket, contract_volume.copy_negate())
            self.update_executed_cliqs(vendor_balance.profile_name, submarket, contract_volume)

        return contract_volume

    def compare_volume_with_limits(self, reference_volume, cliq, cliq_instance):
        """Calculates the upper and lower bounds for a cliq using it's flexibility limits, the peak limits are stored
        on their own column but the conventional and off pean limits are stored on the same column on the energy
        contract module. The flow for 'PONTA E FORA PONTA' flexibility is treated differently because this contract
        was added later."""
        cliq_seasonality_volume = self.calculate_cliq_seasonalization(cliq, cliq_instance)
        cliq_flexibilization = cliq_instance.id_contract.flexib_energy_contract
        flexibility_type = cliq.flexibility

        
        if flexibility_type == 'PONTA' or cliq.flexibility_type_is_conventional:
            max_flexibility = cliq_flexibilization.max_flexibility_pu_peak or Decimal('0.0')
            min_flexibility = cliq_flexibilization.min_flexibility_pu_peak or Decimal('0.0')
        elif flexibility_type == 'FORA PONTA':
            max_flexibility = cliq_flexibilization.max_flexibility_pu_offpeak or Decimal('0.0')
            min_flexibility = cliq_flexibilization.min_flexibility_pu_offpeak or Decimal('0.0')
        elif flexibility_type == 'PONTA E FORA PONTA':
            reference_peak, reference_off_peak = reference_volume
            cliq_peak, cliq_off_peak = self.calculate_cliq_seasonalization(cliq, cliq_instance)

            max_flexibility_peak = cliq_flexibilization.max_flexibility_pu_peak or Decimal('0.0')
            min_flexibility_peak = cliq_flexibilization.min_flexibility_pu_peak or Decimal('0.0')
            max_flexibility_off_peak = cliq_flexibilization.max_flexibility_pu_offpeak or Decimal('0.0')
            min_flexibility_off_peak = cliq_flexibilization.min_flexibility_pu_offpeak or Decimal('0.0')

            lower_bound_peak = self.calculate_volume_limits(cliq_peak, max_flexibility_peak)
            upper_bound_peak = self.calculate_volume_limits(cliq_peak, min_flexibility_peak)
            peak_volume = clamp(reference_peak, lower_bound_peak, upper_bound_peak)

            lower_bound_off_peak = self.calculate_volume_limits(cliq_off_peak, max_flexibility_off_peak)
            upper_bound_off_peak = self.calculate_volume_limits(cliq_off_peak, min_flexibility_off_peak)
            off_peak_volume = clamp(reference_off_peak, lower_bound_off_peak, upper_bound_off_peak)

            should_add_to_executed_cliqs = (peak_volume == upper_bound_peak) and \
                (off_peak_volume == upper_bound_off_peak)

            return (peak_volume + off_peak_volume, should_add_to_executed_cliqs)

        # Inverting limits because the reference volume is negative most of the time
        lower_bound = self.calculate_volume_limits(cliq_seasonality_volume, max_flexibility)
        upper_bound = self.calculate_volume_limits(cliq_seasonality_volume, min_flexibility)
        contract_volume = clamp(reference_volume, lower_bound, upper_bound)
        should_add_to_executed_cliqs = contract_volume == upper_bound
        return (contract_volume, should_add_to_executed_cliqs)

    def calculate_volume_limits(self, volume, limit):
        """Multiplies a volume by ones of it's limits, the limits are flipped for latter logic to work.
        All inputs should be Decimal"""
        return volume*limit.copy_negate()

    def get_submarket_description_by_cliq(self, cliq):
        return get_one_by_property_value(self.cache.submarkets, 'id_submarket', cliq.id_submarket).description

    def calculate_market_settlement(self, balance_report, market_settlement_id_list):
        market_settlement_list = self.cache.queryset_market_settlement.filter(id__in=market_settlement_id_list)

        for market_settlement in market_settlement_list:
            self.save_submarkets_settlement(balance_report, market_settlement)
            self.save_market_settlement_saleoff(market_settlement)

    def generate_submarket_list(self):
        """Returns a list of all submarkets' names, lowercase without any non alphabetic characters"""
        submarkets = self.cache.submarkets
        regex = re.compile('[^a-zA-Z]')
        submarket_list = []

        for submarket in submarkets:
            submarket_name = submarket.description
            submarket_list.append(regex.sub('', submarket_name).lower())
        return submarket_list

    def save_submarkets_settlement(self, balance_report, market_settlement):
        submarket_list = self.generate_submarket_list()
        balance_fields = balance_report.report_balance.get()

        for submarket in submarket_list:
            amount_name = f'amount_{submarket}'
            pld_name = f'pld_{submarket}'

            submarket_upper = {
                's': 'S',
                'seco': 'SE/CO',
                'n': 'N',
                'ne': 'NE'
            }
            submkt = submarket_upper[submarket]

            try:
                proinfa = none_to_zero(market_settlement.id_balance.detailed_balance.filter(id_submarket__description__iexact=submkt, unity__iexact=market_settlement.profile_name).aggregate(total_volume=Sum('volume'))['total_volume'])
            except DetailedBalance.DoesNotExist:
                proinfa = Decimal()

            submarket_balance = getattr(market_settlement, amount_name) + proinfa
            submarket_pld = getattr(balance_fields, pld_name)

            setattr(market_settlement, amount_name, submarket_balance*submarket_pld)
        market_settlement.save()

    def save_market_settlement_saleoff(self, market_settlement):
        submarket_list = self.generate_submarket_list()
        saleoff = Decimal()

        for submarket in submarket_list:
            amount_name = f'amount_{submarket}'
            saleoff += getattr(market_settlement, amount_name)
        market_settlement.saleoff = saleoff
        market_settlement.save()

    def update_profile_macro_balance(self, report_balance):
        profile_balance_list = report_balance.balance_set.filter(id_balance_type__description__iexact='PROFILE')

        for profile_balance in profile_balance_list:
            profile_macro_balance = profile_balance.macro_balance.get()
            profile_macro_balance.purchase = self.calculate_profile_volume(profile_balance, 'PURCHASE')
            profile_macro_balance.sale = self.calculate_profile_volume(profile_balance, 'SALE')
            profile_macro_balance.save()

    def save_agent_macro_balance(self, report_balance):
        agent_balance_list = report_balance.balance_set.filter(id_balance_type__description__iexact='AGENT')

        for agent_balance in agent_balance_list:
            self.save_macro_balance(agent_balance, self.calculate_agent_volume)

    def update_balance_value(self, report_balance):
        balance_list = report_balance.balance_set.all()

        for balance in balance_list:
            macro_balance = balance.macro_balance.get()
            balance.value = none_to_zero(macro_balance.generation) + none_to_zero(macro_balance.purchase) \
                            + none_to_zero(macro_balance.proinfa) - none_to_zero(macro_balance.sale) \
                            - none_to_zero(macro_balance.consumption)
            balance.save()

    @transaction.atomic
    def save_balance(self, balance, username):
        """Changes balance status to Saved 'S'."""
        # Checks if balance is already consolidated
        if balance.status == 'S':
            raise AlreadySaved
        # Checks if today is before or equal the 8th workday of saved balance's following month
        if((int(balance.month)+1)%12 > 0):
            balance_date = date(int(balance.year)+1, 1, 1)
        else:
            balance_date = date(int(balance.year), int(balance.month)+1, 1)
        if not is_before_or_equal_nth_brazilian_workday(balance_date.year, balance_date.month, WORK_DAY_LIMIT):
            raise PastDateLimit

        balance.status = 'S'
        balance.report_name = gen_report_name(balance.report_type.initials, balance.month, balance.year)
        balance.creation_date = datetime.now(timezone.utc)
        balance.save(update_fields=['status'])

        try:
            old_balances_queryset = Report.objects.filter(month=balance.month, year=balance.year, status__in=['S', 'C'], report_type__initials__exact='BDE')
            old_balance = old_balances_queryset.exclude(id=balance.id).latest('id')
            HistoryService().save_history_balance(balance, 'Alteração de STATUS Temporário para Salvo.', username, old_balance)
        except Report.DoesNotExist:
            HistoryService().save_history_balance(balance, 'Alteração de STATUS Temporário para Salvo.', username)
        return balance

    @transaction.atomic
    def consolidate_balance(self, pk, username):
        """Consolidates a balance given it's id, no validations are made before consolidating"""
        balance_queryset = Report.objects.filter(report_type__initials__exact='BDE')
        balance = balance_queryset.get(id=pk)
        balances_by_month = balance_queryset.filter(year=balance.year, month=balance.month)
        last_balance_by_month = balances_by_month.filter(status='S').latest('id')
        consolidated_balance_by_month = balances_by_month.filter(status='C')
        old_balance = deepcopy(Report.objects.get(id=pk))

        # Checks if the balance is the lastest one
        if (balance.id == last_balance_by_month.id):
            # Checks if balance is already consolidated
            if balance.status == 'C':
                raise AlreadyConsolidated
            # Checks if today is before or equal the 8th workday of saved balance's following month
            if((int(balance.month)+1)%12 > 0):
                balance_date = date(int(balance.year)+1, 1, 1)
            else:
                balance_date = date(int(balance.year), int(balance.month)+1, 1)
            if not is_before_or_equal_nth_brazilian_workday(balance_date.year, balance_date.month, WORK_DAY_LIMIT):
                raise PastDateLimit

            # Checks if there is a consolidated balance last month, if there is change its status
            if consolidated_balance_by_month.exists():
                try:
                    consolidated_balance_by_month.update(status='S', report_name=consolidated_balance_by_month.first().report_name[:-2])
                    HistoryService().save_history_balance(consolidated_balance_by_month.latest('id'), 'Alteração de STATUS Consolidado para Salvo.', username)
                except Report.DoesNotExist:
                    pass
        else:
            raise OutOfDate

        # Consolidating the balance:
        balance.status = 'C'
        balance.report_name = f'{balance.report_name}_C'
        balance.save(update_fields=['status', 'report_name'])
        HistoryService().save_history_balance(balance, 'Alteração de STATUS Salvo para Consolidado.', username, old_balance)
        return balance

    def report_check_modification_by_request(self, request, balance):
        """Check if the balance was any modification before change its status to Save(S)."""
        if not (request.data['id_reference'] == balance.id_reference.id):
            return False

        if not (request.data['report_name'] == balance.report_name):
            return False

        if not (request.data['month'] == balance.month):
            return False

        if not (request.data['year'] == balance.year):
            return False

        request_balance_fields = request.data['balance_fields']
        saved_balance_fields = BalanceFields.objects.get(id_report=request.data['id'])

        if not (request_balance_fields['month'] == saved_balance_fields.month):
            return False

        if not (request_balance_fields['id_rcd'] == saved_balance_fields.id_report_rcd.id):
            return False

        if not (request_balance_fields['gsf'] == str(saved_balance_fields.gsf)):
            return False

        if not (request_balance_fields['pld_n'] == str(saved_balance_fields.pld_n)):
            return False

        if not (request_balance_fields['pld_ne'] == str(saved_balance_fields.pld_ne)):
            return False

        if not (request_balance_fields['pld_seco'] == str(saved_balance_fields.pld_seco)):
            return False

        if not (request_balance_fields['pld_s'] == str(saved_balance_fields.pld_s)):
            return False

        priorized_cliq = request.data['priorized_cliq']
        saved_priorized_cliq = PriorizedCliq.objects.filter(id_report__id__exact=request.data['id'])

        cliq_id_concat = ''
        for cliq in priorized_cliq:
            cliq_id_concat = cliq_id_concat + str(cliq['id'])

        saved_id_concat = ''
        for saved_cliq in saved_priorized_cliq:
            saved_id_concat = saved_id_concat + str(saved_cliq.id)

        if not (cliq_id_concat == saved_id_concat):
            return False

        return True

    def get_last_balance_fields(self):
        """Retrieves the fields from the last saved balance"""
        try:
            obj = BalanceFields.objects.filter(id_report__isnull=False, id_report__status__in=['S', 'C']).latest('id_report')
            obj.id = None
            return Response(BalanceFieldsSerializer(obj).data)
        except BalanceFields.DoesNotExist:
            response_data = {
                "id": None,
                "month": None,
                "year": None,
                "id_rcd": None,
                "rcd_name": None,
                "gsf": 0,
                "pld_n": 0,
                "pld_ne": 0,
                "pld_seco": 0,
                "pld_s": 0
            }
            serializer = BalanceFieldsSerializer(response_data)
            return Response(serializer.data)
    
    def get_cliq_contracts(self, month, year):
        """Retrieves cliq contracts for ordering"""
        queryset = self.get_cliq_contract_queryset(month, year)
        try:
            last_balance = Report.objects.filter(
                report_type__initials__exact='BDE',
                status__in=['S', 'C']).latest('id')
            priorized_cliq_ids = last_balance.get_priorized_cliq.values_list('cliq_id', flat=True)
            sorted_saved_cliqs = last_balance.get_priorized_cliq
            in_priorized_cliq_ids = Q(id_contract_cliq__in=priorized_cliq_ids)
        except Report.DoesNotExist:
            sorted_saved_cliqs = PriorizedCliq.objects.none()
            in_priorized_cliq_ids = Q(id_contract_cliq__in=[Decimal('0')])

        new_contracts = queryset.exclude(in_priorized_cliq_ids).annotate(
            new=Value(True, output_field=BooleanField())
        )

        if len(sorted_saved_cliqs) == 0 and len(new_contracts) == 0:
            new_contracts = queryset.annotate(
                new=Value(True, output_field=BooleanField())
            )

        # No one saved balance
        if not sorted_saved_cliqs.exists() and new_contracts.exists():
            return self.generate_new_contracts_list(new_contracts)
        # Saved balance and no one new contracts
        elif sorted_saved_cliqs.exists() and not new_contracts.exists():
            sorted_profiles = self.generate_saved_contracts_list(sorted_saved_cliqs, queryset)
            sorted_profiles = self.check_saved_consistency(sorted_profiles, queryset)
            return sorted_profiles
        # Saved balance with new contracts
        elif sorted_saved_cliqs.exists() and new_contracts.exists():
            sorted_profiles = self.generate_saved_contracts_list(sorted_saved_cliqs, queryset)
            self.merge_new_with_saved_contracts(sorted_profiles, new_contracts)
            self.set_double_status_and_profile(sorted_profiles)
            sorted_profiles = self.check_saved_consistency(sorted_profiles, queryset)
            return sorted_profiles

    def get_cliq_contract_queryset(self, month, year):
        """Consult the current contracts cliq within the month and year"""
        first_day = datetime(year, month, 1, 0, 0, 0, tzinfo=timezone.utc)
        last_day = datetime(year, month, monthrange(year, month)[1], 0, 0, 0, tzinfo=timezone.utc)
        start_date_filter = Q(id_contract__start_supply__lte=last_day)
        end_date_filter = Q(id_contract__end_supply__gte=first_day)
        active_contract_filter = Q(status='S', id_contract__status='S')

        return CliqContract.objects.filter(
            start_date_filter &
            end_date_filter &
            active_contract_filter
        ).annotate(contract_type=Case(
            When(id_contract__modality='transferencia',
                 then=Value('transferencia', output_field=CharField())),
            When(id_contract__flexib_energy_contract__flexibility_type='flexivel',
                 then=Value('flexivel', output_field=CharField())),
            When(id_contract__flexib_energy_contract__flexibility_type='flat',
                 then=Value('flat', output_field=CharField())),
            When(id_contract__flexib_energy_contract__flexibility_type__icontains='proporcional',
                 then=Value('flexivel', output_field=CharField())),
            default=None,
            output_field=CharField()
        ), proportional_flexible=Case(
            When(id_contract__flexib_energy_contract__flexibility_type__icontains='proporcional',
                 then=Value(True, output_field=BooleanField())),
            default=False,
            output_field=BooleanField(),
        ), active_price_mwh=Case(
            When(id_contract__flexib_energy_contract__flexibility_type='flexivel',
                 then=F('id_contract__precif_energy_contract__active_price_mwh')),
            When(id_contract__flexib_energy_contract__flexibility_type__icontains='proporcional',
                 then=F('id_contract__precif_energy_contract__active_price_mwh')),
            default=Decimal('0'),
            output_field=DecimalField()
        ), double_status=Value(None, output_field=CharField()),
            priorized_profile_id=Value(None, output_field=DecimalField()))

    def check_saved_consistency(self, sorted_profiles, queryset):
        """Checks the consistency of the list obtained"""
        new_contracts = queryset.annotate(new=Value(True, output_field=BooleanField()))
        if len(sorted_profiles) == 0:
            return self.generate_new_contracts_list(new_contracts)
        for profile in sorted_profiles:
            founded = list(filter(lambda x: x.profile_id == profile.profile_id, sorted_profiles))
            if len(founded) > 1:
                return self.generate_new_contracts_list(new_contracts)
        return sorted_profiles

    def merge_new_with_saved_contracts(self, saved_contracts, new_contracts):
        """Merges lists of saved contracts with new contracts"""
        for new_contract in new_contracts:
            try:
                if new_contract.id_buyer_profile_id is not None:
                    profiles_list = [new_contract.id_buyer_profile_id, new_contract.id_vendor_profile_id]
                elif new_contract.id_buyer_assets_id is not None:
                    profiles_list = [new_contract.id_buyer_assets.id_profile_id, new_contract.id_vendor_profile_id]
                elif new_contract.id_buyer_asset_items_id is not None:
                    profiles_list = [new_contract.id_buyer_asset_items.id_assets.id_profile_id, new_contract.id_vendor_profile_id]

                profile_filter = Q(id_profile__in=profiles_list,
                                   id_agents__id_company__type='I'
                                   )
                profiles = Profile.objects.filter(profile_filter)
            except Profile.DoesNotFound:
                continue

            for profile in profiles:
                founded_purchase = False
                founded_sale = False

                if new_contract.id_buyer_profile_id is not None:
                    purchase_buyer_reference = new_contract.id_buyer_profile_id
                elif new_contract.id_buyer_assets_id is not None:
                    purchase_buyer_reference = new_contract.id_buyer_assets.id_profile_id
                elif new_contract.id_buyer_asset_items_id is not None:
                    purchase_buyer_reference = new_contract.id_buyer_asset_items.id_assets.id_profile_id

                for saved_contract in saved_contracts:
                    if profile.id_profile == saved_contract.profile_id:
                        for contract in saved_contract.contracts:
                            if purchase_buyer_reference == profile.id_profile and\
                                    contract.description == self.PURCHASE:
                                self.add_cliq_contract(contract, new_contract)
                                founded_purchase = True
                            if new_contract.id_vendor_profile_id == profile.id_profile and\
                                    contract.description == self.SALE:
                                self.add_cliq_contract(contract, new_contract)
                                founded_sale = True

                if new_contract.id_buyer_profile_id is not None:
                    purchase_buyer_reference = new_contract.id_buyer_profile_id
                elif new_contract.id_buyer_assets_id is not None:
                    purchase_buyer_reference = new_contract.id_buyer_assets.id_profile_id
                elif new_contract.id_buyer_asset_items_id is not None:
                    purchase_buyer_reference = new_contract.id_buyer_asset_items.id_assets.id_profile_id

                if (purchase_buyer_reference == profile.id_profile) and not founded_purchase:
                    purchases = []
                    purchases.append(new_contract)
                    contracts = []
                    contracts.append(self.generate_contract_item(purchases, self.PURCHASE))
                    contracts.append(self.generate_contract_item([], self.SALE))
                    profile_item = self.generate_profile_item(profile, contracts)
                    saved_contracts.append(profile_item)

                if (new_contract.id_vendor_profile_id == profile.id_profile) and not founded_sale:
                    sales = []
                    sales.append(new_contract)
                    contracts = []
                    contracts.append(self.generate_contract_item([], self.PURCHASE))
                    contracts.append(self.generate_contract_item(sales, self.SALE))
                    profile_item = self.generate_profile_item(profile, contracts)
                    saved_contracts.append(profile_item)

    def add_cliq_contract(self, contract, new_contract):
        """Adds a new contract to the end of the list of payables"""
        idx = -1
        for i, item in enumerate(contract.items):
            if item.double_status == "I":
                idx = i
                break
        if idx > -1:
            contract.items.insert(idx, deepcopy(new_contract))
        else:
            contract.items.append(deepcopy(new_contract))

    def generate_saved_contracts_list(self, priorized_cliqs, queryset):
        """Generates a list of profiles for ordering from saved cliq contracts"""
        if len(priorized_cliqs) <= 0:
            return []
        profiles = []

        try:
            # The first element
            profile = Profile.objects.get(pk=priorized_cliqs[0].priorized_profile_id)
            profile_item = self.generate_saved_profile_item(profile, priorized_cliqs[0])
            profiles.append(profile_item)
        except Profile.DoesNotExist:
            return []

        for priorized_cliq in priorized_cliqs:
            cliq = queryset.filter(id_contract_cliq=priorized_cliq.cliq_id).annotate(
                new=Value(False, output_field=BooleanField())
            ).first()
            if cliq is None:
                continue
            cliq.double_status = priorized_cliq.double_status
            cliq.priorized_profile_id = priorized_cliq.priorized_profile_id

            if profile.id_profile != priorized_cliq.priorized_profile_id:
                profile = Profile.objects.get(pk=priorized_cliq.priorized_profile_id)
                profile_item = self.generate_saved_profile_item(profile, priorized_cliq)
                profiles.append(profile_item)

            if priorized_cliq.id_buyer_profile == priorized_cliq.priorized_profile_id:
                for contract in profile_item.contracts:
                    if contract.description == self.PURCHASE:
                        contract.items.append(cliq)
            elif priorized_cliq.id_vendor_profile == priorized_cliq.priorized_profile_id:
                for contract in profile_item.contracts:
                    if contract.description == self.SALE:
                        contract.items.append(cliq)
        self.set_double_status_and_profile(profiles)
        return profiles

    def generate_saved_profile_item(self, profile, first_cliq):
        """Generates a profile to add the list of contracts for sorting"""
        profile_item = namedtuple('Profile', ['profile_id', 'profile_name', 'contracts'])
        profile_item.profile_id = profile.id_profile
        profile_item.profile_name = profile.name_profile
        contracts = []
        if profile.id_profile == first_cliq.id_buyer_profile:
            contracts.append(self.generate_contract_item([], self.PURCHASE))
            contracts.append(self.generate_contract_item([], self.SALE))
        elif profile.id_profile == first_cliq.id_vendor_profile:
            contracts.append(self.generate_contract_item([], self.SALE))
            contracts.append(self.generate_contract_item([], self.PURCHASE))

        profile_item.contracts = contracts
        return profile_item

    def generate_new_contracts_list(self, new_contracts):
        """Generates a list of current contracts for ordering"""
        """Generates the return from first balance execution according the sort rules"""
        sap_code_sort = ['1001', '1038', '1064', '1525', '1112']
        contract_type_sort = ['flat', 'flexivel', 'transferencia']

        agents = Agents.objects.filter(id_company__id_sap__in=sap_code_sort, id_company__type='I')
        sorted_agents = sorted(agents, key=lambda x: list(sap_code_sort).index(x.id_company.id_sap))
        other_agents = Agents.objects.exclude(id_company__id_sap__in=sap_code_sort).filter(id_company__type='I')
        sorted_other_agents = sorted(other_agents, key=lambda x: x.id_company.company_name)
        sorted_agents.extend(sorted_other_agents)

        profiles = []
        for agent in sorted_agents:
            profiles.extend(agent.profile_agent.all())

        response_list = []
        for profile in profiles:
            buyer_profile = Q(id_buyer_profile_id=profile.id_profile)
            buyer_asset = Q(id_buyer_assets__id_profile_id=profile.id_profile)
            buyer_asset_items = Q(id_buyer_asset_items__id_assets__id_profile_id=profile.id_profile)
            sale_query = Q(id_vendor_profile_id=profile.id_profile)

            purchase_contracts = new_contracts.filter(buyer_profile | buyer_asset | buyer_asset_items)
            sorted_purchase_contracts = sorted(purchase_contracts,
                                               key=lambda x: list(contract_type_sort).index(x.contract_type))
            sale_contracts = new_contracts.filter(sale_query)
            sorted_sale_contracts = sorted(sale_contracts,
                                           key=lambda x: list(contract_type_sort).index(x.contract_type))

            if len(sorted_purchase_contracts) > 0 or len(sorted_sale_contracts) > 0:
                contracts = []
                contracts.append(self.generate_contract_item(sorted_purchase_contracts, self.PURCHASE))
                contracts.append(self.generate_contract_item(sorted_sale_contracts, self.SALE))
                profile_item = self.generate_profile_item(profile, contracts)
                response_list.append(profile_item)

        self.set_double_status_and_profile(response_list)
        self.deprecate_inactives(response_list)
        return response_list

    def generate_contract_item(self, items, description):
        """Generates a contract item"""
        contract = namedtuple('Contract', ['description', 'items', 'id'])
        contract.description = description
        contract.items = items
        return contract

    def generate_profile_item(self, profile, contracts):
        """Gerate a profile item from return"""
        profile_item = namedtuple('Profile', ['profile_id', 'profile_name'])
        profile_item.profile_id = profile.id_profile
        profile_item.profile_name = profile.name_profile
        profile_item.contracts = contracts
        return profile_item

    def set_double_status_and_profile(self, profile_list):
        """Run each contract and check the double status"""
        id_second_level = 300
        for profile in profile_list:
            for contract in profile.contracts:
                id_second_level += 1
                contract.id = id_second_level
                for cliq in contract.items:
                    if cliq.priorized_profile_id is None:
                        cliq.priorized_profile_id = profile.profile_id
                    if cliq.double_status is None:
                        self.check_double_status(cliq, profile_list)


    def check_double_status(self, cliq_key, profile_list):
        """Set the double status in each contract"""
        double_list = []
        for profile in profile_list:
            for contract in profile.contracts:
                for cliq in contract.items:
                    if cliq.id_contract_cliq == cliq_key.id_contract_cliq:
                        double_list.append(cliq)

        if len(double_list) == 1:
            double_list[0].double_status = 'U'
        elif len(double_list) == 2:
            double_list[0].double_status = 'A'
            double_list[1].double_status = 'I'

    def deprecate_inactives(self, profile_list):
        """Deprecate the inactives contracts"""
        for profile in profile_list:
            for contract in profile.contracts:
                if len(contract.items) > 0:
                    for i in range(len(contract.items)-1, -1, -1):
                        cliq = contract.items[i]
                        if cliq.double_status == 'I':
                            contract.items.append(contract.items.pop(contract.items.index(cliq)))

    def schedule_save_balance(self):
        """This method was implemented for automated balance sheet generation for the previous month."""
        balance_date = get_last_month_date()
        # Changes the status of the consolidated balance sheet of the previous month to saved
        try:
            last_report = Report.objects.filter(report_type__initials__exact='BDE', month=balance_date.month, year=balance_date.year).latest('id')
            if last_report.status == 'C':
                last_report.status = 'S'
                last_report.save()
        except Report.DoesNotExist:
            pass
        
        # Gets the fields of the last generated balance
        balance_data = {}
        response = self.get_last_balance_fields()
        balance_fields = response.data
        balance_fields['month'] = balance_date.month
        balance_fields['year'] = balance_date.year
        saved_status = ['S', 's']
        rcd = Report.objects.filter(month=balance_date.month, year=balance_date.year, status__in=saved_status).latest('id')
        balance_fields['id_rcd'] = rcd.id
        balance_fields['rcd_name'] = rcd.report_name

        cache_balance = CacheBalance.get_instance()
        cache_balance.month = balance_date.month
        cache_balance.year = balance_date.year
        cache_balance.id_rcd = rcd.id
        cache_balance.load_data()

        # Gets list of cliqs contracts
        queryset_cliqs = self.get_cliq_contracts(balance_date.month, balance_date.year)
        priorized_cliq = SortProfileSerializer(queryset_cliqs, many=True).data

        # Generate Balance
        balance_data['balance_fields'] = balance_fields
        balance_data['priorized_cliq'] = priorized_cliq
        balance = self.generate_balance(balance_data)
        self.save_balance(balance, 'System')

    def get_saved_balance(self, id_balance):
        queryset = Report.objects.filter(report_type__initials__exact='BDE')
        if id_balance is None:
            raise PreconditionFailed
        try:
            response_data = queryset.get(id=id_balance)
            priorized_cliq = PriorizedCliq.objects.filter(id_report__id=id_balance)
            response_data.priorized_cliq = self.get_priorized_cliq_saved(priorized_cliq,
                                                                                    int(response_data.month),
                                                                                    int(response_data.year))
            return response_data
        except Report.DoesNotExist:
            raise NotFound
        
    def get_priorized_cliq_saved(self, sorted_saved_cliqs, month, year):
        queryset = self.get_cliq_contract_queryset(month, year)
        sorted_profiles = self.generate_saved_contracts_list(sorted_saved_cliqs, queryset)
        sorted_profiles = self.check_saved_consistency(sorted_profiles, queryset)
        return sorted_profiles

    def clear_temporary_balance(self):
        """Clears temporary Balances."""
        try:
            report_type_list = ['BDE']
            time_delta = 1
            datetime_now = datetime.now(get_local_timezone())
            temporary_reports = Report.objects.filter(
                report_type__initials__in=report_type_list,
                status='T',
                creation_date__lte=(datetime_now - timedelta(hours=time_delta))
            )
            count = len(temporary_reports)

            if count > 0:
                try:
                    temporary_reports.delete()
                    detail = f'[{count}] report balance(s) were removed.'
                    self.logger.info(detail)
                except Exception as e:
                    detail = f'ERROR: clear_temporary_balance failed: {str(e)}'
                    self.logger.error(detail)
                    return
        except Exception as e:
            detail = f'ERROR: clear_temporary_balance failed: {str(e)}'
            self.logger.error(detail)

