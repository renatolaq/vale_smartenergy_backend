from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import F, IntegerField, Value
from django.db.models.functions import Cast

from rest_framework.filters import OrderingFilter
from rest_framework.response import Response
from rest_framework.mixins import ListModelMixin
from rest_framework.decorators import api_view, authentication_classes
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_412_PRECONDITION_FAILED, HTTP_500_INTERNAL_SERVER_ERROR, HTTP_404_NOT_FOUND, HTTP_201_CREATED
from rest_framework import viewsets

from .serializers import ProjectedConsumptionReportDataViewSerializer, ProjectedConsumptionReportViewSerializer, GrossConsumptionReportViewSerializer, \
                GrossConsumptionReportDataViewSerializer, DetailedConsumptionReportDataViewSerializer, DetailedConsumptionReportViewSerializer, \
                ProjectedConsumptionReportListSerializer, DetailedConsumptionReportViewSerializerNew, DetailedConsumptionReportDataViewSerializerNew
from .models import *
from .utils import *
from django.db.models import *
from .models import Report, Log
from .services import *
from .repositories import *
from .utils import Paginator, replace_comma_with_dot, StrSQL, get_peak_time, get_last_month_date
from SmartEnergy.handler_logging import HandlerLog
from SmartEnergy.auth import check_permission, check_module
from .services import ReportService
import SmartEnergy.auth.permissions as permissions
import SmartEnergy.auth.groups as groups
import SmartEnergy.auth.modules as modules
from  SmartEnergy.auth.IAM import IAMAuthentication
import types


logger = HandlerLog()
class ProjectedConsumptionDataViewSet(viewsets.ViewSet):
    queryset = Report.objects.filter(report_type__initials__exact='RCP')

    @check_module(modules.projected_consumption, [permissions.EDITN1])
    def create(self, request):
        response_data, status = ReportService(ProjectedConsumptionReportRepository()).create(request)
        return Response(SavedReportSerializer(response_data).data if not isinstance(response_data, dict) else response_data, status)

class ProjectedConsumptionChangeDatasourceViewSet(viewsets.ViewSet):
    queryset = MeteringReportData.objects.filter(report__report_type__initials__exact='RCP')

    @check_module(modules.projected_consumption, [permissions.EDITN1])
    def update(self, request, pk=None):
        metering_report_data = self.queryset.get(id=pk)
        param = request.query_params
        response, status = ReportService(ProjectedConsumptionReportRepository()).change_datasource(metering_report_data, param['data_source'], request)
        return Response(response, status)

class ProjectedConsumptionSaveViewSet(viewsets.ViewSet):
    queryset = Report.objects.filter(report_type__initials__exact='RCP')

    @check_module(modules.projected_consumption, [permissions.EDITN1])
    def update(self, request, pk=None):
        report = self.queryset.get(id=pk)
        response, status = ReportService(ProjectedConsumptionReportRepository()).save_report(report, request)
        return Response(response, status)


class ProjectedConsumptionReportsViewSet(viewsets.ViewSet):
    queryset = Report.objects.filter(report_type__initials__exact='RCP')

    @check_module(modules.projected_consumption, [permissions.VIEW, permissions.EDITN1])
    def retrieve(self, request, pk=None):
        response_data, status = ReportService(ProjectedConsumptionReportRepository()).get(request, pk)
        return Response(ProjectedConsumptionReportDataViewSerializer(response_data).data, status)

    @check_module(modules.projected_consumption, [permissions.VIEW, permissions.EDITN1])
    def list(self, request):
        response_data, status = ReportService(ProjectedConsumptionReportRepository()).list(request)
        return Response(ProjectedConsumptionReportViewSerializer(response_data).data, status)

    @check_module(modules.projected_consumption, [permissions.EDITN1])
    def update(self, request, pk=None):
        response_data, status = ReportService(ProjectedConsumptionReportRepository()).update(request, pk)
        return Response(SavedReportSerializer(response_data).data if not isinstance(response_data, dict) else response_data, status)
    
    @check_module(modules.projected_consumption, [permissions.EDITN1])
    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

       
