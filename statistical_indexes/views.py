from company.models import Company
from pytz import timezone

import datetime
from rest_framework import viewsets
from django.db.models import F, CharField, DecimalField, Value
from django.db.models.functions import Cast, TruncSecond, Replace
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND, \
    HTTP_500_INTERNAL_SERVER_ERROR, HTTP_412_PRECONDITION_FAILED
from django.core.paginator import Paginator

from core.models import Log
from energy_composition.models import ApportiomentComposition
from .models import CompanyReference
from energy_composition.models import EnergyComposition
from core.serializers import LogSerializer
from .serializers import CompaniesSerializer, IndexesDataSerializer, CompanyReferenceSerializer
from SmartEnergy.handler_logging import HandlerLog
from SmartEnergy.auth import check_module
import SmartEnergy.auth.permissions as permissions
import SmartEnergy.auth.modules as modules

from .service import SAPService, StatisticalIndexService

# list of status
# 0 - Temporary
# 1 - Shipping: Sent to SAP
# 2 - Shipping: Shipping Complete
# 3 - Sending: Communication failure
# 4 - Shipping: Shipping Completed Manually
# 5 - Chargeback: Sent to SAP
# 6 - Chargeback: Submission Complete
# 7 - Chargeback: Communication failure
# 8 - Chargeback: Manually Completed Shipping
# 9 - Saved


class IndexesViewSet(viewsets.ModelViewSet):
    queryset = CompanyReference.objects.all()
    serializer_class = CompanyReferenceSerializer

    @check_module(modules.apportionment, [permissions.VIEW, permissions.EDITN1])
    def send_indexes_transaction(self, data):
        sap_service = SAPService()
        sap_response = sap_service.send_indexes_transaction(data)
        return sap_response

    @check_module(modules.apportionment, [permissions.EDITN1])
    def create(self, request, *args, **kwargs):
        temp_id = request.data.get("temp_id")

        # check if do not exists another index from the same company, type and date and create in database if doesn't exists
        try:
            index = CompanyReference.objects.get(pk=temp_id)
        except CompanyReference.DoesNotExist:
            return Response({"message": "error_index_not_found"}, status=HTTP_412_PRECONDITION_FAILED)
                
        if index.status not in ["0", "1", "9"]:
            return Response({"message": "error_index_already_exists"}, status=HTTP_412_PRECONDITION_FAILED)
        
        if index.transaction_type == 'A':
            volume_or_cost_sent_indexes = CompanyReference.objects.filter(
                id_company=index.id_company,
                transaction_type__in=['V', 'C'],
                month=index.month,
                year=index.year,
            ).exclude(
                status__in=["0", "5", "6", "7", "8", "9"]
            )
            sent_index = volume_or_cost_sent_indexes.first()
            index_type = 'volume' if index.transaction_type == 'V' else 'cost'
            if volume_or_cost_sent_indexes.exists():
                return Response({"message": f"error_{index_type}_index_sent", "args": [sent_index.index_name]},
                                status=HTTP_412_PRECONDITION_FAILED)

        statistical_index_service = StatisticalIndexService()
        response = statistical_index_service.send_index(request, index)
        return response

    @check_module(modules.apportionment, [permissions.VIEW, permissions.EDITN1])
    def retrieve(self, request, *args, **kwargs):
        value = request.query_params.get('value', '')
        unity = request.query_params.get('unit', '')
        statistic_index = request.query_params.get('statistic_index', '')
        cost_center = request.query_params.get('cost_center', '')
        instance = self.get_object()
        instance.results.filter(id__contains=statistic_index,
                                value__contains=value,
                                unity__contains=unity,
                                id_apport__id_energy_composition__cost_center__contains=cost_center)
        serializer = self.get_serializer(instance)
        response_data = serializer.data
        response_data.pop('company_name', None)
        return Response(response_data, HTTP_200_OK)

    @check_module(modules.apportionment, [permissions.VIEW, permissions.EDITN1])
    def get_queryset(self):
        current_datetime = datetime.datetime.now()
        creation_date = self.request.query_params.get('creation_date', '')
        user_timezone = self.request.query_params.get('user_timezone', 'America/Sao_Paulo')
        index_name = self.request.query_params.get('index_name', '')
        company_name = self.request.query_params.get('company_name', '')
        sap_document_number = self.request.query_params.get('sap_document_number', '')
        dispatch_status = self.request.query_params.get('dispatch_status', '')
        ordenation_field = self.request.query_params.get('ordering', '-creation_date')
        tzuser = timezone(user_timezone)

        queryset = self.queryset.exclude(status__exact="0").annotate(
                company_name=F('id_company__company_name'),
                dispatch_status=F('status'),
                creation_date_user_timezone=Cast(TruncSecond(F('creation_date'), tzinfo=tzuser), output_field=CharField()),
                creation_date_formated=Replace('creation_date_user_timezone', Value('.0000000'), Value(""))
            ).filter(
                company_name__contains=company_name,
                index_name__contains=index_name,
                status__contains=dispatch_status,
                creation_date_formated__contains=creation_date
            ).order_by(ordenation_field)
        if sap_document_number:
            queryset = queryset.filter(sap_document_number__contains=sap_document_number)
        elif sap_document_number != '':
            return queryset.none()
        return queryset

    @check_module(modules.apportionment, [permissions.VIEW, permissions.EDITN1])
    def list(self, request):
        if request.query_params.get('export_all', 'False') == 'True':
            response_data = self.get_queryset()
        else:
            paginator = Paginator(self.get_queryset(), request.query_params.get('page_size', 10))
            page = paginator.get_page(request.query_params.get('page', 1))
            response_data = page.object_list
        
        serialized_data = self.get_serializer(data=response_data, many=True)
        serialized_data.is_valid()
        response_data = serialized_data.validated_data
        
        return Response({'count': paginator.count, 
                         'next': None, 
                         'previous': None,
                         'results': serialized_data.data}, HTTP_200_OK)

    @check_module(modules.apportionment, [permissions.EDITN1])
    def update(self, request, *args, **kwargs):
        statistical_index_service = StatisticalIndexService()
        response = statistical_index_service.resend_index(self.get_object, self.get_serializer, request)
        return response



