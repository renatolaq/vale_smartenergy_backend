from threading import Thread
from .models import BalanceFields, ReportType, Balance, BalanceType, \
    DetailedBalanceType, MarketSettlement, HistoryBalance
from agents.models import Agents
from profiles.models import Profile
from core.models import Seasonality, CceeDescription
from company.models import Company, EletricUtilityCompany
from assets.models import Assets, Submarket, SeasonalityProinfa
from asset_items.models import AssetItems, SeasonalityAssetItem
from balance_report_market_settlement.models import MeteringReportData, MeteringReportValue
from .utils import get_all


class CacheBalance:
    __instance = None

    month = None
    year = None
    id_rcd = None
    
    detailed_balance_types = []
    balance_types = []
    report_types = []
    submarkets = []
    companies = []
    assets = []
    asset_items = []
    profiles = []
    eletric_utility_companies = []
    seasonalities = []
    seasonality_asset_items = []
    ccee_description = []
    seasonality_proinfa = []

    queryset_assets = None
    queryset_asset_items = None
    queryset_agent = None
    queryset_metering_report_data = None
    queryset_profile = None
    queryset_balance_fields = None
    queryset_balance = None
    queryset_priorized_cliq = None
    queryset_history_balance = None


    @staticmethod
    def get_instance():
        """ Static access method. """
        if CacheBalance.__instance == None:
            CacheBalance()
        return CacheBalance.__instance

    def __init__(self):
        """ Virtually private constructor. """
        if CacheBalance.__instance != None:
            raise Exception("This class is a singleton!")
        else:
            CacheBalance.__instance = self

    def load_data(self):
        """ Load data for generate balance. """
        if CacheBalance.__instance == None:
            raise Exception("The class was not instantiated!")

        thread = CacheThread(1)
        thread.start()


class CacheThread(Thread):
    """ Opens a new thread so as not to delay the response to the user. """
    def __init__(self, num):
        Thread.__init__(self)
        self.num = num

    def run(self):
        cache = CacheBalance.get_instance()

        cache.queryset_assets = Assets.objects.filter(status__in=['S', 's']).all()
        cache.queryset_asset_items = AssetItems.objects.filter(status__in=['S', 's']).all()
        cache.queryset_agent = Agents.objects.exclude(status__in=['0', 'n', 'N']).all()
        cache.queryset_metering_report_data = MeteringReportData.objects.all()
        cache.queryset_market_settlement = MarketSettlement.objects.all()
        cache.queryset_profile = Profile.objects.all()
        cache.queryset_balance_fields = BalanceFields.objects.all()
        cache.queryset_balance = Balance.objects.all()
        cache.queryset_history_balance = HistoryBalance.objects.all()
        # cached
        cache.balance_types = get_all(BalanceType.objects)
        cache.detailed_balance_types = get_all(DetailedBalanceType.objects)
        cache.report_types = get_all(ReportType.objects)
        cache.submarkets = get_all(Submarket.objects.filter(status__in=['S', 's']))
        cache.profiles = get_all(Profile.objects.filter(status__in=['S', 's']))
        cache.assets = get_all(Assets.objects.exclude(status__in=['0', 'n', 'N']))
        cache.asset_items = get_all(AssetItems.objects.exclude(status__in=['0', 'n', 'N']))
        cache.companies = get_all(Company.objects.filter(status__in=['S', 's']))
        cache.eletric_utility_companies = get_all(EletricUtilityCompany.objects)
        cache.seasonalities = get_all(Seasonality.objects)
        cache.seasonality_asset_items = get_all(SeasonalityAssetItem.objects)
        cache.ccee_description = get_all(CceeDescription.objects.filter(status__in=['S', 's']))
        cache.seasonality_proinfa = get_all(SeasonalityProinfa.objects)