class GrossConsumptionReportsViewSet(viewsets.ViewSet):
    queryset = Report.objects.filter(report_type__initials__exact='RCB')
    
    @check_module(modules.gross_consumption, [permissions.VIEW, permissions.EDITN1])
    def retrieve(self, request, pk=None):
        response_data, status = ReportService(GrossConsumptionReportRepository()).get(request, pk)
        return Response(GrossConsumptionReportDataViewSerializer(response_data).data, status)

    @check_module(modules.gross_consumption, [permissions.VIEW, permissions.EDITN1])
    def list(self, request):
        response_data, status = ReportService(GrossConsumptionReportRepository()).list(request)
        return Response(GrossConsumptionReportViewSerializer(response_data).data, status)

    @check_module(modules.gross_consumption, [permissions.EDITN1])
    def update(self, request, pk=None):
        response_data, status = ReportService(GrossConsumptionReportRepository()).update(request, pk)
        return Response(SavedReportSerializer(response_data).data if not isinstance(response_data, dict) else response_data, status)
    
    @check_module(modules.gross_consumption, [permissions.EDITN1])
    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)


class GrossConsumptionDataViewSet(viewsets.ModelViewSet):
    queryset = Report.objects.filter(report_type__initials__exact='RCB')
    
    @check_module(modules.gross_consumption, [permissions.EDITN1])
    def create(self, request):
        response_data, status = ReportService(GrossConsumptionReportRepository()).create(request)
        return Response(SavedReportSerializer(response_data).data if not isinstance(response_data, dict) else response_data, status)


class GrossConsumptionSaveViewSet(viewsets.ViewSet):
    queryset = Report.objects.filter(report_type__initials__exact='RCB')

    @check_module(modules.gross_consumption, [permissions.EDITN1])
    def update(self, request, pk=None):
        report = self.queryset.get(id=pk)
        response, status = ReportService(GrossConsumptionReportRepository()).save_report(report, request)
        return Response(response, status)


class DetailedConsumptionDataViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Report.objects.filter(report_type__initials__exact='RCD')

    @check_module(modules.detailed_projected_consumption, [permissions.EDITN1])
    def create(self, request):
        response_data, status = ReportService(DetailedConsumptionReportRepository()).create(request)
        return Response(SavedReportSerializer(response_data).data if not isinstance(response_data, dict) else response_data, status)


class DetailedConsumptionReportsViewSet(viewsets.ModelViewSet):
    queryset = Report.objects.filter(report_type__initials__exact='RCD')
    pagination_class = Paginator
    filter_backends = [OrderingFilter]
    ordering_fields = '__all__'
    
    def get_queryset(self):
        return self.queryset.select_related('id_reference').filter(report_type__initials__exact='RCD')

    @check_module(modules.detailed_projected_consumption, [permissions.VIEW, permissions.EDITN1])
    def retrieve(self, request, pk=None):
        response_data, status = ReportService(DetailedConsumptionReportRepository()).get(request, pk)
        return Response(DetailedConsumptionReportDataViewSerializer(response_data).data, status)

    @check_module(modules.detailed_projected_consumption, [permissions.VIEW, permissions.EDITN1])
    def list(self, request):
        response_data, status = ReportService(DetailedConsumptionReportRepository()).list(request)
        return Response(DetailedConsumptionReportViewSerializer(response_data).data, status)
    
    @check_module(modules.detailed_projected_consumption, [permissions.EDITN1])
    def update(self, request, pk=None):
        response_data, status = ReportService(DetailedConsumptionReportRepository()).update(request, pk)
        return Response(SavedReportSerializer(response_data).data if not isinstance(response_data, dict) else response_data, status)
    
    @check_module(modules.detailed_projected_consumption, [permissions.EDITN1])
    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)


class DetailedConsumptionChangeLossTypeViewSet(viewsets.ViewSet):
    queryset = MeteringReportData.objects.filter(report__report_type__initials__exact='RCD')

    @check_module(modules.detailed_projected_consumption, [permissions.EDITN1])
    def update(self, request, pk=None):
        metering_report_data = self.queryset.get(id=pk)
        param = request.query_params
        response, status = ReportService(DetailedConsumptionReportRepository()).change_losstype(metering_report_data, param['loss_type'], request)
        return Response(response, status)


