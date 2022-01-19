from rest_framework.test import APITestCase
from consumption_metering_reports.serializers import DetailedConsumptionReportDataSerializerNew, DetailedConsumptionReportDataViewSerializerNew
from django.test import TestCase
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_409_CONFLICT, HTTP_500_INTERNAL_SERVER_ERROR, \
    HTTP_400_BAD_REQUEST
from rest_framework.response import Response
from random import randrange
from .services import ReportService, GenerateProjectedDetailedDataServiceNew
from .repositories import DetailedConsumptionReportRepositoryNew, ProjectedConsumptionReportRepository
from django.db.models import *
from .models import *
from datetime import timedelta, date
from .utils import get_last_month_date


class NewDetailedReportTests(APITestCase):
    """
        Steps for run that test:
            python manage.py test --keepdb consumption_metering_reports
    """
    month = 6
    year = 2020

    def test_period_failed_or_not_found(self):

        mock_request = {
            'params': {
                'month': 99,
                'year': self.year,
                'status': "S",
                'limit_value': 10000
            },
            'report_name': 'RPD'
        }

        request = lambda: None
        setattr(request, 'data', mock_request)

        # created with random value, need return status code 201
        body_created, status = ReportService(ProjectedConsumptionReportRepository()).create(request)
        error_list = [HTTP_500_INTERNAL_SERVER_ERROR, HTTP_400_BAD_REQUEST, HTTP_409_CONFLICT]
        self.assertTrue(status in error_list)

        # if your write method Test with T capital,

    def test_detailed(self):
        mock_request = {
            'params': {
                'status': "S",
                'limit_value': 10000,
                'month': self.month,
                'year': self.year
            },
            'report_name': 'RPD'
        }

        request = lambda: None
        setattr(request, 'data', mock_request)
        setattr(request, 'query_params', {})
        setattr(request, 'build_absolute_uri', lambda: None)

        response_data, status = ReportService(DetailedConsumptionReportRepositoryNew()).create(request)

        self.assertEqual(status, HTTP_201_CREATED)
        self.assertIsInstance(response_data, Report)

        ReportService(DetailedConsumptionReportRepositoryNew()).create(request)

        response, status = ReportService(DetailedConsumptionReportRepositoryNew()).save_report(response_data, request)

        self.assertEqual(status, HTTP_200_OK)

        mock_request_list = self.mock_get_request()
        list_data, status = ReportService(DetailedConsumptionReportRepositoryNew()).list(mock_request_list)

        self.assertEqual(status, HTTP_200_OK)

        metering_report_data = MeteringReportData.objects.filter(report=list_data['results'][0]['id']).first()
        response, status = ReportService(DetailedConsumptionReportRepositoryNew()).change_losstype(
            metering_report_data,
            '2',
            request
        )
        self.assertEqual(status, HTTP_200_OK)

        metering_report_data = ReportService(DetailedConsumptionReportRepositoryNew()).get(request, metering_report_data.report_id)[0]['results'][0]

        response, status = ReportService(DetailedConsumptionReportRepositoryNew()).change_datasource(
            metering_report_data,
            'VALE',
            request
        )
        self.assertEqual(status, HTTP_200_OK)

        request.data['status'] = 'N'
        response_data, status = ReportService(DetailedConsumptionReportRepositoryNew()).update(request, response_data.pk)

        self.assertEqual(status, HTTP_200_OK)        

    def test_get_detailedcompsumption(self):
        print("teste1")
        self.test_detailed()
        request = self.mock_get_request()
        last_report = Report.objects.filter(report_type__initials__exact='RPD').latest('id')

        response_data, status = ReportService(DetailedConsumptionReportRepositoryNew()).get(request, last_report.pk)
        report =  DetailedConsumptionReportDataViewSerializerNew(response_data).data
        self.assertEqual(last_report.report_name, report['report_name'])

    def mock_build_absolute_uri(self):
        return '/#'

    def mock_get_request(self):
        query_params = {
            'page_size': '10',
            'encoding': 'utf-8',
            '__len__': '1'
        }
        request = lambda: None
        setattr(request, 'query_params', query_params)
        setattr(request, 'build_absolute_uri', self.mock_build_absolute_uri)
        return request
    
    def test_get_last_month_date(self):
        last_date = get_last_month_date()
        self.assertIsInstance(last_date, date)


    def test_edit_report(self):
        url = '/reports-api/detailed-consumption-new-data/'

        self.test_detailed()
        last_report: Report = Report.objects.filter(report_type__initials__exact='RPD').latest('id')
        data = {
            'params': {
                'month': self.month,
                'page_size': 10,
                'referenced_report_id': last_report.id,
                'update_consumptions': [last_report.metering_report_data.last().id],
                'year': self.year,
            }
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, HTTP_201_CREATED)


    def test_repository_get_queryset(self):
        self.test_detailed()
        request = self.mock_get_request()
        last_report: Report = Report.objects.filter(report_type__initials__exact='RPD').latest('id')
        
        response_data, status = ReportService(ProjectedConsumptionReportRepository()).get(request, last_report.pk)

        self.assertEqual(status, HTTP_200_OK)
        
        
    def test_edit_automatic_report(self):
        url = '/reports-api/schedule/generate-detailed-projected-consumption-new/'

        data = {
            'params': {
                'month': self.month,
                'page_size': 10,
                'year': self.year,
            }
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, HTTP_200_OK)
