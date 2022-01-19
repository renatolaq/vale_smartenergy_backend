from django.db import models
from datetime import datetime
from assets.models import Assets, Submarket
from consumption_metering_reports.models import MeteringReportData, MeteringReportValue
from profiles.models import Profile
from energy_contract.models import EnergyContract
from asset_items.models import AssetItems
from core.models import Seasonality, CceeDescription
from balance_report_market_settlement.exceptions import InvalidContract
from django.contrib.contenttypes.fields import GenericRelation
from django.db.models import Sum
from itertools import chain


class ReportType(models.Model):
    id = models.AutoField(db_column='ID_REPORT_TYPE', primary_key=True)  # Field name made lowercase.
    name = models.CharField(db_column='REPORT_NAME', max_length=50)  # Field name made lowercase.
    initials = models.CharField(db_column='REPORT_INITIALS', max_length=3)  # Field name made lowercase.
    class Meta:
        managed = False
        db_table = 'REPORT_TYPE'

        
class Report(models.Model):
    id = models.AutoField(db_column='ID_REPORT', primary_key=True)
    report_type = models.ForeignKey('ReportType', related_name='report_type', on_delete=models.DO_NOTHING, db_column='ID_REPORT_TYPE', null=True)
    id_reference = models.ForeignKey('self', related_name='related_report', on_delete=models.DO_NOTHING, db_column='ID_REFERENCE', null=True)
    creation_date = models.DateTimeField(db_column='CREATION_DATE', null=False, default=datetime.now)
    report_name = models.CharField(max_length=50, unique=True, null=False, blank=False)
    status = models.CharField(db_column='STATUS', max_length=1, null=False, blank=False, default=None)
    month = models.CharField(db_column='MONTH', max_length=2, null=False, blank=False, default=None)
    year = models.CharField(db_column='YEAR', max_length=4, null=False, blank=False, default=None)
    limit_value = models.DecimalField(db_column='LIMIT_VALUE', max_digits=18, decimal_places=9, null=True)

    @property
    def get_balance_fields(self):
        return BalanceFields.objects.filter(id_report__id=self.id).first()

    @property
    def get_priorized_cliq(self):
        return PriorizedCliq.objects.filter(id_report__id=self.id)

    @property
    def get_balance(self):
        return Balance.objects.filter(id_report__id=self.id, id_balance_type__description__exact='AGENT', internal_company=True)

    def __str__(self):
        return '%s %s %s %s %s %s %s %s %s' % (self.id, self.report_type, self.id_reference, self.creation_date,
                self.report_name, self.status, self.month, self.year, self.limit_value)

    class Meta:
        managed = False
        db_table = 'REPORT_TABLE'

        
class BalanceFields(models.Model):
    id = models.AutoField(db_column='ID_BALANCE_FIELDS', primary_key=True)  # Field name made lowercase.
    month = models.DecimalField(db_column='MONTH', max_digits=2, decimal_places=0)  # Field name made lowercase.
    year = models.DecimalField(db_column='YEAR', max_digits=4, decimal_places=0)  # Field name made lowercase.
    id_report_rcd = models.ForeignKey(Report, models.DO_NOTHING, db_column='ID_REPORT_RCD', related_name='report_balance_rcd')  # Field name made lowercase.
    gsf = models.DecimalField(db_column='GSF', max_digits=18, decimal_places=6)  # Field name made lowercase.
    pld_n = models.DecimalField(db_column='PLD_N', max_digits=18, decimal_places=4)  # Field name made lowercase.
    pld_ne = models.DecimalField(db_column='PLD_NE', max_digits=18, decimal_places=4)  # Field name made lowercase.
    pld_seco = models.DecimalField(db_column='PLD_SECO', max_digits=18, decimal_places=4)  # Field name made lowercase.
    pld_s = models.DecimalField(db_column='PLD_S', max_digits=18, decimal_places=4)  # Field name made lowercase.
    id_report = models.ForeignKey(Report, models.CASCADE, db_column='ID_REPORT', related_name='report_balance')  # Field name made lowercase.

    def __str__(self):
        return '%s %s %s %s %s %s %s %s %s %s' % (self.id, self.month, self.year, self.id_report_rcd,
                self.gsf, self.pld_n, self.pld_ne, self.pld_seco, self.pld_s, self.id_report)

    class Meta:
        managed = False
        db_table = 'BALANCE_FIELDS'