class DetailedConsumptionSaveViewSet(viewsets.ViewSet):
    queryset = Report.objects.filter(report_type__initials__exact='RCD')

    @check_module(modules.detailed_projected_consumption, [permissions.EDITN1])
    def update(self, request, pk=None):
        report = self.queryset.get(id=pk)
        response, status = ReportService(DetailedConsumptionReportRepository()).save_report(report, request)
        return Response(response, status)


class LogReportsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Log.objects.all()
    serializer_class = LogSerializer
    pagination_class = Paginator
    filter_backends = [OrderingFilter]
    ordering_fields = '__all__'
    
    @check_module([groups.administrator, groups.backoffice_commerce], [permissions.VIEW, permissions.EDITN1])
    def retrieve(self, request, pk=None):
        instance = self.queryset.filter(field_pk=pk, table_name='REPORT_TABLE').order_by('-date')
        serializer = self.get_serializer(instance, many=True)
        return Response(serializer.data, 200)


class ProjectedConsumptionReportListViewSet(ListModelMixin, viewsets.GenericViewSet):
    """Returns a list of Projected Consumption Reports (id and name) for month and year"""
    queryset = Report.objects.filter(
        report_type__initials__exact='RCP', 
        status='S')
    serializer_class = ProjectedConsumptionReportListSerializer
    paginator = None

    @check_module(modules.detailed_projected_consumption, [permissions.EDITN1])
    def get_queryset(self):
        month = self.request.query_params.get('month')
        year = self.request.query_params.get('year')
        
        if None in [month, year]:
            return self.queryset.none()
        else:
            return self.queryset.filter(month__icontains=month, year__icontains=year).order_by('-id')


@api_view(['POST'])
#@authentication_classes([IAMAuthentication])
@check_module(modules.gross_consumption, [permissions.EDITN1])
def generate_gross_consumption(request):
    """
    Checks if it is the third work day of the month only on weekdays, if it is, checks if there is
    a gross report saved last month, if there isn't a saved report saves a new report
    """
    try:
        queryset = Report.objects.filter(report_type__initials__exact='RCB')
        try:
            report_date = get_last_month_date()
            # Checks if there is already a report saved in the current month
            report_saved = queryset.filter(month=report_date.month, year=report_date.year, status='S')            
            if report_saved.exists():
                mock_request = {
                    'status': 'N',
                    'report_name': 'RCB'
                }
                request = lambda: None
                setattr(request, 'data', mock_request)
                response_data, status = ReportService(ProjectedConsumptionReportRepository()).update(request, report_saved.values('id').first()['id'])
                if status != HTTP_200_OK:
                    raise Exception
        except Report.DoesNotExist:
            pass

        # Saves a report with a temporary status
        mock_request = {
            'params':{
                'month': report_date.month,
                'status': 'S',
                'year': report_date.year,
                'report_type': 1.0
            }
        }
        request = lambda: None
        setattr(request, 'data', mock_request)
        body, status = ReportService(GrossConsumptionReportRepository()).create(request)
        if status != HTTP_201_CREATED:
            detail = f'INFO: Job Generate_Gross_Consumption was failed to generate. {body}'
            return Response({"message": detail}, status=status)

        # Updates the temporary status to saved
        report = queryset.get(id=body.pk)
        body, status = ReportService(GrossConsumptionReportRepository()).save_report(report, request)
        if status != HTTP_200_OK:
            detail = f'INFO: Job Generate_Gross_Consumption was failed to save. {body}'
            return Response({"message": detail}, status=status)

        # Returns success message
        detail = f'INFO: Job Generate_Gross_Consumption was successfully.'
        logger.info(detail)
        return Response({"message": detail}, status=HTTP_200_OK)
    except Exception as e:
        detail = f'INFO: Job Generate_Gross_Consumption was failed {str(e)}'
        logger.error(detail)
        return Response({"message": detail}, status=HTTP_412_PRECONDITION_FAILED)