class IndexesDataViewSet(viewsets.ModelViewSet):
    queryset = EnergyComposition.objects.all()
    serializer_class = IndexesDataSerializer

    @check_module(modules.apportionment, [permissions.VIEW, permissions.EDITN1])
    def create(self, request, *args, **kwargs):
        statistical_index_service = StatisticalIndexService()

        company_id = self.request.data['params'].get('company_id')
        queryset = ApportiomentComposition.objects.select_related('id_company').filter(
            status='S',
            id_company__pk=company_id
        ).annotate(
            value=Value('0', output_field=DecimalField()),
            unit=Value('kWh', output_field=CharField()),
            associated_company=F('id_energy_composition__id_company__company_name')
        ).order_by('id_company__company_name')

        response = statistical_index_service.generate_data(queryset, self.request, self.get_success_headers)
        return response
        

class CompaniesViewSet(viewsets.ReadOnlyModelViewSet):
    DEACTIVATED = ['0', 'n', 'N']
    INTERNAL = 'I'
    SUBSIDIARY = 'F'

    queryset = Company.objects.all().exclude(
            status__in=DEACTIVATED
        ).filter(
            type__in=[INTERNAL, SUBSIDIARY]
        ).order_by('company_name')
    serializer_class = CompaniesSerializer


class ReverseIndexViewSet(viewsets.ModelViewSet):
    queryset = CompanyReference.objects.all()
    serializer_class = CompanyReferenceSerializer

    @check_module(modules.apportionment, [permissions.EDITN1])
    def update(self, request, *args, **kwargs):
        statistical_index_service = StatisticalIndexService()
        response = statistical_index_service.reverse_index(self.get_object, self.get_serializer, request)
        return response


class SaveIndexViewSet(viewsets.ModelViewSet):
    queryset = CompanyReference.objects.all()
    http_method_names = ['put']
    serializer_class = CompanyReferenceSerializer

    @check_module(modules.apportionment, [permissions.EDITN1])
    def update(self, request, *args, **kwargs):
        statistical_index_service = StatisticalIndexService()
        response = statistical_index_service.save_index(self.get_object, self.get_serializer, request)
        return response


class HistoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Log.objects.all()
    serializer_class = LogSerializer
    
    @check_module(modules.apportionment, [permissions.VIEW, permissions.EDITN1])
    def list(self):
        return Response({"message": "please provide an instance"}, status=HTTP_400_BAD_REQUEST)

    @check_module(modules.apportionment, [permissions.VIEW, permissions.EDITN1])
    def retrieve(self, request, *args, **kwargs):
        company_reference = CompanyReference.objects.get(pk=kwargs.get('pk'))
        queryset = self.queryset.filter(table_name='COMPANY_REFERENCE', field_pk=company_reference.id).order_by('date')

        paginator = Paginator(queryset, request.query_params.get('page_size', 10))
        page = paginator.get_page(request.query_params.get('page', 1))
        response_data = page.object_list
        
        serializer = self.get_serializer(data=response_data, many=True)
        serializer.is_valid()
        
        return Response(serializer.data, HTTP_200_OK)


class ShowIndexesViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CompanyReference.objects.all()
    serializer_class = CompanyReferenceSerializer
    logger = HandlerLog()

    @check_module(modules.apportionment, [permissions.VIEW, permissions.EDITN1])
    def get_statistical_indexes_filtered_ordered(self, indexes_dict):
        statistical_index_service = StatisticalIndexService()
        indexes_dict = statistical_index_service.get_statistical_indexes_filtered_ordered(indexes_dict, self.request)
        return indexes_dict
    
    @check_module(modules.apportionment, [permissions.VIEW, permissions.EDITN1])
    def list(self, request, *args, **kwargs):
        id = request.query_params.get('id', None)
        if id is None:
            return Response({"description: error_instance_not_found"}, status=HTTP_400_BAD_REQUEST)

        queryset = self.queryset.filter(id__exact=id)

        if not queryset:
            return Response({"description: error_instance_not_found"}, status=HTTP_400_BAD_REQUEST)
        
        serialized_data = self.serializer_class(data=queryset, many=True)
        serialized_data.is_valid()
        paginated_data = serialized_data.data[0]
        indexes_dict = paginated_data['results']
        
        results = self.get_statistical_indexes_from_sap(indexes_dict)

        if(len(results) == 0):
            results = self.get_statistical_indexes_filtered_ordered(indexes_dict)

        if request.query_params.get('export_all', 'False') == 'True':
            paginated_data['results'] = results
            return Response(paginated_data, HTTP_200_OK)

        paginator = Paginator(results, request.query_params.get('page_size', 10))
        page = paginator.get_page(request.query_params.get('page', 1))
        response_data = page.object_list

        paginated_data['count'] = paginator.count
        paginated_data['next'] = None
        paginated_data['previous'] = None
        paginated_data['results'] = response_data
        
        return Response(paginated_data, HTTP_200_OK)
    
    @check_module(modules.apportionment, [permissions.VIEW, permissions.EDITN1])
    def get_statistical_indexes_from_sap(self, indexes_dict):
        sap_service = SAPService()
        sap_response = sap_service.get_statistical_indexes_from_sap(indexes_dict, self.logger)
        return sap_response
        

class SAPViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Company.objects.none()
    serializer_class = CompaniesSerializer

    @check_module(modules.apportionment, [permissions.VIEW, permissions.EDITN1])
    def list(self, request, *args, **kwargs):
        return Response({"message": "error_sap_communication"}, status=HTTP_404_NOT_FOUND)


class IndexesScheduleDataViewSet(viewsets.ModelViewSet):
    queryset = EnergyComposition.objects.all()
    serializer_class = IndexesDataSerializer
    logger = HandlerLog()

    #@check_module(modules.apportionment, [permissions.VIEW, permissions.EDITN1])
    def create(self, request, *args, **kwargs):
        try:
            statistical_index_service = StatisticalIndexService()
            statistical_index_service.generate_and_sender_statistical_indexes(request, self.get_success_headers)
            detail = f'INFO :: Job successfully.'
            self.logger.info(detail)
            return Response({"detail": detail}, status=HTTP_200_OK)

        except Exception as e:
            detail = f'INFO: Job Generate_Statistical_Indexes was failed. {str(e)}'
            self.logger.error(detail)
            return Response({"detail": detail}, status=HTTP_412_PRECONDITION_FAILED)


@api_view(['POST'])
#@check_module(modules.apportionment, [permissions.EDITN1])
def update_flat_rate_apportionment(request):
    logger = HandlerLog()
    try:
        statistical_index_service = StatisticalIndexService()
        statistical_index_service.update_flat_rate_apportionment()
        detail = f'INFO :: Job successfully.'
        logger.info(detail)
        return Response({"detail": detail}, status=HTTP_200_OK)
    except Exception as e:
        detail = f'INFO: Job Update_flat_rate_apportonment was failed. {str(e)}'
        logger.error(detail)
        return Response({"detail": detail}, status=HTTP_412_PRECONDITION_FAILED)
