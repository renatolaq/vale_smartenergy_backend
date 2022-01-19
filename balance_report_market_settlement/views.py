from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_412_PRECONDITION_FAILED, \
    HTTP_500_INTERNAL_SERVER_ERROR, HTTP_201_CREATED
from rest_framework.filters import OrderingFilter
from rest_framework.decorators import api_view, authentication_classes
from datetime import timezone
from pytz import timezone
from django.db.models import Q, F, CharField, Value
from django.db.models.functions import Cast, TruncSecond, Replace
from .serializers import ReportsSerializerGet, HistoryBalancesSerializer, LastBalancesSerializer, \
    ReportsSerializer, BalanceFieldsSerializer, DetailedConsumptionReferenceSerializer, SortProfileSerializer
from .models import Report, HistoryBalance, BalanceFields, CliqContract
from .utils import Paginator, get_user_username, is_before_or_equal_nth_brazilian_workday
from .service import BalanceService
from .cache_balance import CacheBalance
from .exceptions import *
from SmartEnergy.auth import check_permission, check_module
from SmartEnergy.handler_logging import HandlerLog
import SmartEnergy.auth.permissions as permissions
import SmartEnergy.auth.modules as modules
from SmartEnergy.auth.IAM import IAMAuthentication


WORKDAY_LIMIT = 8
logger = HandlerLog()
  

class CliqContractsViewSet(viewsets.ReadOnlyModelViewSet):
    """Returns a list of Cliq Contracts"""
    queryset = CliqContract.objects.all()
    serializer_class = SortProfileSerializer
    balance_service = BalanceService()

    @check_module(modules.balance, [permissions.EDITN1])
    def get_queryset(self):
        month = int(self.request.query_params.get('month', None))
        year = int(self.request.query_params.get('year', None))
        if (month is None) or (year is None):
            raise PreconditionFailed(detail='error_month_and_year_required')
        return self.balance_service.get_cliq_contracts(month, year)

    @check_module(modules.balance, [permissions.EDITN1])
    def list(self, request):
        try:
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data, HTTP_200_OK)
        except EmptySeasonality as error:
            return Response({"detail": "error_empty_seasonality",
                             "args": [error.args[0]['contract_name']]}, status=HTTP_412_PRECONDITION_FAILED)
        except NoTransferContractPriorization as error:
            return Response({"detail": "error_no_transfer_constract_priorization",
                            "args": [error.args[0]['contract_name']]}, status=HTTP_412_PRECONDITION_FAILED)
        except NoFlexibilityLimit as error:
            return Response({"detail": "error_no_flexibility_limits",
                             "args": [error.args[0]['contract_name']]}, status=HTTP_412_PRECONDITION_FAILED)


class HistoryBalancesViewSet(viewsets.ReadOnlyModelViewSet):
    """Returns a list of history balances for month and year"""
    queryset = HistoryBalance.objects.filter(id_report__report_type__initials__exact='BDE')
    serializer_class = HistoryBalancesSerializer

    @check_module(modules.balance, [permissions.VIEW, permissions.EDITN1])
    def get_queryset(self):
        month = self.request.query_params.get('month', None)
        year = self.request.query_params.get('year', None)
        if month is None or year is None:
            raise PreconditionFailed
        query_filter = Q(id_report__month__icontains=month) & Q(id_report__year__icontains=year)
        return self.queryset.filter(query_filter).order_by('-create_date')
        

class LastBalancesViewSet(viewsets.ReadOnlyModelViewSet):
    """Returns a list of the last saved balances of each month"""
    queryset = Report.objects.filter(report_type__initials__exact='BDE', status__in=['S', 'C'])
    serializer_class = LastBalancesSerializer
    pagination_class = Paginator
    filter_backends = [OrderingFilter]
    ordering_fields = '__all__'
    
    @check_module(modules.balance, [permissions.VIEW, permissions.EDITN1])
    def get_queryset(self):
        params = self.request.query_params
        user_timezone = timezone(params.get('user_timezone', 'America/Sao_Paulo'))

        native = """
        SELECT ID_REPORT
        FROM   report_table 
        WHERE  id_report IN (SELECT Max(RT.id_report) AS ID_REPORT 
                     FROM   report_table RT 
                            INNER JOIN report_type TP 
                                    ON RT.id_report_type = TP.id_report_type 
                     WHERE  TP.report_initials = 'BDE' AND RT.status in ('S', 'C')
                     GROUP  BY RT.year, 
                               RT.month) 
        """
        id_select = Report.objects.raw(native)
        id_list = [obj.id for obj in id_select]
        return self.queryset.filter(
                id__in=id_list, 
                status__in=['S', 'C']
            ).annotate(
                reference_report_name=F('id_reference__report_name'),
                creation_date_user_timezone=Cast(TruncSecond(F('creation_date'), tzinfo=user_timezone), output_field=CharField()),
                creation_date_formated=Replace('creation_date_user_timezone', Value('.0000000'), Value(""))
            ).filter(
                report_name__contains=params.get('report_name', ''),
                reference_report_name__contains=params.get('reference_report_name', ''),
                creation_date_formated__contains=params.get('creation_date', ''),
                status__contains=params.get('status', '')
            ).order_by(params.get('ordering', '-id'))