@api_view(['POST'])
#@authentication_classes([IAMAuthentication])
@check_module(modules.projected_consumption, [permissions.EDITN1])
def generate_projected_consumption(request):
    """
    Checks if it is the third work day of the month only on weekdays, if it is, checks if there is
    a projected report saved last month, if there isn't a saved report saves a new report
    """
    try:
        queryset = Report.objects.filter(report_type__initials__exact='RCP')
        try:
            report_date = get_last_month_date()
            # Checks if there is already a report saved in the current month
            report_saved = queryset.filter(month=report_date.month, year=report_date.year, status='S')            
            if report_saved.exists():
                mock_request = {
                    'status': 'N',
                    'report_name': 'RCP'
                }
                request = lambda: None
                setattr(request, 'data', mock_request)
                response_data, status = ReportService(ProjectedConsumptionReportRepository()).update(request, report_saved.values('id').first()['id'])
                if status != HTTP_200_OK:
                    detail = f'INFO: Job Generate_Projected_Consumption was failed. {response_data}'
                    return Response({"message": detail}, status=status)
        except Report.DoesNotExist:
            pass

        # Saves a report with a temporary status
        mock_request = {
            'params':{
                'month': report_date.month, 
                'year': report_date.year, 
                'status': "S", 
                'limit_value': 0.05
            }
        }
        request = lambda: None
        setattr(request, 'data', mock_request)
        body, status = ReportService(ProjectedConsumptionReportRepository()).create(request)
        if status != HTTP_201_CREATED:
            detail = f'INFO: Job Generate_Projected_Consumption was failed to generate. {body}'
            return Response({"message": detail}, status=status)

        # Updates the temporary status to saved
        report = queryset.get(id=body.pk)
        body, status = ReportService(ProjectedConsumptionReportRepository()).save_report(report, request)
        if status != HTTP_200_OK:
            detail = f'INFO: Job Generate_Projected_Consumption was failed to save. {body}'
            return Response({"message": detail}, status=status)

        # Returns success message
        detail = f'INFO: Job Generate_Projected_Consumption was successfully.'
        logger.info(detail)
        return Response({"message": detail}, status=HTTP_200_OK)
    except Exception as e:
        detail = f'INFO: Job Generate_Projected_Consumption was failed. {str(e)}'
        logger.error(detail)
        return Response({"message": detail}, status=HTTP_412_PRECONDITION_FAILED)


@api_view(['POST'])
#@authentication_classes([IAMAuthentication])
@check_module(modules.detailed_projected_consumption, [permissions.EDITN1])
def generate_detailed_projected_consumption(request):
    """
    Checks if it is the third work day of the month only on weekdays, if it is, checks if there is
    a detailed report saved last month, if there isn't a saved report saves a new report
    """
    try:
        queryset = Report.objects.filter(report_type__initials__exact='RCD')
        try:
            report_date = get_last_month_date()
            last_projected_consumption = GenerateProjectedDetailedDataService(ProjectedConsumptionReportRepository()).get_last_project_consumption(report_date.month, report_date.year)
        except Report.DoesNotExist:
            detail = f'ERROR: Unable to generate detailed project report, projected does not exist.'
            logger.error(detail)
            return Response({"message": detail}, status=HTTP_412_PRECONDITION_FAILED)

        try:
            # Checks if there is already a report saved in the current month
            report_saved = queryset.filter(month=report_date.month, year=report_date.year, status='S')            
            if report_saved.exists():
                mock_request = {
                    'status': 'N',
                    'report_name': 'RCD'
                }
                request = lambda: None
                setattr(request, 'data', mock_request)
                response_data, status = ReportService(ProjectedConsumptionReportRepository()).update(request, report_saved.values('id').first()['id'])
                if status != HTTP_200_OK:
                    detail = f'INFO: Job Generate_Detailed_Projected_Consumption was failed.'
                    return Response({"message": detail}, status=status)
        except Report.DoesNotExist:
            pass

        # Saves a report with a temporary status
        mock_request = {
            'params':{
                'status': "S",
                'referenced_report_id': last_projected_consumption.id,
                'month': report_date.month,
                'year': report_date.year
            }
        }
        request = lambda: None
        setattr(request, 'data', mock_request)
        body, status = ReportService(DetailedConsumptionReportRepository()).create(request)
        if status != HTTP_201_CREATED:
            detail = f'INFO: Job Generate_Detailed_Projected_Consumption was failed to create. {body}'
            return Response({"message": detail}, status=status)

        # Updates the temporary status to saved
        report = queryset.get(id=body.pk)
        body, status = ReportService(DetailedConsumptionReportRepository()).save_report(report, request)
        if status != HTTP_200_OK:
            detail = f'INFO: Job Generate_Detailed_Projected_Consumption was failed to save. {body}'
            return Response({"message": detail}, status=status)

        # Returns success message
        detail = f'INFO: Job Generate_Detailed_Projected_Consumption was successfully.'
        logger.info(detail)
        return Response({"message": detail}, status=HTTP_200_OK)
    except Report.DoesNotExist as error:
        detail = f'ERROR: Unable to generate detailed project report. {str(error)}'
        logger.error(detail)
        return Response({"message": detail}, status=HTTP_412_PRECONDITION_FAILED)