class Address(models.Model):

    id_address = models.AutoField(db_column='ID_ADDRESS', primary_key=True)  # Field name made lowercase.
    id_city = models.ForeignKey('City', models.DO_NOTHING, db_column='ID_CITY', blank=True, null=True, related_name='city')  # Field name made lowercase.
    street = models.CharField(db_column='STREET', max_length=100, blank=True, null=True)  # Field name made lowercase.
    neighborhood = models.CharField(db_column='NEIGHBORHOOD', max_length=100, blank=True,
                                    null=True)  # Field name made lowercase.
    number = models.DecimalField(db_column='NUMBER', max_digits=9, decimal_places=0, blank=True,
                                 null=True)  # Field name made lowercase.

    zip_code = models.CharField(db_column='ZIP_CODE', max_length=40, blank=True,
                                null=True)  # Field name made lowercase.
    complement = models.CharField(db_column='COMPLEMENT', max_length=30, blank=True,
                                  null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'ADDRESS'


class City(models.Model):
    id_city = models.AutoField(db_column='ID_CITY', primary_key=True)  # Field name made lowercase.
    id_state = models.ForeignKey('State', models.DO_NOTHING, db_column='ID_STATE', blank=True,
                                 null=True)  # Field name made lowercase.
    city_name = models.CharField(db_column='CITY_NAME', max_length=40, blank=True,
                                 null=True)  # Field name made lowercase.
    initials = models.CharField(db_column='INITIALS', max_length=40, blank=True,
                                null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'CITY'



class Country(models.Model):
    id_country = models.AutoField(db_column='ID_COUNTRY', primary_key=True)  # Field name made lowercase.
    name = models.CharField(db_column='NAME', max_length=30)  # Field name made lowercase.
    initials = models.CharField(db_column='INITIALS', max_length=4, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'COUNTRY'



class State(models.Model):
    id_state = models.AutoField(db_column='ID_STATE', primary_key=True)  # Field name made lowercase.
    id_country = models.ForeignKey(Country, models.DO_NOTHING, db_column='ID_COUNTRY', blank=True,
                                   null=True)  # Field name made lowercase.
    name = models.CharField(db_column='NAME', max_length=100, blank=True, null=True)  # Field name made lowercase.
    initials = models.CharField(db_column='INITIALS', max_length=4, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'STATE'


class Company(models.Model):
    id_company = models.AutoField(db_column='ID_COMPANY', primary_key=True)  # Field name made lowercase.
    id_address = models.ForeignKey(Address, models.DO_NOTHING, db_column='ID_ADDRESS', blank=True, null=True, related_name="address_company")  # Field name made lowercase.
    company_name = models.CharField(db_column='COMPANY_NAME', max_length=250)  # Field name made lowercase.
    legal_name = models.CharField(db_column='LEGAL_NAME', max_length=250)  # Field name made lowercase.
    registered_number = models.CharField(db_column='REGISTERED_NUMBER', max_length=12, blank=True, null=True)  # Field name made lowercase.
    type = models.CharField(db_column='TYPE', max_length=5)  # Field name made lowercase.
    state_number = models.CharField(db_column='STATE_NUMBER', max_length=18)  # Field name made lowercase.
    nationality = models.CharField(db_column='NATIONALITY', max_length=3)  # Field name made lowercase.
    id_sap = models.CharField(db_column='ID_SAP', unique=True, max_length=18)  # Field name made lowercase.
    characteristics = models.CharField(db_column='CHARACTERISTICS', max_length=30, blank=True, null=True)  # Field name made lowercase.
    status = models.CharField(db_column='STATUS', max_length=1)  # Field name made lowercase.
    create_date = models.DateTimeField(db_column='CREATE_DATE', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'COMPANY'


class CceeDescription(models.Model):
    id_ccee = models.AutoField(db_column='ID_CCEE', primary_key=True)  # Field name made lowercase.
    code_ccee = models.CharField(db_column='CODE_CCEE', max_length=40, blank=True)  # Field name made lowercase.
    type = models.CharField(db_column='TYPE', max_length=40)  # Field name made lowercase.
    name_ccee = models.CharField(db_column='NAME_CCEE', max_length=30, blank=True,
                                 null=True)  # Field name made lowercase.
    status = models.CharField(db_column='STATUS', max_length=1)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'CCEE_DESCRIPTION'


class Agents(models.Model):
    id_agents = models.AutoField(db_column='ID_AGENTS', primary_key=True)  # Field name made lowercase.
    id_company = models.ForeignKey(Company, models.DO_NOTHING, db_column='ID_COMPANY', related_name='agents_company')  # Field name made lowercase.
    id_ccee = models.OneToOneField(CceeDescription, models.DO_NOTHING,
                                   db_column='ID_CCEE', related_name='ccee_agent')  # Field name made lowercase.
    vale_name_agent = models.CharField(db_column='VALE_NAME_AGENT', max_length=40)  # Field name made lowercase.
    status = models.CharField(db_column='STATUS', max_length=1)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'AGENTS'


class Profile(models.Model):
    id_profile = models.AutoField(db_column='ID_PROFILE', primary_key=True)  # Field name made lowercase.
    id_agents = models.ForeignKey(Agents, models.DO_NOTHING, db_column='ID_AGENTS', blank=True,
                                  null=True, related_name='profile_agent')  # Field name made lowercase.
    id_ccee = models.OneToOneField(CceeDescription, models.DO_NOTHING, db_column='ID_CCEE',
                                   unique=True, related_name='profile_ccee')  # Field name made lowercase.
    name_profile = models.CharField(db_column='NAME_PROFILE', max_length=40)  # Field name made lowercase.
    alpha = models.CharField(db_column='ALPHA', max_length=1)  # Field name made lowercase.
    encouraged_energy = models.BooleanField(db_column='ENCOURAGED_ENERGY')  # Field name made lowercase.
    status = models.CharField(db_column='STATUS', max_length=1)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'PROFILE'


class PriorizedCliq(models.Model):
    id = models.AutoField(db_column='ID_PRIORIZED_CLIQ', primary_key=True)  # Field name made lowercase.
    contract_name = models.CharField(db_column='CONTRACT_NAME', max_length=102)  # Field name made lowercase.
    contract_modality = models.CharField(db_column='CONTRACT_TYPE', max_length=13)  # Field name made lowercase.
    contract_cliq = models.CharField(db_column='CONTRACT_CLIQ', max_length=40, blank=True)  # Field name made lowercase.
    buyer_profile = models.CharField(db_column='BUYER_PROFILE', max_length=80)  # Field name made lowercase.
    id_buyer_profile = models.DecimalField(db_column='ID_BUYER_PROFILE', max_digits=9, decimal_places=0)  # Field name made lowercase.
    id_buyer_assets = models.DecimalField(db_column='ID_BUYER_ASSET', max_digits=9, decimal_places=0)  # Field name made lowercase.
    id_buyer_asset_items = models.DecimalField(db_column='BUYER_ASSET_ITEMS', max_digits=9, decimal_places=0)  # Field name made lowercase.
    vendor_profile = models.CharField(db_column='VENDOR_PROFILE', max_length=80)  # Field name made lowercase.
    id_vendor_profile = models.DecimalField(db_column='ID_VENDOR_PROFILE', max_digits=9, decimal_places=0)  # Field name made lowercase.
    id_submarket = models.DecimalField(db_column='ID_SUBMARKET', max_digits=9, decimal_places=0)  # Field name made lowercase.
    cliq_type = models.CharField(db_column='CLIQ_TYPE', max_length=15)  # Field name made lowercase.
    fare = models.DecimalField(db_column='FARE', max_digits=18, decimal_places=6)  # Field name made lowercase.
    volume = models.DecimalField(db_column='VOLUME', max_digits=18, decimal_places=3)  # Field name made lowercase.
    transaction_type = models.CharField(db_column='TRANSACTION_TYPE', max_length=30)  # Field name made lowercase.
    flexibility = models.CharField(db_column='FLEXIBILITY', max_length=20, blank=True, null=True)  # Field name made lowercase.
    proinfa_flexibility = models.CharField(db_column='PROINFA_FLEXIBILITY', max_length=1, blank=True, null=True, default='N')  # Field name made lowercase.
    seasonality = models.DecimalField(db_column='SEASONALITY', max_digits=18, decimal_places=9, blank=True, null=True, default=1)  # Field name made lowercase.
    id_report = models.ForeignKey(Report, models.CASCADE, db_column='ID_REPORT', related_name='cliq_report')  # Field name made lowercase.
    cliq_id = models.DecimalField(db_column='CLIQ_ID', max_digits=9, decimal_places=0)
    priorized_profile_id = models.DecimalField(db_column='PRIORIZED_PROFILE_ID', max_digits=9, decimal_places=0)
    double_status = models.CharField(db_column='DOUBLE_STATUS', max_length=1, null=False, blank=False, default=None)

    def __str__(self):
        return '%s %s %s %s %s %s %s %s' % (self.id, self.contract_name, self.contract_modality, self.contract_cliq,
                self.buyer_profile, self.vendor_profile, self.cliq_type, self.id_report)
    
    @property
    def buyer_is_a_profile(self):
        return ((self.id_buyer_assets is None) and (self.id_buyer_asset_items is None)) and bool(self.buyer_profile)

    @property
    def transaction_type_is_fixed_volume(self):
        return (self.transaction_type is not None) and (self.transaction_type.upper() == 'VOLUME_FIXO')

    @property
    def flexibility_type_is_conventional(self):
        return (self.flexibility is not None) and (self.flexibility.upper() == 'CONVENCIONAL')

    @property
    def flexibility_is_peak_or_off_peak(self):
        return (self.flexibility is not None) and (self.flexibility.upper() in ['PONTA', 'FORA PONTA', 'PONTA E FORA PONTA'])

    def clean(self):
        if self.cliq_type.lower() == 'flat':
            # Checking if a flat cliq contract has an invalid transaction type
            if not self.transaction_type_is_fixed_volume:
                raise InvalidContract({
                "translation_key": "error_flat_transaction_type",
                "contract_name": self.contract_name
            })
        if self.cliq_type.lower() == 'flexivel':
            # Checking if a flexible cliq that which buyer is a profile has an invalid flexibility type
            if self.buyer_is_a_profile and not self.flexibility_type_is_conventional:
                raise InvalidContract({
                    "translation_key": "error_buyer_profile_flexibilization_type",
                    "contract_name": self.contract_name
                })
            if (not self.buyer_is_a_profile and not self.transaction_type_is_fixed_volume) and \
                (not (self.id_buyer_asset_items and self.flexibility.upper() == 'PONTA E FORA PONTA')):
                raise InvalidContract({
                    "translation_key": "error_buyer_consumer_transaction_type",
                    "contract_name": self.contract_name
                })
        if self.cliq_type.lower() == 'transferencia':
            if self.flexibility_is_peak_or_off_peak:
                raise InvalidContract({
                    "translation_key": "error_transfer_contract_flexibility",
                    "contract_name": self.contract_name
                })

    class Meta:
        managed = False
        db_table = 'PRIORIZED_CLIQ'


class BalanceType(models.Model):
    id = models.AutoField(db_column='ID_BALANCE_TYPE', primary_key=True)  # Field name made lowercase.
    description = models.CharField(db_column='DESCRIPTION', max_length=100, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'BALANCE_TYPE'


class Balance(models.Model):
    id = models.AutoField(db_column='ID_BALANCE', primary_key=True)  # Field name made lowercase.
    name = models.CharField(db_column='NAME', max_length=40)  # Field name made lowercase.
    value = models.DecimalField(db_column='VALUE', max_digits=18, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    id_balance_type = models.ForeignKey(BalanceType, models.DO_NOTHING, db_column='ID_BALANCE_TYPE')  # Field name made lowercase.
    id_agente = models.ForeignKey('self', models.CASCADE, db_column='ID_AGENTE', blank=True, null=True, related_name='agent_balance')  # Field name made lowercase.
    id_report = models.ForeignKey(Report, models.CASCADE, db_column='ID_REPORT')  # Field name made lowercase.
    internal_company = models.BooleanField(db_column='INTERNAL_COMPANY', null=True)  # Field name made lowercase.

    @property
    def get_macro(self):
        return MacroBalance.objects.filter(id_balance__id=self.id).first()

    @property
    def get_profile(self):
        return Balance.objects.filter(id_agente__id=self.id, id_balance_type__description__exact='PROFILE')

    @property
    def get_purchase_detail(self):
        purchase_queryset = DetailedBalance.objects.filter(id_balance__id=self.id, id_detailed_balance_type__description__exact='PURCHASE')
        proinfa_queryset = DetailedBalance.objects.filter(id_balance__id=self.id, id_detailed_balance_type__description__exact='PROINFA')
        proinfa_list = []
        submarket_list = list(set(proinfa_queryset.values_list('id_submarket', 'id_submarket__description')))
        
        for id_submarket, submarket in submarket_list:
            proinfa_submarket = proinfa_queryset.filter(id_submarket__description=submarket)
            volume = proinfa_submarket.aggregate(total_volume=Sum('volume'))['total_volume']
            proinfa_list.append(DetailedBalance(volume=volume, id_submarket=proinfa_submarket.first().id_submarket, contract_name='PROINFA'))

        result_list = list(chain(proinfa_list, purchase_queryset.order_by('id')))
        return result_list
        

    @property
    def get_sale_detail(self):
        return DetailedBalance.objects.filter(id_balance__id=self.id, id_detailed_balance_type__description__exact='SALE').order_by('id')

    @property
    def get_consumption_detail(self):
        return DetailedBalance.objects.filter(id_balance__id=self.id, id_detailed_balance_type__description__exact='CONSUMPTION')

    @property
    def get_generation_detail(self):
        return DetailedBalance.objects.filter(id_balance__id=self.id, id_detailed_balance_type__description__exact='GENERATION')

    @property
    def get_market_settlement(self):
        return MarketSettlement.objects.filter(id_balance__id=self.id)

    class Meta:
        managed = False
        db_table = 'BALANCE'


class MacroBalance(models.Model):
    id = models.AutoField(db_column='ID_MACRO_BALANCE', primary_key=True)  # Field name made lowercase.
    purchase = models.DecimalField(db_column='PURCHASE', max_digits=18, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    sale = models.DecimalField(db_column='SALE', max_digits=18, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    consumption = models.DecimalField(db_column='CONSUMPTION', max_digits=18, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    generation = models.DecimalField(db_column='GENERATION', max_digits=18, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    proinfa = models.DecimalField(db_column='PROINFA', max_digits=18, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    id_balance = models.ForeignKey(Balance, models.CASCADE, db_column='ID_BALANCE', related_name='macro_balance')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'MACRO_BALANCE'


class DetailedBalanceType(models.Model):
    id = models.AutoField(db_column='ID_DETAILED_BALANCE_TYPE', primary_key=True)  # Field name made lowercase.
    description = models.CharField(db_column='DESCRIPTION', max_length=100, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'DETAILED_BALANCE_TYPE'


class DetailedBalance(models.Model):
    id = models.AutoField(db_column='ID_DETAILED_BALANCE', primary_key=True)  # Field name made lowercase.
    id_contract_cliq = models.DecimalField(db_column='ID_PRIORIZED_CLIQ', max_digits=9, decimal_places=0)  # Field name made lowercase.
    contract_name = models.CharField(db_column='CONTRACT_NAME', max_length=102, blank=True, null=True)  # Field name made lowercase.
    contract_id = models.CharField(db_column='CONTRACT_ID', max_length=40, blank=True)
    id_submarket = models.ForeignKey(Submarket, models.DO_NOTHING, db_column='ID_SUBMARKET')  # Field name made lowercase.
    volume = models.DecimalField(db_column='VOLUME', max_digits=18, decimal_places=3, blank=True, null=True)  # Field name made lowercase.
    fare = models.DecimalField(db_column='FARE', max_digits=18, decimal_places=6, blank=True, null=True)  # Field name made lowercase.
    amount = models.DecimalField(db_column='AMOUNT', max_digits=18, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    unity = models.CharField(db_column='UNITY', max_length=40, blank=True, null=True)  # Field name made lowercase.
    loss = models.DecimalField(db_column='LOSS', max_digits=18, decimal_places=2, blank=True, null=True)  # Field name made lowercase.
    gsf = models.DecimalField(db_column='GSF', max_digits=18, decimal_places=6, blank=True, null=True)  # Field name made lowercase.
    id_balance = models.ForeignKey(Balance, models.CASCADE, db_column='ID_BALANCE', blank=True, null=True, related_name='detailed_balance')  # Field name made lowercase.
    id_detailed_balance_type = models.ForeignKey(DetailedBalanceType, models.DO_NOTHING, db_column='ID_DETAILED_BALANCE_TYPE')  # Field name made lowercase.


    class Meta:
        managed = False
        db_table = 'DETAILED_BALANCE'


class MarketSettlement(models.Model):
    id = models.AutoField(db_column='ID_MARKET_SETTLEMENT', primary_key=True)  # Field name made lowercase.
    profile_name = models.CharField(db_column='PROFILE_NAME', max_length=40, blank=True, null=True)  # Field name made lowercase.
    amount_seco = models.DecimalField(db_column='AMOUNT_SECO', max_digits=18, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    amount_s = models.DecimalField(db_column='AMOUNT_S', max_digits=18, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    amount_ne = models.DecimalField(db_column='AMOUNT_NE', max_digits=18, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    amount_n = models.DecimalField(db_column='AMOUNT_N', max_digits=18, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    saleoff = models.DecimalField(db_column='SALEOFF', max_digits=18, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    id_balance = models.ForeignKey(Balance, models.CASCADE, db_column='ID_BALANCE')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'MARKET_SETTLEMENT'


class HistoryBalance(models.Model):
    id = models.AutoField(db_column='ID_HISTORY_BALANCE', primary_key=True)  # Field name made lowercase.
    id_report = models.ForeignKey(Report, models.CASCADE, db_column='ID_REPORT')  # Field name made lowercase.
    month = models.BooleanField(db_column='MONTH')  # Field name made lowercase.
    year = models.BooleanField(db_column='YEAR')  # Field name made lowercase.
    id_rcd = models.BooleanField(db_column='ID_RCD')  # Field name made lowercase.
    status = models.BooleanField(db_column='STATUS')  # Field name made lowercase.
    gsf = models.BooleanField(db_column='GSF')  # Field name made lowercase.
    pld_n = models.BooleanField(db_column='PLD_N')  # Field name made lowercase.
    pld_ne = models.BooleanField(db_column='PLD_NE')  # Field name made lowercase.
    pld_seco = models.BooleanField(db_column='PLD_SECO')  # Field name made lowercase.
    pld_s = models.BooleanField(db_column='PLD_S')  # Field name made lowercase.
    priorized_cliq = models.BooleanField(db_column='PRIORIZED_CLIQ')  # Field name made lowercase.
    username = models.CharField(db_column='USERNAME', max_length=170, null=True)  # Field name made lowercase.
    justification = models.CharField(db_column='JUSTIFICATION', max_length=300)  # Field name made lowercase.
    create_date = models.DateTimeField(db_column='CREATE_DATE')  # Field name made lowercase.
    

    class Meta:
        managed = False
        db_table = 'HISTORY_BALANCE'


class CliqContract(models.Model):
    id_contract_cliq = models.AutoField(db_column='ID_CONTRACT_CLIQ', primary_key=True)  # Field name made lowercase.
    id_vendor_profile = models.ForeignKey(Profile, models.DO_NOTHING,
                                          db_column='ID_VENDOR_PROFILE', related_name='cliqs_vendor')  # Field name made lowercase.
    id_buyer_profile = models.ForeignKey(Profile, models.DO_NOTHING,
                                         db_column='ID_BUYER_PROFILE', blank=True, null=True)  # Field name made lowercase.
    id_contract = models.ForeignKey(EnergyContract, models.DO_NOTHING, db_column='ID_CONTRACT')  # Field name made lowercase.
    id_ccee = models.ForeignKey(CceeDescription, models.DO_NOTHING, db_column='ID_CCEE',
                                    blank=True, null=True)  # Field name made lowercase.
    id_buyer_assets = models.ForeignKey(Assets, models.DO_NOTHING, db_column='BUYER_ASSET_ID', blank=True,
                                    null=True)  # Field name made lowercase.
    id_buyer_asset_items = models.ForeignKey(AssetItems, models.DO_NOTHING, db_column='BUYER_ASSET_ITEMS', blank=True,
                                          null=True)  # Field name made lowercase.
    id_submarket = models.ForeignKey(Submarket, models.DO_NOTHING, db_column='ID_SUBMARKET', blank=True,
                                     null=True)  # Field name made lowercase.
    ccee_type_contract = models.CharField(db_column='CCEE_TYPE_CONTRACT', max_length=5, blank=True,
                                          null=True)  # Field name made lowercase.
    transaction_type = models.CharField(db_column='TRANSACTION_TYPE', max_length=30)  # Field name made lowercase.
    flexibility = models.CharField(db_column='FLEXIBILITY', max_length=12, blank=True,
                                   null=True)  # Field name made lowercase.
    mwm_volume = models.DecimalField(db_column='MWM_VOLUME', max_digits=18,
                                     decimal_places=9)  # Field name made lowercase.
    contractual_loss = models.DecimalField(db_column='CONTRACTUAL_LOSS', max_digits=18,
                                           decimal_places=9, blank=True, null=True)  # Field name made lowercase.
    status = models.CharField(db_column='STATUS', max_length=1, blank=True, null=True)  # Field name made lowercase.
    submarket = models.BooleanField(db_column='SUBMARKET', null=True)  # Field name made lowercase.
    mwm_volume_peak = models.DecimalField(db_column='MWM_VOLUME_PEAK', max_digits=18, decimal_places=9, blank=True, null=True)  # Field name made lowercase.
    mwm_volume_offpeak = models.DecimalField(db_column='MWM_VOLUME_OFFPEAK', max_digits=18, decimal_places=9, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'CLIQ_CONTRACT'


class SeasonalityCliq(models.Model):
    id_seasonality_cliq = models.AutoField(db_column='ID_SEASONALITY_CLIQ', primary_key=True)  # Field name made lowercase.
    id_seasonality = models.ForeignKey(Seasonality, models.DO_NOTHING, db_column='ID_SEASONALITY', blank=True,
                                          null=True)  # Field name made lowercase.
    id_contract_cliq = models.ForeignKey(CliqContract, models.DO_NOTHING, db_column='ID_CONTRACT_CLIQ', blank=True,
                                         null=True, related_name='seasonality_cliq')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'SEASONALITY_CLIQ'
        unique_together = ('id_seasonality_cliq', 'id_seasonality', 'id_contract_cliq')

class TransferContractPriority(models.Model):
    id_transfer = models.AutoField(db_column='ID_TRANSFER', primary_key=True)  # Field name made lowercase.
    id_contract_cliq = models.ForeignKey(CliqContract, models.DO_NOTHING, db_column='ID_CONTRACT_CLIQ', blank=True,
                                         null=True, related_name='cliqs_priority')  # Field name made lowercase.
    priority_number = models.DecimalField(db_column='PRIORITY_NUMBER', max_digits=4, decimal_places=0, blank=True,
                                          null=True)  # Field name made lowercase.
    status = models.CharField(db_column='STATUS', max_length=1, blank=True, null=True)  # Field name made lowercase.
    
    class Meta:
        managed = False
        db_table = 'TRANSFER_CONTRACT_PRIORITY'