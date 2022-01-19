from django.test import TestCase, tag
from django.db.models import *
from django.db import transaction

from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_409_CONFLICT, HTTP_500_INTERNAL_SERVER_ERROR, \
    HTTP_400_BAD_REQUEST
from rest_framework.response import Response

from .services import ReportService, GenerateProjectedDetailedDataService
from .repositories import GrossConsumptionReportRepository, ProjectedConsumptionReportRepository, \
    DetailedConsumptionReportRepository, clear_temporary_reports
from .models import *
from .serializers import DetailedConsumptionReportDataSerializer
from .repositories import ReportRepository
from random import randrange
from .utils import get_last_month_date, get_week_days, get_last_month_date

from datetime import timedelta, date
from collections import namedtuple
from unittest import mock


class ReportTests(TestCase):
    """
        Steps for run that test:
            python manage.py test --keepdb consumption_metering_reports
    """
    month = 6
    year = 2020

    def test_gross_saved_and_conflict(self):
        # route to api
        # route = 'reports-api/gross-consumption/'
        # month and year needing exist, because have an error.

        mock_request = {
            'params': {
                'month': self.month,
                'status': 'S',
                'year': self.year,
                'report_type': 1
            },
            'report_name': 'RCB'
        }

        request = lambda: None
        setattr(request, 'data', mock_request)

        body, status = ReportService(GrossConsumptionReportRepository()).create(request)

        if status == HTTP_409_CONFLICT:  # if having data in database.
            status_to_check = HTTP_409_CONFLICT
        elif status == HTTP_400_BAD_REQUEST:
            status_to_check = HTTP_400_BAD_REQUEST
        else:  # the correct case
            status_to_check = HTTP_201_CREATED
            self.assertIsInstance(body, Report)

        self.assertEqual(status, status_to_check)

        response, status = ReportService(GrossConsumptionReportRepository()).save_report(body, request)

        self.assertEqual(status, HTTP_200_OK)

        mock_request_list = self.mock_get_request()
        list_data, status = ReportService(GrossConsumptionReportRepository()).list(mock_request_list)

        self.assertEqual(status, HTTP_200_OK)

        request.data['status'] = 'N'
        response_data, status = ReportService(GrossConsumptionReportRepository()).update(request, body.pk)

        self.assertEqual(status, HTTP_200_OK)

        body.status = 'T'
        body.creation_date = datetime.utcnow() - timedelta(hours=1, minutes=10)
        body.save

        clear_temporary_reports()


    def test_gross_period_not_found(self):
        # any mouth and year, for return expected status code.

        mock_request = {
            'params': {
                'month': 60,
                'status': 'S',
                'year': 2089,
                'report_type': 1
            }
        }

        request = lambda: None
        setattr(request, 'data', mock_request)

        body, status = ReportService(GrossConsumptionReportRepository()).create(request)
        status_to_check = HTTP_400_BAD_REQUEST

        self.assertEqual(status, status_to_check)
        self.assertIsInstance(body, dict)

    def Test_projected_saved_and_conflict(self):
        # generate rando value to create
        random_limit_value = randrange(1000, 100000)

        mock_request = {
            'params': {
                'month': self.month,
                'year': self.year,
                'status': "S",
                'limit_value': random_limit_value
            },
            'report_name': 'RCD'
        }

        request = lambda: None
        setattr(request, 'data', mock_request)

        # created with random value, need return status code 201
        body_created, status_created = ReportService(ProjectedConsumptionReportRepository()).create(request)

        if status_created == HTTP_409_CONFLICT:  # if having data in database.
            status_to_check = HTTP_409_CONFLICT
        elif status_created == HTTP_400_BAD_REQUEST:
            status_to_check = HTTP_400_BAD_REQUEST
        else:  # the correct case
            status_to_check = HTTP_201_CREATED

        self.assertEqual(status_created, status_to_check)
        self.assertIsInstance(body_created, Report)

        return body_created.id, request

    def test_projected_period_failed_or_not_found(self):

        route = 'reports-api/projected-consumption/'

        mock_request = {
            'params': {
                'month': 99,
                'year': self.year,
                'status': "S",
                'limit_value': 10000
            },
            'report_name': 'RCP'
        }

        request = lambda: None
        setattr(request, 'data', mock_request)

        # created with random value, need return status code 201
        body_created, status = ReportService(ProjectedConsumptionReportRepository()).create(request)
        error_list = [HTTP_500_INTERNAL_SERVER_ERROR, HTTP_400_BAD_REQUEST, HTTP_409_CONFLICT]
        self.assertTrue(status in error_list)

        # if your write method Test with T capital,

    # you can call in other method test_...,
    # util for useful to have control of the execution flow 
    # and a data that depends on another
    @tag('slow')
    def Test_detailed(self, id):

        self.assertIsInstance(id, int)

        mock_request = {
            'params': {
                'status': "S",
                'referenced_report_id': id,
                'month': self.month,
                'year': self.year
            },
            'report_name': 'RCD'
        }

        request = lambda: None
        setattr(request, 'data', mock_request)

        response_data, status = ReportService(DetailedConsumptionReportRepository()).create(request)

        self.assertEqual(status, HTTP_201_CREATED)
        self.assertIsInstance(response_data, Report)

        ReportService(DetailedConsumptionReportRepository()).create(request)

        response, status = ReportService(DetailedConsumptionReportRepository()).save_report(response_data, request)

        self.assertEqual(status, HTTP_200_OK)

        mock_request_list = self.mock_get_request()
        list_data, status = ReportService(DetailedConsumptionReportRepository()).list(mock_request_list)

        self.assertEqual(status, HTTP_200_OK)

        metering_report_data = MeteringReportData.objects.filter(report=list_data['results'][0]['id']).first()
        response, status = ReportService(DetailedConsumptionReportRepository()).change_losstype(
            metering_report_data,
            '2',
            request
        )
        self.assertEqual(status, HTTP_200_OK)

        request.data['status'] = 'N'
        response_data, status = ReportService(DetailedConsumptionReportRepository()).update(request, response_data.pk)

        self.assertEqual(status, HTTP_200_OK)

        response_data.status = 'T'
        response_data.creation_date = datetime.utcnow() - timedelta(hours=1, minutes=10)
        response_data.save()

        clear_temporary_reports()

    @tag('slow')
    def test_project_and_detailed(self):
        id_projected, request = self.Test_projected_saved_and_conflict()
        self.Test_detailed(id_projected)

        # final of projected       
        body_conflict, status_conflict = ReportService(ProjectedConsumptionReportRepository()).create(request)

        self.assertEqual(status_conflict, HTTP_201_CREATED)
        self.assertIsInstance(body_conflict, Report)

        ReportService(ProjectedConsumptionReportRepository()).create(request)

        response, status = ReportService(ProjectedConsumptionReportRepository()).save_report(body_conflict, request)

        self.assertEqual(status, HTTP_200_OK)

        mock_request_list = self.mock_get_request()
        list_data, status = ReportService(ProjectedConsumptionReportRepository()).list(mock_request_list)

        self.assertEqual(status, HTTP_200_OK)

        metering_report_data = MeteringReportData.objects.filter(report=list_data['results'][0]['id']).first()
        response, status = ReportService(ProjectedConsumptionReportRepository()).change_datasource(
            metering_report_data,
           '2',
           request
        )
        self.assertEqual(status, HTTP_200_OK)

        request.data['status'] = 'N'
        response_data, status = ReportService(ProjectedConsumptionReportRepository()).update(request, body_conflict.pk)

        self.assertEqual(status, HTTP_200_OK)

        body_conflict.status = 'T'
        body_conflict.creation_date = datetime.utcnow() - timedelta(hours=1, minutes=10)
        body_conflict.save()

        clear_temporary_reports()

    def test_get_grosscompsumption(self):
        request = self.mock_get_request()
        last_report = Report.objects.filter(report_type__initials__exact='RCB').latest('id')
        report = ReportService(GrossConsumptionReportRepository()).get(request, last_report.pk)
        self.assertEqual(last_report.report_name, report[0]['report_name'])

    def test_get_projectedcompsumption(self):
        request = self.mock_get_request()
        last_report = Report.objects.filter(report_type__initials__exact='RCP').latest('id')
        report = ReportService(ProjectedConsumptionReportRepository()).get(request, last_report.pk)
        self.assertEqual(last_report.report_name, report[0]['report_name'])

    def test_get_detailedcompsumption(self):
        request = self.mock_get_request()
        last_report = Report.objects.filter(report_type__initials__exact='RCD').latest('id')
        report = ReportService(DetailedConsumptionReportRepository()).get(request, last_report.pk)
        self.assertEqual(last_report.report_name, report[0]['report_name'])

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

    def test_(self):
        report = Report.objects.filter(report_type__initials__exact='RCP').latest('id')

        last_projected_consumption = GenerateProjectedDetailedDataService(
            ProjectedConsumptionReportRepository()).get_last_project_consumption(report.month, report.year)
        self.assertEqual(report.month, last_projected_consumption.month)

    def test_get_week_days(self):
        day = get_week_days(2020, 1)
        self.assertTrue(len(day) > 0)

    def test_get_last_month_date(self):
        last_date = get_last_month_date()
        self.assertIsInstance(last_date, date)

    def test_check_same_sum_values(self):
        with transaction.atomic():
            metering_report_value = MeteringReportValue.objects.first()
            metering_report_value_queryset = MeteringReportValue.objects.filter(pk=metering_report_value.id)

        check_sum_result = ReportRepository().check_same_sum_values(metering_report_value_queryset, metering_report_value_queryset)
        self.assertTrue(check_sum_result)

    def test_DetailedConsumptionReportDataSerializer(self):
        fields = ['id', 'director_board', 'business', 'consumer', 'projected_consumption_off_peak', 'projected_consumption_on_peak',
                'total_projected_consumption', 'loss_percentage', 'total_projected_consumption_more_loss_type_1',
                'total_projected_consumption_more_loss_type_2', 'loss_type', 'projected_consumption_ccee', 'projected_consumption_vale']
        defaults = [0, 'test', 'test', 'test', 0, 0, 0, 0, 0, 0, '0', 0, 0]
        DetailedConsumptionReportDataSerializerMock = namedtuple('DetailedConsumptionReportDataSerializerMock', fields, defaults=defaults)

        detailed_consumption_report_mock = DetailedConsumptionReportDataSerializerMock()
        serialized_data = DetailedConsumptionReportDataSerializer(detailed_consumption_report_mock).data
        self.assertEqual(set(serialized_data.keys()), set(fields))
        self.assertEqual(len(fields), len(serialized_data))

        # covering when some of the fields are None
        detailed_consumption_report_empty_mock = DetailedConsumptionReportDataSerializerMock(*(None,)*len(fields))
        serialized_empty_data = DetailedConsumptionReportDataSerializer(detailed_consumption_report_empty_mock).data
        self.assertEqual(set(serialized_empty_data.keys()), set(fields))
        self.assertEqual(len(fields), len(serialized_empty_data))

    def test_gross_report_get(self):
        url = '/reports-api/gross-consumption/'
        response = self.client.get(url, {}, format='json')
        self.assertEqual(response.status_code, HTTP_200_OK)

    def test_projected_report_get(self):
        url = '/reports-api/projected-consumption/'
        response = self.client.get(url, {}, format='json')
        self.assertEqual(response.status_code, HTTP_200_OK)

    def test_detailed_report_get(self):
        url = '/reports-api/detailed-consumption/'
        response = self.client.get(url, {}, format='json')
        self.assertEqual(response.status_code, HTTP_200_OK)

    @mock.patch('consumption_metering_reports.views.get_last_month_date', return_value=date(2020, 6, 1))
    def test_generate_gross_consumption(self, get_last_month_date_function):
        url = '/reports-api/schedule/generate-gross-consumption/'
        response = self.client.post(url, {}, format='json')
        self.assertEqual(response.status_code, HTTP_200_OK)

    @mock.patch('consumption_metering_reports.views.get_last_month_date', return_value=date(2020, 6, 1))
    def test_generate_projected_and_detailed(self, get_last_month_date_function):
        with transaction.atomic():
            Report.objects.filter(month=6, year=2020, status='S').update(status='N')

        url_projected = '/reports-api/schedule/generate-projected-consumption/'
        response = self.client.post(url_projected, {}, format='json')
        self.assertEqual(response.status_code, HTTP_200_OK)

        url_detailed = '/reports-api/schedule/generate-detailed-projected-consumption/'
        response = self.client.post(url_detailed, {}, format='json')
        self.assertEqual(response.status_code, HTTP_200_OK)