#==========================================================================================================
#==========================================================================================================
#==========================================================================================================
#==========================================================================================================
#==========================================================================================================
class DetailedConsumptionReportsViewSetNew(viewsets.ModelViewSet):
    queryset = Report.objects.filter(report_type__initials__exact='RPD')
    pagination_class = Paginator
    filter_backends = [OrderingFilter]
    ordering_fields = '__all__'
    
    def get_queryset(self):
        return self.queryset.select_related('id_reference').filter(report_type__initials__exact='RPD')

    @check_module(modules.detailed_projected_consumption, [permissions.VIEW, permissions.EDITN1])
    def retrieve(self, request, pk=None):
        response_data, status = ReportService(DetailedConsumptionReportRepositoryNew()).get(request, pk)
        return Response(DetailedConsumptionReportDataViewSerializerNew(response_data).data, status)

    @check_module(modules.detailed_projected_consumption, [permissions.VIEW, permissions.EDITN1])
    def list(self, request):
        response_data, status = ReportService(DetailedConsumptionReportRepositoryNew()).list(request)
        return Response(DetailedConsumptionReportViewSerializerNew(response_data).data, status)
    
    @check_module(modules.detailed_projected_consumption, [permissions.EDITN1])
    def update(self, request, pk=None):
        response_data, status = ReportService(DetailedConsumptionReportRepositoryNew()).update(request, pk)
        return Response(SavedReportSerializer(response_data).data if not isinstance(response_data, dict) else response_data, status)
    
    @check_module(modules.detailed_projected_consumption, [permissions.EDITN1])
    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

class LogReportsViewSetNew(viewsets.ReadOnlyModelViewSet):
    queryset = Log.objects.all()
    serializer_class = LogSerializer
    pagination_class = Paginator
    filter_backends = [OrderingFilter]
    ordering_fields = '__all__'
    
    @check_module([groups.administrator, groups.backoffice_commerce], [permissions.VIEW, permissions.EDITN1])
    def retrieve(self, request, pk=None):
        instance = self.queryset.filter(field_pk=pk, table_name='REPORT_TABLE').order_by('-date')
        serializer = self.get_serializer(instance, many=True)
        return Response(serializer.data, 200)

class DetailedConsumptionDataViewSetNew(viewsets.ReadOnlyModelViewSet):
    queryset = Report.objects.filter(report_type__initials__exact='RPD')

    @check_module(modules.detailed_projected_consumption, [permissions.EDITN1])
    def create(self, request):
        response_data, status = ReportService(DetailedConsumptionReportRepositoryNew()).create(request)
        return Response(SavedReportSerializer(response_data).data if not isinstance(response_data, dict) else response_data, status)

