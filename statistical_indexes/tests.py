from django.test import TestCase
from django.db.models import F, DecimalField, CharField, Value
from django.utils.timezone import make_aware
from rest_framework.status import HTTP_201_CREATED, HTTP_200_OK, HTTP_501_NOT_IMPLEMENTED, HTTP_403_FORBIDDEN, \
    HTTP_501_NOT_IMPLEMENTED

from .service import StatisticalIndexService, SAPService
from .models import Company, CompanyReference, Report, ReportType, KSB1, ImportSource, StatisticalIndex, GaugePoint, GaugeData
from .serializers import CompanyReferenceSerializer
from .utils import get_local_timezone, is_nth_brazilian_workday
from energy_composition.models import EnergyComposition, ApportiomentComposition
from energy_composition.models import Company as EnergyCompositionCompany
from global_variables.models import Variable, GlobalVariable, Unity
from SmartEnergy.handler_logging import HandlerLog

from datetime import datetime, timedelta
from collections import namedtuple
from decimal import Decimal
from calendar import monthrange
import json
from unittest import mock

class TestStatistical(TestCase):
    logger = HandlerLog()
    statistical_index_service = StatisticalIndexService()
    queryset = None
    company = None
    datetime_now = datetime.now(get_local_timezone())

    @staticmethod
    def setUpReport(report_type, report_name, mock_date, reference_report=None, status='S'):
        month = mock_date.month
        year = mock_date.year
        report_type_id = ReportType.objects.get(initials=report_type).id
        reference_report_id = reference_report.id if reference_report else None
        report = Report(None, report_type_id, reference_report_id, mock_date, report_name, status, month, year, None)
        report.save()
        return report
    
    @staticmethod
    def setUpFixedApprtRate(value=Decimal('1.0')):
        tfr = GlobalVariable.objects.filter(variable__name='TARIFA FIXA DE RATEIO')
        if not tfr.exists():
            FIXED_APPRT_RATE = Variable.objects.get(name='TARIFA FIXA DE RATEIO')
            FIXED_APPRT_RATE_UNIT = Unity.objects.get(description='Valor monetário')
            global_tfr = GlobalVariable(variable=FIXED_APPRT_RATE, unity=FIXED_APPRT_RATE_UNIT, state=None, value=value, \
                                        month=None, year=None, marketing=False, status=True)
        else:
            global_tfr = tfr.get()
            global_tfr.value = value
        global_tfr.save()
        return global_tfr

    @staticmethod
    def setUpKSB1(cost_center, cost_element, company_sap_id, value, month, year):
        mock_date = make_aware(datetime.now())
        MANUAL_IMPORT = ImportSource.objects.get(import_type='Manual')
        KSB1.objects.first()
        mock_KSB1 = KSB1(id_import_source=MANUAL_IMPORT, cost_center=cost_center, cost_element_description='test',
                        cost_element=cost_element, time_period=month, currency_value=value, utc_creation=mock_date,
                        incoming_date=mock_date, incoming_time='00:00:00', release_date=mock_date, document_number=0000000,
                        exercise=year, company=company_sap_id, mr_value=value)
        mock_KSB1.save()
        return mock_KSB1
    
    @staticmethod
    def setUpCompanyReference(status=0, mock_date=make_aware(datetime.now())):
        mock_company = Company.objects.first()
        mock_company_reference = CompanyReference(id_company=mock_company, transaction_type='A', 
                                                index_name='test_company_reference', creation_date=mock_date,
                                                month=mock_date.month, year=mock_date.year, cost_type='1', status=status)
        mock_company_reference.save()
        return mock_company_reference
    
    @staticmethod
    def setUpStatisticalIndex(company_reference, value, unit, name):
        mock_apprt = ApportiomentComposition.objects.first()
        mock_statistical_index = StatisticalIndex(id_reference=company_reference, id_apport=mock_apprt, value=value,
                                                unity=unit, rate_apportionment=Decimal('1.0'), associated_company=name)
        mock_statistical_index.save()
        return mock_statistical_index
    
    def setUp(self):
        mock_date = make_aware(datetime.now())
        RCP_report = self.setUpReport('RCP', 'mock_projected_report', mock_date, None)
        RCD_report = self.setUpReport('RCD', 'mock_detailed_report', mock_date, RCP_report)
        BDE_report = self.setUpReport('BDE', 'mock_balance_report', mock_date, RCD_report, 'C')
        BDE_report_june = self.setUpReport('BDE', 'mock_balance_report_june', datetime(2020, 6, 1), RCD_report, 'C')

        last_month_date = mock_date.replace(day=1) - timedelta(days=1)
        BDE_report_last_month = self.setUpReport('BDE', 'mock_balance_report_last_month', last_month_date, RCD_report, 'C')

        tfr = self.setUpFixedApprtRate()
        mock_KSB1 = self.setUpKSB1(1720032, 50, 1001, 0, datetime.now().month, datetime.now().year)
        mock_KSB1_june = self.setUpKSB1(1720032, 50, 1001, 0, 6, 2020)

    def test_statistical_indexes(self):
        DEACTIVATED = ['0', 'n', 'N']
        INTERNAL = 'I'
        SUBSIDIARY = 'F'

        try:
            companies_id = ApportiomentComposition.objects.filter(status='S').values('id_company_id').distinct()
            companies = Company.objects.all().exclude(
                status__in=DEACTIVATED
            ).filter(
                pk__in=companies_id,
                type__in=[INTERNAL, SUBSIDIARY]
            ).order_by('company_name')

            for company in companies:
                try:
                    self.queryset = ApportiomentComposition.objects.select_related('id_company').filter(
                        status='S',
                        id_company__pk=company.id_company
                    ).annotate(
                        value=Value('0', output_field=DecimalField()),
                        unit=Value('kWh', output_field=CharField()),
                        associated_company=F('id_energy_composition__id_company__company_name')
                    ).order_by('id_company__company_name')
                    self.company = company
                    if self.queryset.exists():
                        break

                except ApportiomentComposition.DoesNotExist:
                    self.logger.error("ERROR: No apportionmentComposition found in database.")
        except Company.DoesNotExist:
            self.logger.error("ERROR: No companies found in database.")

        if not self.company and not self.queryset:
            self.logger.error("ERROR: fail statistical_indexes, no Apportionment found in database.")
            return
        params = {
            'params': {
                'company_id': self.company.id_company,
                'year': self.datetime_now.year,
                'month': self.datetime_now.month,
                'index_type': 'A',
                'opt': '1'
            }
        }
        auth = {
            'cn': 'c0000000',
            'UserFullName': 'Running Django Tests'
        }
        mock = namedtuple('Mock', ['data', 'auth'])
        mock.data = params
        mock.auth = auth
        response = self.statistical_index_service.generate_data(self.queryset, mock, self.mock_location)
        self.assertEqual(response.status_code, HTTP_201_CREATED)

        if response.status_code is not 201:
            self.logger.error(
                f'ERROR: Fail to generate the statistical indexes for company [{self.company.company_name}]')
        else:
            # Send a statistical index
            generated_indexex_dict = response.data
            index = CompanyReference.objects.get(pk=generated_indexex_dict['id'])
            saved_indexes = self.statistical_index_service.send_index(mock, index)

            self.assertEqual(saved_indexes.status_code, HTTP_501_NOT_IMPLEMENTED) # TODO: Change test when SAP integration is done
            if saved_indexes.status_code is not HTTP_200_OK:
                self.logger.error(
                    f'ERROR: Fail to send statistical-indexes temp_id: [{generated_indexex_dict["id"]} to SAP.')
        
        # Testing option 2 for cost calculation
        mock.data['params']['opt'] = '2'
        response = self.statistical_index_service.generate_data(self.queryset, mock, self.mock_location)
        self.assertEqual(response.status_code, HTTP_201_CREATED)

    def mock_location(self, data):
        return {'Location': '/'}

    def test_get_statistical_indexes_filtered_ordered(self):
        mock_request = MockRequest({
                'unity': 'test',
                'cost_center': 'test',
                'statistic_index': 'test',
                'formatted_value': 'test',
                'associated_company': 'test',
                'ordering': 'unity'
            }, {}, {})
        mock_indexes_dict = [
            {'unity': 'test', 'cost_center': 'test', 'statistic_index': 'test', 'formatted_value': 'test', 
                'associated_company': 'test'},
            {'unity': 'statistical index', 'cost_center': 'test', 'statistic_index': 'test', 'formatted_value': 'test', 
                'associated_company': 'test'}
        ]
        filtered_indexes = self.statistical_index_service.get_statistical_indexes_filtered_ordered(mock_indexes_dict, 
                                                                                                    mock_request)
        self.assertEqual(len(filtered_indexes), 1)

    def test_reverse_index(self):
        last_day_of_the_month = monthrange(datetime.now().year, datetime.now().month)[1]
        statistical_index_service = self.statistical_index_service
        statistical_index_service.window_day = last_day_of_the_month
        statistical_index_service.limit_hour = 23

        SENT_MANUALLY_TO_SAP = '4'
        mock_company_reference = self.setUpCompanyReference(status=SENT_MANUALLY_TO_SAP)
        mock_statistical_index = self.setUpStatisticalIndex(mock_company_reference, Decimal('0.0'), 'R$', 
                                                            'test_statistical_index_cost')
        mock_get_object = lambda: mock_company_reference
        mock_get_serializer = lambda company_reference: CompanyReferenceSerializer(company_reference)
        mock_request = MockRequest({'observation_logs': 'test_reverse_index'}, {'cn': 0000, 'UserFullName': 'test_index'}, {})
        reverse_index_response = statistical_index_service.reverse_index(mock_get_object, mock_get_serializer, mock_request)
        self.assertEqual(reverse_index_response.status_code, 503) #TODO: Change test when SAP integration is done 
    
    def test_resend_index(self):
        SENDING_COMMUNICATION_FAILURE = '3'
        mock_company_reference = self.setUpCompanyReference(status=SENDING_COMMUNICATION_FAILURE)
        mock_get_object = lambda: mock_company_reference
        mock_get_serializer = lambda company_reference: CompanyReferenceSerializer(company_reference)
        mock_request = MockRequest({}, {}, {'sap_document_number': '0000'})
        resend_index_response = self.statistical_index_service.resend_index(mock_get_object, mock_get_serializer, mock_request)
        self.assertEqual(resend_index_response.status_code, HTTP_200_OK)

        mock_company_reference.status = 'invalid_status'
        invalid_status_response = self.statistical_index_service.resend_index(mock_get_object, mock_get_serializer, mock_request)
        self.assertEqual(invalid_status_response.status_code, HTTP_403_FORBIDDEN)

    def test_clear_temporary_index(self):
        datetime_now = datetime.now(get_local_timezone())
        TIMEDELTA = 1
        TEMPORARY_STATUS = '0'
        mock_company_reference = self.setUpCompanyReference(status=TEMPORARY_STATUS)
        mock_company_reference.creation_date = datetime_now - timedelta(hours=TIMEDELTA + 1)
        mock_company_reference.save()

        temp_company_reference_count = CompanyReference.objects.filter(
                status__exact='0',
                creation_date__lte=(datetime_now - timedelta(hours=TIMEDELTA))
            ).count()

        log_detail = f'[{temp_company_reference_count}] statistical index(es) were removed.'

        with self.assertLogs('django', level='INFO') as django_log:
            self.statistical_index_service.clear_temporary_index()
            self.assertIn(log_detail, django_log.output[-1])

    def test_generate_and_sender_statistical_indexes(self):
        mock_get_success_headers = lambda: {}
        log_detail = 'Job Generate and sender Statistical Indexes was successfully ran at'

        with self.assertLogs('django', level='INFO') as django_log:
            self.statistical_index_service.generate_and_sender_statistical_indexes({}, mock_get_success_headers)
            self.assertIn(log_detail, django_log.output[-1])

    def test_update_flat_rate_apportionment(self):
        log_detail = 'Job Update flat rate apportionment was successfully ran at'

        SENT_MANUALLY_TO_SAP = '4'
        mock_company_reference = self.setUpCompanyReference(status=SENT_MANUALLY_TO_SAP)
        mock_statistical_index = self.setUpStatisticalIndex(mock_company_reference, Decimal('0.0'), 'R$', 
                                                            'test_statistical_index_cost')
        last_month_date = make_aware(datetime.now()).replace(day=1) - timedelta(days=1)
        mock_company_reference.month = last_month_date.month
        mock_company_reference.year = last_month_date.year
        mock_company_reference.save()

        with self.assertLogs('django', level='INFO') as django_log:
            self.statistical_index_service.update_flat_rate_apportionment()
            self.assertIn(log_detail, django_log.output[-1])
    
    def test_statistical_index_for_subsidiary_company(self):
        mock_date = datetime.now()
        mock_get_success_headers = lambda x: {}

        mock_company = Company.objects.filter(status='S').first()
        mock_company.company_name = 'test_statistical_index_for_subsidiary_company'
        mock_company.type = 'F'
        mock_company.save()

        mock_gauge_point = GaugePoint.objects.filter(status='S').first()
        mock_gauge_point.id_company = mock_company
        mock_gauge_point.save()

        mock_gauge_data = GaugeData.objects.first()
        mock_gauge_data.id_gauge = mock_gauge_point
        mock_gauge_data.utc_gauge = make_aware(mock_date)
        mock_gauge_data.value = Decimal('5.0')
        mock_gauge_data.save()

        mock_company_from_energy_comp = EnergyCompositionCompany.objects.get(pk=mock_company.pk)

        mock_energy_composition = EnergyComposition.objects.filter(status='S').first()
        mock_energy_composition.kpi_formulae = "{'id':'temp','key':'A'}".replace('temp', str(mock_gauge_point.pk))
        mock_energy_composition.id_company = mock_company_from_energy_comp
        mock_energy_composition.save()

        mock_apprt_composition = ApportiomentComposition.objects.first()
        mock_apprt_composition.id_energy_composition = mock_energy_composition
        mock_apprt_composition.id_company = mock_company_from_energy_comp
        mock_apprt_composition.save()

        mock_queryset = ApportiomentComposition.objects.filter(pk=mock_apprt_composition.pk).annotate(
            value=Value('0', output_field=DecimalField()),
            unit=Value('kWh', output_field=CharField()),
            associated_company=F('id_energy_composition__id_company__company_name')
        )

        mock_request = MockRequest({}, 
            {
                'cn': 'c0000',
                'UserFullName': 'test_statistical_index_for_subsidiary_company'
            },
            {
                'params': {
                    'company_id': mock_company.id_company,
                    'year': mock_date.year,
                    'month': mock_date.month,
                    'index_type': 'V',
                    'opt': '1'
                }
            }
        )

        test_response = self.statistical_index_service.generate_data(mock_queryset, mock_request, mock_get_success_headers)
        self.assertEqual(test_response.status_code, HTTP_201_CREATED)

    def test_get_statistical_indexes_from_sap(self):
        mock_indexes = {}
        mock_logger = self.statistical_index_service.logger
        sap_service = SAPService()
        log_detail = 'SAP integration hasn\'t been implemented.' # TODO: Change test when SAP integration is done 

        with self.assertLogs('django', level='WARNING') as django_log:
            sap_service.get_statistical_indexes_from_sap(mock_indexes, mock_logger)
            self.assertIn(log_detail, django_log.output[-1])
    
    def test_generate_data_params_errors(self):
        mock_date = datetime.now()
        mock_request = MockRequest({}, {},
            {
                'params': {
                    'company_id': Company.objects.first().pk,
                    'year': mock_date.year,
                    'month': mock_date.month,
                    'index_type': 'test',
                    'opt': '1'
                }
            }
        )

        response_index_type_error = self.statistical_index_service.generate_data(None, mock_request, None)
        self.assertEqual(response_index_type_error.data['message'], 'error_invalid_index')

        mock_request.data['params']['index_type'] = 'C'
        mock_queryset = ApportiomentComposition.objects.none()
        response_index_type_error = self.statistical_index_service.generate_data(mock_queryset, mock_request, None)
        self.assertEqual(response_index_type_error.data['message'], 'error_no_apportionment_composition')

        mock_request.data['params']['opt'] = '0'
        response_index_type_error = self.statistical_index_service.generate_data(None, mock_request, None)
        self.assertEqual(response_index_type_error.data['message'], 'error_cost_index_flag')

    def test_save_index(self):
        TEMPORARY = '0'
        SAVED = '9'
        mock_company_reference = self.setUpCompanyReference(status=TEMPORARY)
        mock_get_object = lambda: mock_company_reference
        mock_get_serializer = lambda company_reference: CompanyReferenceSerializer(company_reference)
        mock_request = MockRequest({'observation_logs': 'test save index'}, {}, {})

        saved_index = self.statistical_index_service.save_index(mock_get_object, mock_get_serializer, mock_request)
        self.assertEqual(saved_index.data['status'], SAVED)

        # reset status to temporary
        mock_company_reference.status = TEMPORARY
        mock_company_reference.save()

        mock_company_reference.status = 'invalid_status'
        saved_index = self.statistical_index_service.save_index(mock_get_object, mock_get_serializer, mock_request)
        self.assertEqual(saved_index.data['message'], 'error_invalid_status_update')

    def test_is_nth_brazilian_workday(self):
        eigth_workday_on_a_weekday = datetime(2020, 7, 10)
        self.assertTrue(is_nth_brazilian_workday(eigth_workday_on_a_weekday, 8))
        self.assertFalse(is_nth_brazilian_workday(eigth_workday_on_a_weekday, 9))

        eigth_workday_on_a_weekend = datetime(2021, 5, 12)
        self.assertTrue(is_nth_brazilian_workday(eigth_workday_on_a_weekend, 8))
    
    @mock.patch('statistical_indexes.service.StatisticalIndexService.check_window_time', return_value=True)
    def test_statistical_indexes_views(self, check_window_time_function):
        mock_company = ApportiomentComposition.objects.exclude(status='N').first().id_company
        params = {
                'params': {
                    'company_id': int(mock_company.id_company),
                    'year': 2020,
                    'month': 6,
                    'index_type': 'A',
                    'opt': '1'
            }}

        generate_index_url = '/statistical-indexes-api/indexes-data/'
        response_generated = self.client.post(generate_index_url, data=json.dumps(params),
                                content_type='application/json')
        self.assertEqual(response_generated.status_code, HTTP_201_CREATED)

        index_id = response_generated.data['id']

        save_index_url = f'/statistical-indexes-api/save/{index_id}/'
        response_saved = self.client.put(save_index_url, {}, content_type='application/json')
        self.assertEqual(response_saved.status_code, HTTP_200_OK)

        get_index_url = f'/statistical-indexes-api/indexes/{index_id}/'
        response_get_by_id = self.client.get(get_index_url, {}, content_type='application/json')
        self.assertEqual(response_get_by_id.status_code, HTTP_200_OK)

        get_index_data_url = '/statistical-indexes-api/show-indexes/'
        response_get_index_data = self.client.get(get_index_data_url, {'id': index_id}, 
            content_type='application/json')
        self.assertEqual(response_get_index_data.status_code, HTTP_200_OK)

        get_indexes_list_url = '/statistical-indexes-api/indexes/'
        response_get_list = self.client.get(get_indexes_list_url, {}, content_type='application/json')
        self.assertEqual(response_get_list.status_code, HTTP_200_OK)
        
        url_send_to_sap = '/statistical-indexes-api/indexes/'
        response_sent_to_sap = self.client.post(url_send_to_sap, data=json.dumps({'temp_id': index_id}),
                                content_type='application/json')
        self.assertEqual(response_sent_to_sap.status_code, HTTP_501_NOT_IMPLEMENTED) # TODO: change when integration to sap is done

MockRequest = namedtuple('MockRequest', ['query_params', 'auth', 'data'])