class LastBalanceFieldsViewSet(viewsets.ReadOnlyModelViewSet):
    """Returns the contents of the BALANCE_FIELDS table that belongs to the latest saved Balance or an default
    object if the table is empty"""
    queryset = BalanceFields.objects.all()
    serializer_class = BalanceFieldsSerializer
    balance_service = BalanceService()

    @check_module(modules.balance, [permissions.EDITN1])
    def list(self, request):
        return self.balance_service.get_last_balance_fields()


@api_view(['PUT'])
@check_module(modules.balance, [permissions.EDITN1])
def consolidate_balance(request, pk):
    """Consolidate a balance given it's id, before consolidating it checks if this balance is
    the last one of the month and if there is another consolidated balance for that month"""
    balance = Report.objects.filter(report_type__initials__exact='BDE').get(id=pk)
    balance_service = BalanceService()

    try:
        if((int(balance.year)+1)%12 > 0):
            if not is_before_or_equal_nth_brazilian_workday(int(balance.year) + 1, 1, WORKDAY_LIMIT):
                return Response({"detail": 'error_save_past_workday_limit'}, status=HTTP_412_PRECONDITION_FAILED)
        else:
            if not is_before_or_equal_nth_brazilian_workday(int(balance.year), int(balance.month) + 1, WORKDAY_LIMIT):
                return Response({"detail": 'error_consolidate_past_workday_limit'}, status=HTTP_412_PRECONDITION_FAILED)

        consolidated_balance = balance_service.consolidate_balance(pk, get_user_username(request))
    except Report.DoesNotExist:
        return Response({"detail": 'error_balance_doesnt_exist'}, status=HTTP_400_BAD_REQUEST)
    except OutOfDate:
        return Response({"detail": 'error_isnt_most_updated_balance',
                         "args": [balance.report_name]}, status=HTTP_412_PRECONDITION_FAILED)
    except AlreadyConsolidated:
        return Response({"detail": 'error_already_consolidated',
                         "args": [balance.report_name]}, status=HTTP_412_PRECONDITION_FAILED)
    except PastDateLimit:
        return Response({"detail": 'error_cant_consolidate_error_past_workday_limit',
                        "args": [balance.report_name]}, status=HTTP_412_PRECONDITION_FAILED)
    except Exception as e:
        return Response({"detail": 'error_something_went_wong_status',
                         "args": [balance.report_name]}, status=HTTP_400_BAD_REQUEST)
    return Response(ReportsSerializer(consolidated_balance).data, status=HTTP_200_OK)


class GetBalanceViewSet(viewsets.ReadOnlyModelViewSet):
    """Returns a balance for identifier"""
    queryset = Report.objects.filter(report_type__initials__exact='BDE')
    serializer_class = ReportsSerializerGet

    @check_module(modules.balance, [permissions.VIEW, permissions.EDITN1])
    def list(self, request):
        balance_service = BalanceService()
        id = self.request.query_params.get('id', None)

        if id is None:
            raise PreconditionFailed
        try:
            response_data = balance_service.get_saved_balance(id)

            self.request.query_params._mutable = True
            self.request.query_params['month'] = response_data.month
            self.request.query_params['year'] = response_data.year
            self.request.query_params['validate_contract'] = False          
            self.request.query_params._mutable = False
        except PreconditionFailed:
            raise PreconditionFailed
        except Report.DoesNotExist:
            raise NotFound

        serializer = self.get_serializer(response_data)
        return Response(serializer.data)

class DetailedConsumptionReferenceViewSet(viewsets.ReadOnlyModelViewSet):
    """Returns a list of Detailed Consumption Report (id and name) for month and year"""
    queryset = Report.objects.filter(report_type__initials__exact='RPD', status='S').order_by('-creation_date')
    serializer_class = DetailedConsumptionReferenceSerializer

    @check_module(modules.balance, [permissions.EDITN1])
    def get_queryset(self):
        month = self.request.query_params.get('month', None)
        year = self.request.query_params.get('year', None)

        if month is None or year is None:
            raise PreconditionFailed
        
        query_filter = Q(month=month) & Q(year=year)
        return self.queryset.filter(query_filter)


