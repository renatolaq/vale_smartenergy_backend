from .repositories import ReportRepository
from .models import Report, GaugePoint, Assets
from rest_framework.status import HTTP_201_CREATED, HTTP_200_OK
from .factories import PaginatedDataFactory
from django.utils import timezone
from .utils import ValidationError
from .exceptions import AlreadySaved, PreconditionFailed
from .serializers import DetailedConsumptionReportDataSerializerNew

class ReportService:
    def __init__(self, report_repository: ReportRepository):
        self.__report_repository = report_repository

    def create(self, request):
        if 'params' in request.data:
            params = request.data['params'].copy()
        else:
            params = request.data.copy()
        params.setdefault('data_source', {})
        params['status'] = 'S'
        params['creation_date'] = timezone.now()
        params['report_name'] = self.__report_repository.createReportName(self.__report_repository.report_type, int(params['month']), int(params['year']))
        try:
            params['user'] = request.auth.get('FirstName', 'System')
        except:
            params['user'] = 'System'

        try:
            saved_report = self.__report_repository.create(params, request)
        except GaugePoint.DoesNotExist as error:
            return ({'message': str(error)}, 400)
        except Assets.DoesNotExist as error:
            return ({'message': str(error)}, 400)
        except Report.DoesNotExist as error:
            return ({'message': 'error_no_metering_data'}, 409)
        except ValueError as error:
            return ({'message': 'error_duplicated_report'}, 409)
        except PreconditionFailed as error:
            return ({'message': 'error_no_energy_composition',
                     'consumer': error.args[0]["asset"]}, error.status_code)
        except AttributeError as error:
            return ({'message': str(error)}, 400)
        return (saved_report, HTTP_201_CREATED)

    def get(self, request, pk):
        try:
            return (self.__report_repository.get(request, pk), HTTP_200_OK)
        except IndexError as error:
            return (PaginatedDataFactory.get_paginated_data(), HTTP_200_OK)

    def update(self, request, pk):
        params = request.data
        params['user'] = request.auth.get('FirstName') if 'auth' in dir(request) else 'System'
        
        if not 'status' in params or params['status'] not in ['S', 'N']:
            return ({'message': 'error_invalid_status'}, 400)

        try:
            updated_report = self.__report_repository.update(params, request, pk)
            return (updated_report, HTTP_200_OK)
        except ValidationError as e:
            return ({'message': e.args[0].get('message', ''), 'active_reports': e.args[0].get('active_reports', '')}, 412)
        except Report.DoesNotExist:
            return ({'message': 'error_report_doesnt_exist'}, 409)
        except ValueError as e:
            return ({'message': e.args[0]}, 409)

    def list(self, request):
        return (self.__report_repository.list(request), HTTP_200_OK)
    
    def save_report(self, report, request):
        """Checks if report is already saved and changes report status to Saved 'S'."""
        if report.status != 'T':
            raise AlreadySaved(detail='error_already_saved_report')

        if self.__report_repository.check_if_already_saved(report):
            return ({'message': 'error_duplicated_report'}, 409)

        report.status = 'S'
        report.save(update_fields=['status'])
        response = {}
        try:
            response['detail'] = 'info_saved_report'
        except:
            pass
        return response, 200
    
    def change_datasource(self, metering_report_data, data_source, request):
        """Changes report data_source."""
        metering_report_data.data_source = data_source
        
        response = {}
        if metering_report_data.report.report_type.id == 6:
            comsumptions = self.__report_repository.prefetch_asset_comsumption([metering_report_data], metering_report_data.report.year, metering_report_data.report.month)

            self.__report_repository.calculate_asset_comsumption(metering_report_data, 
                metering_report_data.report.year, metering_report_data.report.month, data_source, comsumptions)
            consumption_values = metering_report_data.consumption_values.all()[0]
            consumption_values.ccee_consumption_value=getattr(metering_report_data, "ccee_consumption_value", None)
            consumption_values.vale_consumption_value=getattr(metering_report_data, "vale_consumption_value", None)
            consumption_values.off_peak_consumption_value=metering_report_data.projected_consumption_off_peak
            consumption_values.on_peak_consumption_value=metering_report_data.projected_consumption_on_peak
            consumption_values.loss=metering_report_data.loss_percentage
            consumption_values.total_consumption_loss=metering_report_data.total_consumption_loss
            consumption_values.save()
            
            response['data'] = DetailedConsumptionReportDataSerializerNew(metering_report_data).data
        metering_report_data.save()
        response['detail'] = 'info_changed_datasource'
        return response, 200

    def change_losstype(self, metering_report_data, loss_type, request):
        """Changes report loss_type."""
        metering_report_data.loss_type = '1' if 'type1' in loss_type else '2'
        metering_report_data.save(update_fields=['loss_type'])
        response = {}
        response['detail'] = 'info_changed_loss_type'
        return response, 200

class GenerateProjectedDetailedDataService:
    def __init__(self, repository):
        self.__repository = repository

    def generate_data(self, vale_gauge_list, associated_companies, month, year, filters):
        vale_gauge_tags = vale_gauge_list
        detailed_projected_data, status = self.__repository.get_detailed_projected_data(
            vale_gauge_tags, associated_companies, month, year, filters)
        return detailed_projected_data

    def get_last_project_consumption(self, month, year):
        return Report.objects.filter(report_type__initials__exact='RCP', month=month, year=year).latest('id')


#==============================================================================================
#==============================================================================================
#==============================================================================================
#==============================================================================================
class GenerateProjectedDetailedDataServiceNew:
    def __init__(self, repository):
        self.__repository = repository

    def generate_data(self, vale_gauge_list, associated_companies, month, year, filters):
        vale_gauge_tags = vale_gauge_list
        detailed_projected_data, status = self.__repository.get_detailed_projected_data(
            vale_gauge_tags, associated_companies, month, year, filters)
        return detailed_projected_data

    def get_last_project_consumption(self, month, year):
        return Report.objects.filter(report_type__initials__exact='RCP', month=month, year=year).latest('id')