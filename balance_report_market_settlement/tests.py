from django.test import TestCase
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_412_PRECONDITION_FAILED, \
    HTTP_500_INTERNAL_SERVER_ERROR, HTTP_201_CREATED
from datetime import datetime, timedelta
from decimal import Decimal
from collections import namedtuple
from .service import BalanceService
from .cache_balance import CacheBalance
from rest_framework.response import Response
from .serializers import ReportsSerializer, SortProfileSerializer
from .models import Report, CliqContract, PriorizedCliq, ReportType, Profile, BalanceType, Balance, MarketSettlement, \
    DetailedBalance, DetailedBalanceType
from .exceptions import *
from .utils import get_local_timezone, is_nth_brazilian_workday, get_user_username, check_for_balances, \
    calculate_flexible_proportional_cliq_volume, get_one_by_id, get_many_by_property_value, get_last_month_date
from assets.models import Submarket, Assets
from asset_items.models import AssetItems
from django.utils.timezone import make_aware
from django.test import tag

MockedMarketSettlement = namedtuple('MockedMarketSettlement', ['profile_name'])


class BalaceTest(TestCase):
    @staticmethod
    def setUpReport(report_type, report_name, reference_report=None):
        mock_date = make_aware(datetime.now())
        report_type_id = ReportType.objects.get(initials=report_type).id
        reference_report_id = reference_report.id if reference_report else None
        report = Report(None, report_type_id, reference_report_id, mock_date, report_name, 'S', mock_date.month, mock_date.year, None)
        report.save()
        return report

    @staticmethod
    def setUpPriorizedCliq(**kwargs):
        priorized_cliq = PriorizedCliq(**kwargs)
        priorized_cliq.clean()
        priorized_cliq.save()
        return priorized_cliq
    
    @staticmethod
    def setUpProfileBalance(profile, balance_report):
        agent_balance_type = BalanceType.objects.get(description='AGENT')
        agent = profile.id_agents
        agent_balance = Balance(id=None, name=agent.vale_name_agent, value=Decimal('0.0'), 
                                id_balance_type=agent_balance_type, id_agente=None, id_report=balance_report, 
                                internal_company=None)
        agent_balance.save()
        profile_balance_type = BalanceType.objects.get(description='PROFILE')
        profile_balance = Balance(id=None, name=profile.name_profile, value=Decimal('0.0'), 
                                id_balance_type=profile_balance_type, id_agente=agent_balance, id_report=balance_report, 
                                internal_company=None)
        profile_balance.save()
        return profile_balance

    @staticmethod
    def setUpMarketSettlement(name, profile_balance):
        market_settlement = MarketSettlement(profile_name=name, amount_seco=Decimal('0.0'), amount_s=Decimal('0.0'),
                                            amount_ne=Decimal('0.0'), amount_n=Decimal('0.0'), saleoff=Decimal('0.0'),
                                            id_balance=profile_balance)
        market_settlement.save()
        return market_settlement

    @staticmethod
    def setUpDetailedBalance(profile_balance, submarket, identifier_name, volume, detailed_balance_type):
        detailed_type = DetailedBalanceType.objects.get(description=detailed_balance_type)
        detailed_balance = DetailedBalance(contract_name=identifier_name, id_submarket=submarket, volume=volume,
                                        id_balance=profile_balance, id_detailed_balance_type=detailed_type)
        detailed_balance.save()
        return detailed_balance

    def setUpBalanceService(self, priorized_cliq=None):
        """Returns an instance of BalanceService() with a mocked cache and mocked executed_cliqs for the buyer and vendor
        profiles of the given priorized_cliq"""
        if priorized_cliq:
            balance_service = self.mock_executed_cliqs(BalanceService(), 
                                                    [priorized_cliq.buyer_profile, priorized_cliq.vendor_profile])
        else:
            balance_service = BalanceService()
        cache_balance = CacheBalance.get_instance()
        cache_balance.load_data()
        balance_service.cache = cache_balance
        balance_service.cache.submarkets = Submarket.objects.all()
        return balance_service

    def setUp(self):
        RCD_report = self.setUpReport('RPD', 'mock_detailed_report', None)
        BDE_report = self.setUpReport('BDE', 'mock_balance_report', RCD_report)
        buyer_profile = Profile.objects.first()
        vendor_profile = Profile.objects.last()
        generic_cliq = CliqContract.objects.first()
        generic_submarket = Submarket.objects.first()
        buyer_profile_balance = self.setUpProfileBalance(vendor_profile, BDE_report)
        self.setUpDetailedBalance(buyer_profile_balance, generic_submarket, 'test_consumption', Decimal('3.0'), 'CONSUMPTION')
        buyer_ms = self.setUpMarketSettlement('test_market_settlement_0', buyer_profile_balance)
        flat_cliq = self.setUpPriorizedCliq(**{
            'buyer_profile': 'ECOM',
            'cliq_id': generic_cliq.pk,
            'cliq_type': 'flat',
            'contract_cliq': '',
            'contract_modality': 'Curto Prazo',
            'contract_name': 'CVI_1,7_VALE_ECOM_0520__test_flat_cliq',
            'double_status': 'U',
            'fare': Decimal('99.240000'),
            'flexibility': None,
            'id': None,
            'id_buyer_asset_items': None,
            'id_buyer_assets': None,
            'id_buyer_profile': buyer_profile.pk,
            'id_report': BDE_report,
            'id_submarket': generic_submarket.pk,
            'id_vendor_profile': vendor_profile.pk,
            'priorized_profile_id': Decimal('46'),
            'proinfa_flexibility': 'N',
            'seasonality': None,
            'transaction_type': 'VOLUME_FIXO',
            'vendor_profile': 'CVRD APE I5',
            'volume': Decimal('1264.800')
        })
        zero_buyer_cliq = self.setUpPriorizedCliq(**{
            'buyer_profile': 'CVRD TIG',
            'cliq_id': generic_cliq.pk,
            'cliq_type': 'transferencia',
            'contract_cliq': '1167485',
            'contract_modality': 'Transferencia',
            'contract_name': 'CT_CVRD APE I5_CVRD TIG_0618_0122__test_zero_buyer_transference',
            'double_status': 'I',
            'fare': None,
            'flexibility': None,
            'id': None,
            'id_buyer_asset_items': None,
            'id_buyer_assets': None,
            'id_buyer_profile': buyer_profile.pk,
            'id_report': BDE_report,
            'id_submarket': generic_submarket.pk,
            'id_vendor_profile': vendor_profile.pk,
            'priorized_profile_id': Decimal('46'),
            'proinfa_flexibility': 'S',
            'seasonality': None,
            'transaction_type': 'ZERAR_COMPRADOR',
            'vendor_profile': 'CVRD APE I5',
            'volume': Decimal('0.000')
        })

    @tag('slow')
    def test_all_steps_to_balance(self):
        balance_service = self.setUpBalanceService()

        request_step_1 = balance_service.get_last_balance_fields()
        self.assertEqual(request_step_1.status_code, HTTP_200_OK)
        
        date_now = datetime.today()
        cliq_contracts = balance_service.get_cliq_contracts(date_now.month, date_now.year)

        request_step_2 = Response(SortProfileSerializer(cliq_contracts, many=True).data, HTTP_200_OK)
        self.assertEqual(request_step_2.status_code, HTTP_200_OK)
        
        balace_fields = request_step_1.data
        del balace_fields['id']

        balance_data = {
            'balance_fields': balace_fields,
            'priorized_cliq': request_step_2.data
        }

        new_balance_report = balance_service.generate_balance(balance_data)
        request_step_3 = Response(ReportsSerializer(Report.objects.get(id=new_balance_report.id)).data, status=HTTP_201_CREATED)

        body_step_3 = request_step_3.data
        self.assertEqual(request_step_3.status_code, HTTP_201_CREATED)
        self.assertEqual(body_step_3['status'], 'T')

        id_balance = body_step_3['id']

        try:
            balance = Report.objects.filter(report_type__initials__exact='BDE').get(id=id_balance)
            balance_service.save_balance(balance, 'System_Test_User')
        except AlreadySaved:
            request_step_4 = Response({"detail": f"{balance.report_name} is already saved."}, status=HTTP_412_PRECONDITION_FAILED)
        except PastDateLimit:
            request_step_4 = Response({"detail": f"Can't consolidate {balance.report_name} because it's already past the workday deadline."}, status=HTTP_412_PRECONDITION_FAILED)
        except Report.DoesNotExist:
            request_step_4 = Response({"detail": f"The Report id:{balance.report_name}, is  has already been saved or is not found."}, status=HTTP_412_PRECONDITION_FAILED)
        except Exception:
            request_step_4 = Response({"detail": f"Something went wrong, it was not possible to save balance."}, status=HTTP_500_INTERNAL_SERVER_ERROR)

        request_step_4 = Response(ReportsSerializer(balance).data, status=HTTP_200_OK)

        body_step_4 = request_step_4.data
        self.assertEqual(request_step_4.status_code, HTTP_200_OK)
        self.assertEqual(body_step_4['status'], 'S')

        balance = Report.objects.filter(report_type__initials__exact='BDE').get(id=id_balance)

        try:
            consolidated_balance = balance_service.consolidate_balance(id_balance, 'System_Test_User')
        except Report.DoesNotExist:
            request_step_5 = Response({"detail": "Specified balance id doesn't exist."}, status=HTTP_400_BAD_REQUEST)
        except OutOfDate:
            request_step_5 = Response({"detail": f"{balance.report_name} isn't the most up to date balance."}, status=HTTP_412_PRECONDITION_FAILED)
        except AlreadyConsolidated:
            request_step_5 = Response({"detail": f"{balance.report_name} is already consolidated."}, status=HTTP_412_PRECONDITION_FAILED)
        except PastDateLimit:
            request_step_5 = Response({"detail": f"Can't consolidate {balance.report_name} because it's already past the workday deadline."}, status=HTTP_412_PRECONDITION_FAILED)
        except Exception as e:
            request_step_5 = Response({"detail": f"Something went wrong. Couldn't change {balance.report_name} (id={balance.id}) status."}, status=HTTP_400_BAD_REQUEST)

        request_step_5 = Response(ReportsSerializer(consolidated_balance).data, status=HTTP_200_OK)

        body_step_5 = request_step_5.data
        self.assertEqual(request_step_5.status_code, HTTP_200_OK)
        self.assertEqual(body_step_5['status'], 'C')

    @staticmethod
    def mock_executed_cliqs(balance_service, profile_name_list):
        for profile_name in profile_name_list:
            balance_service.executed_cliqs[profile_name] = {
                'N': Decimal('0.0'),
                'NE': Decimal('0.0'),
                'SE/CO': Decimal('0.0'),
                'S': Decimal('0.0')
            }
        return balance_service

    def test_flat_cliq(self):
        balance_service = self.mock_executed_cliqs(BalanceService(), ['ECOM', 'CVRD APE I5'])
        ECOM = MockedMarketSettlement('ECOM')
        CVRD_APE_I5 = MockedMarketSettlement('CVRD APE I5')
        flat_cliq = PriorizedCliq.objects.get(contract_name='CVI_1,7_VALE_ECOM_0520__test_flat_cliq')
        flat_cliq_volume = balance_service.calculate_cliq_volume(flat_cliq, ECOM, CVRD_APE_I5, 'SE/CO')
        self.assertEqual(flat_cliq_volume, Decimal('-1264.800'))

    def test_zero_buyer_transference(self):
        balance_service = BalanceService()
        zero_buyer_cliq = PriorizedCliq.objects.get(contract_name='CT_CVRD APE I5_CVRD TIG_0618_0122__test_zero_buyer_transference')
        buyer_balance = MarketSettlement.objects.get(profile_name='test_market_settlement_0')
        transference_volume = balance_service.calculate_transference_volume(zero_buyer_cliq, buyer_balance, {}, None, False)
        self.assertEqual(transference_volume, Decimal('-3.0'))
    
    def test_zero_vendor_transference(self):
        balance_service = BalanceService()
        zero_vendor_cliq = PriorizedCliq.objects.get(contract_name='CT_CVRD APE I5_CVRD TIG_0618_0122__test_zero_buyer_transference')
        zero_vendor_cliq.transaction_type = 'ZERAR_VENDEDOR'
        vendor_balance = MarketSettlement.objects.get(profile_name='test_market_settlement_0')
        transference_volume = balance_service.calculate_transference_volume(zero_vendor_cliq, {}, vendor_balance, None, False)
        self.assertEqual(transference_volume, Decimal('0.0'))
    
    def test_balanced_transference(self):
        balance_service = BalanceService()
        balanced_cliq = PriorizedCliq.objects.get(contract_name='CT_CVRD APE I5_CVRD TIG_0618_0122__test_zero_buyer_transference')
        balanced_cliq.transaction_type = 'BALANCEADO'
        buyer_balance = MarketSettlement.objects.get(profile_name='test_market_settlement_0')
        vendor_balance = MarketSettlement.objects.get(profile_name='test_market_settlement_0')
        transference_volume = balance_service.calculate_transference_volume(balanced_cliq, buyer_balance, vendor_balance, 
                                                                            None, False)
        self.assertEqual(transference_volume, Decimal('0.0'))

    def test_flexible_conventional_and_buyer_is_a_profile(self):
        """Test for a flexible cliq whose buyer is a profile and flexibility type is conventional"""
        flexible_cliq = PriorizedCliq.objects.get(contract_name='CT_CVRD APE I5_CVRD TIG_0618_0122__test_zero_buyer_transference')
        balance_service = self.setUpBalanceService(flexible_cliq)
        cliq_instance = CliqContract.objects.first()
        cliq_instance.id_contract.flexib_energy_contract.max_flexibility_pu_offpeak = Decimal('1.0')
        cliq_instance.id_contract.flexib_energy_contract.min_flexibility_pu_offpeak = Decimal('1.0')
        flexible_cliq.cliq_type = 'flexivel'
        flexible_cliq.flexibility = 'CONVENCIONAL'
        flexible_cliq.transaction_type = 'VOLUME_FIXO'
        buyer_balance = MarketSettlement.objects.get(profile_name='test_market_settlement_0')
        buyer_balance.profile_name = flexible_cliq.buyer_profile
        flexible_volume = balance_service.calculate_flexible_volume(flexible_cliq, cliq_instance, buyer_balance, 
                                                                    buyer_balance, False)
        self.assertEqual(flexible_volume, Decimal('0.0'))

    def test_flexible_conventional_and_buyer_is_a_consumer(self):
        """Test for a flexible cliq whose buyer is an asset or asset item and flexibility type is conventional"""
        flexible_cliq = PriorizedCliq.objects.get(contract_name='CT_CVRD APE I5_CVRD TIG_0618_0122__test_zero_buyer_transference')
        balance_service = self.setUpBalanceService(flexible_cliq)
        cliq_instance = CliqContract.objects.first()
        cliq_instance.id_contract.flexib_energy_contract.max_flexibility_pu_offpeak = Decimal('1.0')
        cliq_instance.id_contract.flexib_energy_contract.min_flexibility_pu_offpeak = Decimal('1.0')
        flexible_cliq.cliq_type = 'flexivel'
        flexible_cliq.flexibility = 'CONVENCIONAL'
        flexible_cliq.transaction_type = 'VOLUME_FIXO'
        flexible_cliq.id_buyer_asset_items = AssetItems.objects.first().pk
        buyer_balance = MarketSettlement.objects.get(profile_name='test_market_settlement_0')
        buyer_balance.profile_name = flexible_cliq.buyer_profile
        flexible_volume = balance_service.calculate_flexible_volume(flexible_cliq, cliq_instance, buyer_balance, 
                                                                    buyer_balance, False)
        self.assertEqual(flexible_volume, Decimal('0.0'))

        flexible_cliq.flexibility = 'PONTA'
        cliq_instance.mwm_volume_peak = Decimal('0.0')
        cliq_instance.id_contract.flexib_energy_contract.max_flexibility_pu_peak = Decimal('1.0')
        cliq_instance.id_contract.flexib_energy_contract.min_flexibility_pu_peak = Decimal('1.0')
        flexible_volume_peak = balance_service.calculate_flexible_volume(flexible_cliq, cliq_instance, buyer_balance, 
                                                                    buyer_balance, False)
        self.assertEqual(flexible_volume_peak, Decimal('0.0'))

        flexible_cliq.flexibility = 'FORA PONTA'
        cliq_instance.mwm_volume_offpeak = Decimal('0.0')
        flexible_volume_peak = balance_service.calculate_flexible_volume(flexible_cliq, cliq_instance, buyer_balance, 
                                                                    buyer_balance, False)
        self.assertEqual(flexible_volume_peak, Decimal('0.0'))

        flexible_cliq.flexibility = 'PONTA E FORA PONTA'
        flexible_volume_peak_and_off_peak = balance_service.calculate_flexible_volume(flexible_cliq, cliq_instance, 
                                                                    buyer_balance, buyer_balance, False)
        self.assertEqual(flexible_volume_peak_and_off_peak, Decimal('0.0'))

    def test_clear_temporary_balance(self):
        datetime_now = datetime.now(get_local_timezone())
        TIMEDELTA = 1
        mocked_balance = Report.objects.get(report_name='mock_balance_report')
        mocked_balance.status = 'T'
        mocked_balance.creation_date = datetime_now - timedelta(hours=TIMEDELTA + 1)
        mocked_balance.save()

        temp_balance_count = Report.objects.filter(
                report_type__initials='BDE',
                status='T',
                creation_date__lte=(datetime_now - timedelta(hours=TIMEDELTA))
            ).count()
        log_detail = f'[{temp_balance_count}] report balance(s) were removed.'
        
        balance_service = BalanceService()

        with self.assertLogs('django', level='INFO') as django_log:
            balance_service.clear_temporary_balance()
            self.assertIn(log_detail, django_log.output[-1])

    def test_calculate_flexible_proportional_cliq_volume(self):
        mocked_detailed_report = Report.objects.get(report_name='mock_detailed_report')
        buyer_profile = Assets.objects.select_related('id_profile').filter(
            id_company__type__in=['I', 'R']
        ).exclude(
            status__in=['0', 'n', 'N']
        ).first().id_profile
        mocked_priorized_cliq = CliqContract.objects.first()
        cliq_volume = calculate_flexible_proportional_cliq_volume(mocked_priorized_cliq, mocked_detailed_report)
        self.assertEqual(cliq_volume, Decimal('0.0'))
    
    def test_is_nth_brazilian_workday(self):
        eigth_workday_on_a_weekday = datetime(2020, 7, 10)
        self.assertTrue(is_nth_brazilian_workday(eigth_workday_on_a_weekday, 8))
        self.assertFalse(is_nth_brazilian_workday(eigth_workday_on_a_weekday, 9))

        eigth_workday_on_a_weekend = datetime(2021, 5, 12)
        self.assertTrue(is_nth_brazilian_workday(eigth_workday_on_a_weekend, 8))
    
    def test_get_user_username(self):
        Request = namedtuple('Request', ['auth'])
        CN = '00000'
        USERFULLNAME = 'mock_username'
        mock_username = f'{CN} - {USERFULLNAME}'
        mock_auth = {'cn': CN, 'UserFullName': USERFULLNAME}
        mock_request = Request(mock_auth)
        self.assertEqual(get_user_username(mock_request), mock_username)
        self.assertEqual(get_user_username({}), 'System')

    def test_check_for_balances(self):
        YEAR = '2020'
        MONTH = '1'
        STATUS = 'S'
        found_reports = Report.objects.filter(
            report_type__initials__exact='BDE',
            month__icontains=MONTH,
            year__icontains=YEAR,
            status__icontains=STATUS
        )
        self.assertEqual(check_for_balances(YEAR, MONTH, STATUS), found_reports.exists())

    def test_get_one_by_id(self):
        with self.assertRaises(Exception) as cm:
            get_one_by_id([], 0)
        self.assertEqual(cm.exception.args[0].args[0], 'Not found')

        MockElement = namedtuple('MockElement', ['id'])
        mock_element = MockElement(0)
        with self.assertRaises(Exception) as cm:
            get_one_by_id([mock_element, mock_element], 0)
        self.assertEqual(cm.exception.args[0].args[0], 'More than one element founded.')

        mock_element_id_1 = MockElement(1)
        self.assertEqual(get_one_by_id([mock_element, mock_element_id_1], 1), mock_element_id_1)
    
    def test_get_many_by_property_value(self):
        self.assertEqual(get_many_by_property_value([], 'test', 0), [])

        MockElement = namedtuple('MockElement', ['test'])
        elements_list = [MockElement(1), MockElement(0), MockElement(0)]
        returned_elements = get_many_by_property_value(elements_list, 'test', 0)
        self.assertListEqual(returned_elements, [MockElement(0), MockElement(0)])
    
    def test_get_last_month_date(self):
        last_month_date = make_aware(datetime.now()).replace(day=1) - timedelta(days=1)
        last_month_result = get_last_month_date()
        self.assertEqual(last_month_result.month, last_month_date.month)
        self.assertEqual(last_month_result.year, last_month_date.year)