@api_view(['POST'])
@check_module(modules.balance, [permissions.EDITN1])
def save_balance(request):
    try:
        if((int(request.data['year'])+1)%12 > 0):
            if not is_before_or_equal_nth_brazilian_workday(int(request.data['year']) + 1, 1, WORKDAY_LIMIT):
                return Response({"detail": 'error_save_past_workday_limit'}, status=HTTP_412_PRECONDITION_FAILED)
        else:
            if not is_before_or_equal_nth_brazilian_workday(int(request.data['year']), int(request.data['month']) + 1, WORKDAY_LIMIT):
                return Response({"detail": 'error_save_past_workday_limit'}, status=HTTP_412_PRECONDITION_FAILED)

        balance_service = BalanceService()
        if request.data is None or request.data == {}:
            return Response({"detail": 'error_invalid_body_format_balance'}, status=HTTP_412_PRECONDITION_FAILED)

        balance = Report.objects.filter(report_type__initials__exact='BDE').get(id=request.data['id'])
        if not balance_service.report_check_modification_by_request(request, balance):
            return Response({"detail": 'error_report_was_modified'}, status=HTTP_412_PRECONDITION_FAILED)

        balance_service.save_balance(balance, get_user_username(request))

    except AlreadySaved:
        return Response({"detail": 'error_already_saved_balance',
                         "args": [f"{request.data['report_name']}"]}, status=HTTP_412_PRECONDITION_FAILED)
    except PastDateLimit:
        return Response({"detail": 'error_cant_save_balance',
                         "args": [f"{request.data['report_name']}"]}, status=HTTP_412_PRECONDITION_FAILED)
    except Report.DoesNotExist:
        return Response({"detail": 'error_report_not_found',
                         "args": [f"{request.data['id']}"]}, status=HTTP_412_PRECONDITION_FAILED)
    except Exception as e:
        logger.error(f'{str(e)}')
        return Response({"detail": 'error_something_went_wrong_balance'}, status=HTTP_500_INTERNAL_SERVER_ERROR)
    return Response(ReportsSerializer(balance).data, status=HTTP_201_CREATED)


@api_view(['POST'])
@check_module(modules.balance, [permissions.EDITN1])
def generate_balance(request):
    balance_service = BalanceService()

    try:
        balance_service.clear_temporary_balance()
        new_balance_report = balance_service.generate_balance(request.data)
        return Response(serializer_test(new_balance_report), status=HTTP_201_CREATED)
    except NoGenerationSeasonality as error:
        return Response({"detail": 'error_no_generation_seasonality',
                         "args": [f"{error.args[0]['generating_unit']}"]}, status=HTTP_412_PRECONDITION_FAILED)
    except NoGenerationLoss as error:
        return Response({"detail": 'error_no_generation_losses',
                         "args": [f"{error.args[0]['generating_unit']}"]}, status=HTTP_412_PRECONDITION_FAILED)
    except InvalidContract as error:
        return Response({"detail": f"{error.args[0]['translation_key']}",
                         "args": [f"{error.args[0]['contract_name']}"]}, status=HTTP_412_PRECONDITION_FAILED)
    except Exception as e:
        logger.error(f'{str(e)}')
        return Response({"detail": 'error_something_went_wrong_balance'}, status=HTTP_500_INTERNAL_SERVER_ERROR)

def serializer_test(new_balance_report):
    return ReportsSerializer(Report.objects.get(id=new_balance_report.id)).data

@api_view(['POST'])
@authentication_classes([IAMAuthentication])
@check_module(modules.balance, [permissions.EDITN1])
def schedule_save_balance(request):
    """ Generates, saves and saves balance on the eighth business day of the month. """
    try:
        balance_service = BalanceService()
        balance_service.schedule_save_balance()
        detail = f'INFO :: Job successfully.'
        logger.info(detail)
        return Response({"detail": detail}, status=HTTP_200_OK)
    except Exception as e:
        detail = f'INFO: Job Generate_Balance was failed. {str(e)}'
        logger.error(detail)
        return Response({"detail": detail}, status=HTTP_412_PRECONDITION_FAILED)


@api_view(['POST'])
@check_module(modules.balance, [permissions.EDITN1])
def load_cache(request):
    """" Loads the data to generate the balance in the cache. """
    try:
        cache_balance = CacheBalance.get_instance()
        cache_balance.month = request.query_params.get('month', None)
        cache_balance.year = request.query_params.get('year', None)
        cache_balance.id_rcd = request.query_params.get('id_rcd', None)
        cache_balance.load_data()
        return Response({"detail": "Load cache started."}, status=HTTP_200_OK)
    except Exception as e:
        return Response({"detail": e}, status=HTTP_500_INTERNAL_SERVER_ERROR)