class DetailedConsumptionChangeLossTypeViewSetNew(viewsets.ViewSet):
    queryset = MeteringReportData.objects.filter(report__report_type__initials__exact='RPD')

    @check_module(modules.detailed_projected_consumption, [permissions.EDITN1])
    def update(self, request, pk=None):
        metering_report_data = self.queryset.get(id=pk)
        param = request.query_params
        response, status = ReportService(DetailedConsumptionReportRepositoryNew()).change_losstype(metering_report_data, param['loss_type'], request)
        return Response(response, status)

class DetailedConsumptionSaveViewSetNew(viewsets.ViewSet):
    queryset = Report.objects.filter(report_type__initials__exact='RPD')

    @check_module(modules.detailed_projected_consumption, [permissions.EDITN1])
    def update(self, request, pk=None):
        report = self.queryset.get(id=pk)
        response, status = ReportService(DetailedConsumptionReportRepositoryNew()).save_report(report, request)
        return Response(response, status)

@api_view(['POST'])
@check_module(modules.detailed_projected_consumption, [permissions.EDITN1])
def generate_detailed_projected_consumption_new(request):
    """
    Checks if it is the third work day of the month only on weekdays, if it is, checks if there is
    a detailed report saved last month, if there isn't a saved report saves a new report
    """
    try:
        queryset = Report.objects.filter(report_type__initials__exact='RPD')
        report_date = get_last_month_date()

        try:
            # Checks if there is already a report saved in the current month
            report_saved = queryset.filter(month=report_date.month, year=report_date.year, status='S')            
            if report_saved.exists():
                mock_request = {
                    'status': 'N',
                    'report_name': 'RPD'
                }
                request = lambda: None
                setattr(request, 'data', mock_request)
                response_data, status = ReportService(DetailedConsumptionReportRepositoryNew()).update(request, report_saved.values('id').first()['id'])
                if status != HTTP_200_OK:
                    detail = f'INFO: Job generate_detailed_projected_consumption_new was failed.'
                    return Response({"message": detail}, status=status)
        except Report.DoesNotExist:
            pass
        
        # Saves a report with a temporary status
        mock_request = {
            'params':{
                'status': "S",
                'month': report_date.month,
                'year': report_date.year,
                'limit_value': 0.05
            }
        }
        request = lambda: None
        setattr(request, 'data', mock_request)
        body, status = ReportService(DetailedConsumptionReportRepositoryNew()).create(request)
        if status != HTTP_201_CREATED:
            detail = f'INFO: Job generate_detailed_projected_consumption_new was failed to create. {body}'
            return Response({"message": detail}, status=status)

        # Updates the temporary status to saved
        report = queryset.get(id=body.pk)
        body, status = ReportService(DetailedConsumptionReportRepositoryNew()).save_report(report, request)
        if status != HTTP_200_OK:
            detail = f'INFO: Job generate_detailed_projected_consumption_new was failed to save. {body}'
            return Response({"message": detail}, status=status)

        # Returns success message
        detail = f'INFO: Job generate_detailed_projected_consumption_new was successfully.'
        logger.info(detail)
        return Response({"message": detail}, status=HTTP_200_OK)
    except Report.DoesNotExist as error:
        detail = f'ERROR: Unable to generate new detailed project report. {str(error)}'
        logger.error(detail)
        return Response({"message": detail}, status=HTTP_412_PRECONDITION_FAILED)


class DetailedConsumptionChangeChangeDatasourceViewSet(viewsets.ViewSet):
    queryset = MeteringReportData.objects.filter(report__report_type__initials__exact='RPD')

    @check_module(modules.projected_consumption, [permissions.EDITN1])
    def update(self, request, pk=None):
        param = request.query_params
        report_service = ReportService(DetailedConsumptionReportRepositoryNew())
        metering_report_data = self.queryset.get(id=pk)
        request.query_params._mutable = True
        request.query_params['id'] = pk
        data_source = request.query_params['data_source']
        del request.query_params['data_source']
        metering_report_data = report_service.get(request, metering_report_data.report_id)[0]['results'][0]
        request.query_params['data_source'] = data_source
        response, status = report_service.change_datasource(metering_report_data, param['data_source'], request)
        return Response(response, status)