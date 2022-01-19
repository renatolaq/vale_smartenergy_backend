from django.db.models import Count, Q, F, Max, FloatField, DecimalField, CharField, When, Case, Sum, Value, \
    ExpressionWrapper, Avg
from rest_framework.response import Response
from django.db.models.functions import Cast, TruncSecond, Replace, Coalesce
from django.utils.timezone import now
from datetime import datetime, timedelta
from .models import Report, MeteringReportData, MeteringReportValue, GaugePoint, Assets, GaugeData, Company
from .utils import get_peak_time, replace_comma_with_dot, StrSQL, AbsSQL, GrossConsumptionExpressionBuilder, \
    Paginator, ValidationError, get_user_username, get_local_timezone
from .serializers import LogSerializer, SavedReportSerializer
from .exceptions import PreconditionFailed
from rest_framework.filters import OrderingFilter
from django.db import transaction
from decimal import Decimal
from pytz import timezone
import re, json
from collections import namedtuple
from SmartEnergy.handler_logging import HandlerLog

logger = HandlerLog()

def log_report(action_type, observation):
    """Decorator responsible for recording the reports logs"""
    def formatted_report(report):
        return SavedReportSerializer(report).data if report else None

    def decorator(function):
        def wrapper(*args, **kwargs):
            _, params, request, pk, *_ =  list(args)+[None, None]
            old_value = Report.objects.filter(pk=pk).first() if pk else None
            observation_log = params.get('observation_log', observation)            
            result = function(*args, **kwargs)
            if result:
                new_value = formatted_report(result)
                old_value = formatted_report(old_value)
                new_log = LogSerializer(data={
                            'field_pk':result.pk, 
                            'table_name':'REPORT_TABLE', 
                            'action_type':action_type, 
                            'new_value':str(new_value), 
                            'old_value':str(old_value), 
                            'observation':observation_log, 
                            'date':now(), 
                            'user': get_user_username(request)
                        }, many=False)
                
                if new_log.is_valid(True):
                    new_log.save()
            return result
        return wrapper
    return decorator

def clear_temporary_reports():
    """Clears temporary Reports."""
    try:
        report_type_list = ['RCB', 'RCP', 'RCD', 'RPD']
        time_delta = 1
        datetime_now = datetime.now(get_local_timezone())
        temporary_reports = Report.objects.filter(
            report_type__initials__in=report_type_list,
            status='T',
            creation_date__lte=(datetime_now - timedelta(hours=time_delta))
            )
        count = len(temporary_reports)

        if count > 0:
            try:
                temporary_reports.delete()
            except Exception as e:
                detail = f'ERROR: Job clear_temporary_reports failed: {str(e)}'
                logger.error(detail)
        detail = f'[{count}] temporary reports were removed.'
        logger.info(detail)
    except Exception as e:
        detail = f'ERROR: clear_temporary_reports failed: {str(e)}'
        logger.error(detail)


class ReportRepository:
    param_filters = {'report_name': 'report_name__contains', 'status': 'status', 'creation_date': 'creation_date__date', 'referenced_report_name': 'id_reference__report_name__startswith'}

    def check_if_already_saved(self, report):
        """"Checks whether a given report is already saved"""
        saved_reports = self.check_any_other_exists(report)
        if not saved_reports:
            return False

        for saved_report in saved_reports:
            saved_metering_report_value = MeteringReportValue.objects.filter(
                metering_report_data__report__id=saved_report.id
            )
            metering_report_values = MeteringReportValue.objects.filter(
                metering_report_data__report__id=report.id
            )

            if not self.check_same_length_metering_values(saved_metering_report_value, metering_report_values):
                continue

            if not self.check_same_sum_values(saved_metering_report_value, metering_report_values):
                continue

            if self.check_each_metering_value(saved_metering_report_value, metering_report_values):
                return True

        return False

    def check_any_other_exists(self, report):
        """"Checks if any other report exists"""
        active = ['S', 's']
        saved_reports = Report.objects.filter(
            report_type__initials=report.report_type.initials,
            status__in=active,
            year=report.year,
            month=report.month
        )
        if not saved_reports:
            return False
        return saved_reports

    def check_same_length_metering_values(self, saved_metering_report_value, metering_report_value):
        """"Checks if both metering values lists are the same length"""
        return len(saved_metering_report_value) is len(metering_report_value)

    def sum_metering_report_values(self, metering_report_values):
        metering_report_value_sum = namedtuple(
            'MeteringReportValueSums',
            [
                'off_peak_consumption_value',
                'on_peak_consumption_value',
                'ccee_consumption_value',
                'ccee_metering_days',
                'vale_consumption_value',
                'vale_metering_days',
                'loss',
                'total_consumption_loss'
            ]
        )
        metering_report_value_sum.off_peak_consumption_value = metering_report_values.aggregate(
            Sum('off_peak_consumption_value')
        )['off_peak_consumption_value__sum'] or 0.0
        metering_report_value_sum.on_peak_consumption_value = metering_report_values.aggregate(
            Sum('on_peak_consumption_value')
        )['on_peak_consumption_value__sum'] or 0.0
        metering_report_value_sum.ccee_consumption_value = metering_report_values.aggregate(
            Sum('ccee_consumption_value')
        )['ccee_consumption_value__sum'] or 0.0
        metering_report_value_sum.ccee_metering_days = metering_report_values.aggregate(
            Sum('ccee_metering_days')
        )['ccee_metering_days__sum'] or 0.0
        metering_report_value_sum.vale_consumption_value = metering_report_values.aggregate(
            Sum('vale_consumption_value')
        )['vale_consumption_value__sum'] or 0.0
        metering_report_value_sum.vale_metering_days = metering_report_values.aggregate(
            Sum('vale_metering_days')
        )['vale_metering_days__sum'] or 0.0
        metering_report_value_sum.loss = metering_report_values.aggregate(
            Sum('loss')
        )['loss__sum'] or 0.0
        metering_report_value_sum.total_consumption_loss = metering_report_values.aggregate(
            Sum('total_consumption_loss')
        )['total_consumption_loss__sum'] or 0.0
        return metering_report_value_sum

    def check_same_sum_values(self, saved_metering_report_value, metering_report_values):
        values_sum = self.sum_metering_report_values(metering_report_values)
        saved_values_sum = self.sum_metering_report_values(saved_metering_report_value)
        for key in values_sum._fields:
            if getattr(values_sum, key) != getattr(saved_values_sum, key):
                return False
        return True

    def check_each_metering_value(self, saved_metering_report_value, metering_report_values):
        """"Check if each metering report value is the same"""
        for new_value in metering_report_values:
            saved_founded = saved_metering_report_value.filter(
                off_peak_consumption_value=new_value.off_peak_consumption_value,
                on_peak_consumption_value=new_value.on_peak_consumption_value,
                ccee_consumption_value=new_value.ccee_consumption_value,
                ccee_metering_days=new_value.ccee_metering_days,
                vale_consumption_value=new_value.vale_consumption_value,
                vale_metering_days=new_value.vale_metering_days,
                loss=new_value.loss,
                total_consumption_loss=new_value.total_consumption_loss,
                metering_report_data__id_company=new_value.metering_report_data.id_company,
                metering_report_data__ccee_code=new_value.metering_report_data.ccee_code,
                metering_report_data__gauge_tag=new_value.metering_report_data.gauge_tag,
                metering_report_data__associated_company=new_value.metering_report_data.associated_company,
                metering_report_data__director_board=new_value.metering_report_data.director_board,
                metering_report_data__business=new_value.metering_report_data.business,
                metering_report_data__data_source=new_value.metering_report_data.data_source,
                metering_report_data__loss_type=new_value.metering_report_data.loss_type
            )
            if not saved_founded:
                return False
        return True

    def build_metering_report_data(self, saved_report, ccee_code, gauge_tag, associated_company, id_company, data_source, director_board, business, loss_type, id_assets=None, id_asset_items=None, updated_consumption=None):
        return MeteringReportData.objects.create(
                report=saved_report,
                ccee_code=ccee_code,
                gauge_tag=gauge_tag,
                associated_company=associated_company,
                id_company=id_company,
                data_source=data_source,
                director_board=director_board,
                business=business,
                loss_type=loss_type,
                id_assets_id=id_assets,
                id_asset_items_id=id_asset_items,
                updated_consumption=updated_consumption
            )

    def build_metering_report_value(self, report_data, ccee_metering_days, ccee_consumption, vale_metering_days, vale_consumption, off_peak_consumption_value, on_peak_consumption_value, loss, total_consumption_loss):
        return MeteringReportValue(
            metering_report_data=report_data,
            ccee_metering_days=ccee_metering_days,
            ccee_consumption_value=ccee_consumption,
            vale_metering_days=vale_metering_days,
            vale_consumption_value=vale_consumption,
            off_peak_consumption_value=off_peak_consumption_value,
            on_peak_consumption_value=on_peak_consumption_value,
            loss=loss,
            total_consumption_loss=total_consumption_loss
        )

    def createReportName(self, initials, month, year):
        """Create the report name"""
        existing_reports = Report.objects.filter(month=month, year=year, report_type__initials=initials, status__in=['s', 'S', 'n', 'N']).count()
        sequential = 0
        if existing_reports != 999:
            sequential = 1 + existing_reports
        return f'{initials}_{str(month).zfill(2)}_{str(year).zfill(4)}_{str(sequential).zfill(3)}'

    def build_data(self, params, request):
        generated_data, metering_report_datas, referenced_report = None, None, None
        if self.report_type_id == 3:
            generated_data, metering_report_datas, referenced_report = self.generate_data(params.get('referenced_report_id', None),params.get('list'), params.get('year'), params.get('month'), request)
        elif self.report_type_id == 6:
            generated_data, referenced_report = self.generate_data(params.get('year'), params.get('month'), request)
        else:
           generated_data = self.generate_data(params['year'], params['month'])

        if len(generated_data) == 0 and (self.report_type_id == 3 or self.report_type_id == 6):
            raise Assets.DoesNotExist('error_no_data_gross_report')

        if len(generated_data) == 0 and (self.report_type_id != 3 or self.report_type_id == 6):
            raise GaugePoint.DoesNotExist('error_no_data_for_time_period')
        return generated_data, metering_report_datas, referenced_report

    def get_queryset(self, params, pk):
        return None

    def get(self, request, pk):
        ordering_filter = OrderingFilter()
        paginator = Paginator()
        ordering_filter.ordering_fields = '__all__'
        params = {key: value.replace('.', '').replace(',', '.') for key, value in request.query_params.items()}
        queryset = self.get_queryset(params, pk)
        paginator.paginate_queryset(ordering_filter.filter_queryset(request, queryset, ''), request)
        return {
                    'count': paginator.page.paginator.count,
                    'next': paginator.get_next_link(),
                    'previous': paginator.get_previous_link(),
                    'report_name': paginator.page.object_list[0].report_name,
                    'referenced_report_name':paginator.page.object_list[0].referenced_report_name,
                    'month': paginator.page.object_list[0].referencing_month,
                    'year': paginator.page.object_list[0].referencing_year,
                    'limit_ccee_vale': paginator.page.object_list[0].limit_value,
                    'results': paginator.page.object_list
                }

    @log_report(action_type='CREATE', observation='Create Report.')
    def create(self, params, request):
        """Creates a report record"""
        generated_data, metering_report_datas, referenced_report = self.build_data(params, request)
        with transaction.atomic():
            status = 'T'

            if  self.report_type_id == 2:
                limit_value = params.get('limit_value', '0')
            elif self.report_type_id == 6:
                limit_value = params.get('limit_value', '0')
                if params.get('referenced_report_id', None):
                    status = 'S'                
                    reference = Report.objects.get(id=params.get('referenced_report_id'))
                    reference.status='N'
                    reference.save()
            else:
                limit_value = None

            saved_report = Report.objects.create(
                id_reference=referenced_report,
                report_type_id=self.report_type_id,
                report_name=params['report_name'],
                creation_date=params['creation_date'],
                status=status,
                month=params['month'],
                year=params['year'],
                limit_value=limit_value
            )
            metering_report_data_list = []            

            if self.report_type_id == 3:
                for data in generated_data:
                    if data.show_balance == 'Asset items':
                        metering_report_data_id_list = metering_report_datas.filter(id_company=data.id_company_asset_item).values_list('id', flat=True)
                        company = Company.objects.get(id_company=data.id_company_asset_item)
                        metering_report_value = MeteringReportValue.objects.filter(metering_report_data__id__in=metering_report_data_id_list)
                        average_metering_days = metering_report_value.aggregate(ccee=Avg('ccee_metering_days'), vale=Avg('vale_metering_days'))
                        report_data = self.build_metering_report_data(saved_report, None, None, data.consumer, company, None, data.director_board, data.business, data.loss_type)
                        built_data_report = self.build_metering_report_value(report_data, average_metering_days['ccee'], data.ccee_consumption_value, average_metering_days['vale'], data.vale_consumption_value, data.projected_consumption_off_peak, data.projected_consumption_on_peak, data.loss_percentage, data.total_consumption_loss)
                    else:
                        asset_item_company_ids = data.asset_items.all().values_list('id_company', flat=True)
                        metering_report_data_id_list = metering_report_datas.filter(id_company_id__in=asset_item_company_ids).values_list('id', flat=True)
                        metering_report_value = MeteringReportValue.objects.filter(metering_report_data__id__in=metering_report_data_id_list)
                        average_metering_days = metering_report_value.aggregate(ccee=Avg('ccee_metering_days'), vale=Avg('vale_metering_days'))
                        report_data = self.build_metering_report_data(saved_report, None, None, data.consumer, data.id_company, None, data.director_board, data.business, data.loss_type)
                        built_data_report = self.build_metering_report_value(report_data, average_metering_days['ccee'], data.ccee_consumption_value, average_metering_days['vale'], data.vale_consumption_value, data.projected_consumption_off_peak, data.projected_consumption_on_peak, data.loss_percentage, data.total_consumption_loss)
                    report_data.consumption_values.add(built_data_report, bulk=False)
                    metering_report_data_list.append(report_data)
            elif self.report_type_id == 6:
                for data in generated_data:
                    if isinstance(data, MeteringReportData):
                        data: MeteringReportData = data
                        value:MeteringReportValue = data.consumption_values.all()[0]
                        report_data = self.build_metering_report_data(saved_report, data.ccee_code, data.gauge_tag, data.associated_company, data.id_company, 
                            data.data_source, data.director_board, data.business, data.loss_type, data.id_assets_id, data.id_asset_items_id, False)
                        built_data_report = self.build_metering_report_value(report_data, value.ccee_metering_days, 
                            value.ccee_consumption_value, value.vale_metering_days, value.vale_consumption_value, value.off_peak_consumption_value, 
                            value.on_peak_consumption_value, value.loss, value.total_consumption_loss)                                
                    elif data.show_balance == 'Asset items':
                        company = Company.objects.get(id_company=data.id_company_asset_item)
                        report_data = self.build_metering_report_data(saved_report, None, None, data.consumer, company, 
                            data.data_source, data.director_board, data.business, data.loss_type, data.id_assets if data.id_asset_items is None else None, data.id_asset_items, referenced_report is not None)
                        built_data_report = self.build_metering_report_value(report_data, data.ccee_metering_days, data.ccee_consumption_value, data.vale_metering_days, data.vale_consumption_value, data.projected_consumption_off_peak, data.projected_consumption_on_peak, data.loss_percentage, data.total_consumption_loss)
                    else:
                        report_data = self.build_metering_report_data(saved_report, None, None, data.consumer, data.id_company, data.data_source, 
                            data.director_board, data.business, data.loss_type, data.id_assets if data.id_asset_items is None else None, data.id_asset_items, referenced_report is not None)
                        built_data_report = self.build_metering_report_value(report_data, data.ccee_metering_days, data.ccee_consumption_value, data.vale_metering_days, data.vale_consumption_value, data.projected_consumption_off_peak, data.projected_consumption_on_peak, data.loss_percentage, data.total_consumption_loss)
                    
                    report_data.consumption_values.add(built_data_report, bulk=False)
                    metering_report_data_list.append(report_data)
            else:
                for data in generated_data:
                    report_data =  self.build_metering_report_data(saved_report, data.ccee_code, data.gauge_tag, data.associated_company, data.id_company, params['data_source'].get(data.gauge_tag, 'CCEE'), None, None, None)
                    built_data_report = self.build_metering_report_value(report_data, data.ccee_metering_days, data.ccee_consumption, data.vale_metering_days, data.vale_consumption, None, None, None, None)
                    report_data.consumption_values.add(built_data_report, bulk=False)
                    metering_report_data_list.append(report_data)
            saved_report.metering_report_data.set(metering_report_data_list, bulk=False)

        return saved_report

    def list(self, request):
        """Lists saved reports according to passed parameters."""
        ordering_filter = OrderingFilter()
        paginator = Paginator()
        ordering_filter.ordering_fields = '__all__'

        params_filtered = {self.param_filters[key]: value for key, value in request.query_params.items() if key in self.param_filters and value}

        creation_date = params_filtered.get('creation_date__date', '')
        user_timezone = params_filtered.get('user_timezone', 'America/Sao_Paulo')
        status = params_filtered.get('status', '')
        report_name = params_filtered.get('report_name__contains', '')
        id_reference__report_name__startswith = params_filtered.get('id_reference__report_name__startswith', '')

        tzuser = timezone(user_timezone)

        basic_filter = (Q(report_type__initials=self.report_type))
        basic_filter.add(Q(status__in=['S', 'N']), Q.AND)

        queryset = Report.objects.filter(basic_filter).values('id', 'report_name', 'creation_date', 'status', 'month', 'year').annotate(
            referenced_report_name=F('id_reference__report_name'),
            creation_date_user_timezone=Cast(TruncSecond(F('creation_date'), tzinfo=tzuser), output_field=CharField()),
            creation_date_formated=Replace('creation_date_user_timezone', Value('.0000000'), Value(""))
        )

        if id_reference__report_name__startswith:
            queryset = queryset.filter(
                id_reference__report_name__startswith=id_reference__report_name__startswith)

        queryset = queryset.filter(
            report_name__contains=report_name,
            status__contains=status,
            creation_date_formated__contains=creation_date            
        ).order_by('-creation_date')

        paginator.paginate_queryset(ordering_filter.filter_queryset(request, queryset, ''), request)
        return {
                    'count': paginator.page.paginator.count,
                    'next': paginator.get_next_link(),
                    'previous': paginator.get_previous_link(),
                    'results': paginator.page.object_list
                }

    @log_report(action_type='UPDATE', observation=None)
    def update(self, params, request, pk):
        """Change status of an already saved report"""
        report_type = params['report_name'][0:3]
        updated_report = Report.objects.prefetch_related('metering_report_data').get(pk=pk)

        related_report_activated_status = {
            'RCP': ['S'], # Status that the RCD should be to be considered active
            'RCD': ['S', 'C'] # Status that the Balance should be to be considered active
        }
        active_related_reports = updated_report.related_report.filter(status__in=related_report_activated_status.get(report_type, 'S'))
        active_related_reports_names = active_related_reports.values_list('report_name', flat=True)

        if active_related_reports.exists() and updated_report.status == 'S':
            raise ValidationError({
                'message': 'error_active_related_reports',
                'active_reports': ", ".join(name for name in active_related_reports_names)
            })

        with transaction.atomic():
            updated_report.status = params['status']
            updated_report.save()
        return updated_report

    def generate_data(self, referencing_year, referencing_month):
        active = ['S', 's', '1', 'y', 'Y']
        #eletric_energy = 'Energia Elétrica'
        return GaugePoint.objects.filter(
                status__in=active,
                id_ccee__isnull=False,
                id_ccee__status__in=active,
                id_ccee__code_ccee__isnull=False,
                id_company__status__in=active,
                gauge_data__utc_gauge__year=referencing_year,
                gauge_data__utc_gauge__month=referencing_month
            ).exclude(
                id_ccee__code_ccee__exact=''
            )
        # Removed filter for meter_type
        # id_source__id_meter_type__description = eletric_energy

class ProjectedConsumptionReportRepository(ReportRepository):
    """Class responsible for generating the projected consumption report"""
    report_type = 'RCP'
    report_type_id = 2

    def generate_data(self, referencing_year, referencing_month):
        """Make inquiries and perform the calculations for generating the temporary projected consumption report"""
        clear_temporary_reports()
        month_peak_time, month_off_peak_time = get_peak_time(referencing_month, referencing_year, 'BR')
        return super().generate_data(referencing_year, referencing_month).annotate(
                ccee_data_quantity = Count('gauge_data__utc_gauge', filter=Q(gauge_data__id_measurements__measurement_name__exact='Active Energy CCEE')),
                vale_data_quantity = Count('gauge_data__utc_gauge', filter=Q(gauge_data__id_measurements__measurement_name__exact='Active Energy Vale')),
                ccee_frequency = Max(Cast(F('gauge_data__id_measurements__frequency'), output_field=FloatField()), filter=Q(gauge_data__id_measurements__measurement_name__exact='Active Energy CCEE')),
                vale_frequency = Max(Cast(F('gauge_data__id_measurements__frequency'), output_field=FloatField()), filter=Q(gauge_data__id_measurements__measurement_name__exact='Active Energy Vale')),
                measured_off_peak_hours = Cast(Count('gauge_data__utc_gauge', filter=Q(gauge_data__id_measurements__measurement_name__exact='Active Energy CCEE Fora Ponta')), output_field=FloatField()),
                monthly_off_peak_hours = Cast(Count('gauge_data__utc_gauge', filter=Q(gauge_data__id_measurements__measurement_name__in=['Active Energy CCEE Fora Ponta','Active Energy Vale Fora Ponta'])), output_field=FloatField()),
                gross_off_peak_consumption_ccee = Sum('gauge_data__value', filter=Q(gauge_data__id_measurements__measurement_name__exact='Active Energy CCEE Fora Ponta')),
                measured_on_peak_hours = Cast(Count('gauge_data__utc_gauge', filter=Q(gauge_data__id_measurements__measurement_name__exact='Active Energy CCEE Ponta')), output_field=FloatField()),
                monthly_on_peak_hours = Cast(Count('gauge_data__utc_gauge', filter=Q(gauge_data__id_measurements__measurement_name__in=['Active Energy CCEE Ponta','Active Energy Vale Ponta'])), output_field=FloatField()),
                gross_on_peak_consumption_ccee = Sum('gauge_data__value', filter=Q(gauge_data__id_measurements__measurement_name__exact='Active Energy CCEE Ponta')),
                measured_off_peak_hours_vale = Cast(Count('gauge_data__utc_gauge', filter=Q(gauge_data__id_measurements__measurement_name__exact='Active Energy Vale Fora Ponta')), output_field=FloatField()),
                gross_off_peak_consumption_vale = Sum('gauge_data__value', filter=Q(gauge_data__id_measurements__measurement_name__exact='Active Energy Vale Fora Ponta')),
                measured_on_peak_hours_vale = Cast(Count('gauge_data__utc_gauge', filter=Q(gauge_data__id_measurements__measurement_name__exact='Active Energy Vale Ponta')), output_field=FloatField()),
                gross_on_peak_consumption_vale = Sum('gauge_data__value', filter=Q(gauge_data__id_measurements__measurement_name__exact='Active Energy Vale Ponta')),
            ).annotate(
                projected_gross_consumption_ccee1 = Case(
                    When(measured_off_peak_hours__gt=0, then=(Decimal(month_off_peak_time) / F('measured_off_peak_hours')) * (F('gross_off_peak_consumption_ccee'))),
                    default=Value('0'),
                    output_field=DecimalField()
                ),
                projected_gross_consumption_ccee2 = Case(
                    When(measured_on_peak_hours__gt=0, then=(Decimal(month_peak_time) / F('measured_on_peak_hours')) * (F('gross_on_peak_consumption_ccee'))),
                    default=Value('0'),
                    output_field=DecimalField()
                ),
                projected_gross_consumption_vale1 = Case(
                    When(measured_off_peak_hours_vale__gt=0, then=(Decimal(month_off_peak_time) / F('measured_off_peak_hours_vale')) * (F('gross_off_peak_consumption_vale'))),
                    default=Value('0'),
                    output_field=DecimalField()
                ),
                projected_gross_consumption_vale2 = Case(
                    When(measured_on_peak_hours_vale__gt=0, then=(Decimal(month_peak_time) / F('measured_on_peak_hours_vale')) * (F('gross_on_peak_consumption_vale'))),
                    default=Value('0'),
                    output_field=DecimalField()
                ),
            ).annotate(
                ccee_code = F('id_ccee__code_ccee'),
                gauge_tag = F('id_source__display_name'),
                associated_company = F('id_company__company_name'),
                ccee_consumption = Case(
                    When(ccee_data_quantity__gt=0, then=(F('projected_gross_consumption_ccee1')+F('projected_gross_consumption_ccee2'))/1000),
                    default=Value('0'),
                    output_field=DecimalField()
                ),
                ccee_metering_days = Case(When(ccee_data_quantity__gt=0, then=F('ccee_data_quantity') / (24 * F('ccee_frequency'))), default=Value('0'), output_field=DecimalField()),
                vale_consumption = Case(
                    When(vale_data_quantity__gt=0, then=(F('projected_gross_consumption_vale1')+F('projected_gross_consumption_vale2'))/1000),
                    default=Value('0'),
                    output_field=DecimalField()
                ),
                vale_metering_days = Case(When(vale_data_quantity__gt=0, then=F('vale_data_quantity') / (24 * F('vale_frequency'))), default=Value('0'), output_field=DecimalField())
            ).order_by('associated_company', 'gauge_tag')
    
    def get_queryset(self, params, pk):
        """Returns a saved report using parameters and primary key"""
        projected_consumption_ccee = replace_comma_with_dot(params.get('projected_consumption_ccee', ''))
        projected_consumption_vale = replace_comma_with_dot(params.get('projected_consumption_vale', ''))

        return MeteringReportData.objects.prefetch_related('consumption_values').annotate(
            projected_consumption_ccee=F('consumption_values__ccee_consumption_value'), 
            metering_days_ccee=F('consumption_values__ccee_metering_days'), 
            projected_consumption_vale=F('consumption_values__vale_consumption_value'), 
            metering_days_vale=F('consumption_values__vale_metering_days'), 
            ccee_consumption_value_rounded=StrSQL(F('consumption_values__ccee_consumption_value'), 21, 3),
            vale_consumption_value_rounded=StrSQL(F('consumption_values__vale_consumption_value'), 21, 3),
            metering_days_ccee_rounded=StrSQL(F('consumption_values__ccee_metering_days'), 21, 2),
            metering_days_vale_rounded=StrSQL(F('consumption_values__vale_metering_days'), 21, 2),
            ccee_vs_vale=Case(
                When(Q(projected_consumption_vale=0) & Q(projected_consumption_ccee=0),
                then=Value('0')),
                When(projected_consumption_vale__gt=0, 
                then=AbsSQL((1 - (F('projected_consumption_ccee') / F('projected_consumption_vale'))) * Value('100'))),
                default=Value('100'), 
                output_field=DecimalField()                
            ),
            ccee_vs_vale_rounded=StrSQL(F('ccee_vs_vale'), 21, 2),
        ).filter(
            report=pk, 
            ccee_code__contains=params.get('ccee_code', ''), 
            gauge_tag__contains=params.get('gauge_tag', ''), 
            associated_company__contains=params.get('associated_company', ''), 
            ccee_consumption_value_rounded__contains=projected_consumption_ccee, 
            vale_consumption_value_rounded__contains=projected_consumption_vale, 
            metering_days_ccee_rounded__contains=params.get('metering_days_ccee', ''),
            metering_days_vale_rounded__contains=params.get('metering_days_vale', ''),
            ccee_vs_vale_rounded__contains=params.get('ccee_vs_vale', ''),
            data_source__contains=params.get('data_source', '')
        ).annotate(
            report_name=F('report__report_name'), 
            limit_value=F('report__limit_value'),
            referenced_report_name=F('report__id_reference'),
            referencing_month = F('report__month'), 
            referencing_year=F('report__year'),
        ).order_by('associated_company', 'gauge_tag')


class GrossConsumptionReportRepository(ReportRepository):
    """Class responsible for generating the gross consumption report"""
    report_type = 'RCB'
    report_type_id = 1

    def generate_data(self, referencing_year, referencing_month):
        """Consult and perform calculations to generate the temporary gross consumption report"""
        clear_temporary_reports()
        return super().generate_data(referencing_year, referencing_month).annotate(
                ccee_data_quantity=Count('gauge_data__utc_gauge', filter=Q(gauge_data__id_measurements__measurement_name__exact='Active Energy CCEE')),
                vale_data_quantity=Count('gauge_data__utc_gauge', filter=Q(gauge_data__id_measurements__measurement_name__exact='Active Energy Vale')),
                ccee_frequency=Max(Cast(F('gauge_data__id_measurements__frequency'), output_field=FloatField()), filter=Q(gauge_data__id_measurements__measurement_name__exact='Active Energy CCEE')),
                vale_frequency=Max(Cast(F('gauge_data__id_measurements__frequency'), output_field=FloatField()), filter=Q(gauge_data__id_measurements__measurement_name__exact='Active Energy Vale'))
            ).annotate(
                ccee_code=F('id_ccee__code_ccee'),
                gauge_tag=F('id_source__display_name'),
                associated_company=F('id_company__company_name'),
                ccee_consumption=Case(When(ccee_data_quantity__gt=0, then=GrossConsumptionExpressionBuilder.with_measurement('Active Energy CCEE').build()), default=Value('0'), output_field=DecimalField()),
                ccee_metering_days=Case(When(ccee_data_quantity__gt=0, then=F('ccee_data_quantity') / (24 * F('ccee_frequency'))), default=Value('0'), output_field=DecimalField()),
                vale_consumption=Case(When(vale_data_quantity__gt=0, then=GrossConsumptionExpressionBuilder.with_measurement('Active Energy Vale').build()), default=Value('0'), output_field=DecimalField()),
                vale_metering_days=Case(When(vale_data_quantity__gt=0, then=F('vale_data_quantity') / (24 * F('vale_frequency'))), default=Value('0'), output_field=DecimalField())
            ).order_by('associated_company', 'gauge_tag')
    
    def get_queryset(self, params, pk):
        """Returns a saved report using parameters and primary key"""
        gross_consumption_ccee = replace_comma_with_dot(params.get('gross_consumption_ccee', ''))
        gross_consumption_vale = replace_comma_with_dot(params.get('gross_consumption_vale', ''))

        return MeteringReportData.objects.prefetch_related('consumption_values').annotate(
            ccee_consumption_value_rounded=StrSQL(F('consumption_values__ccee_consumption_value'), 21, 3),
            vale_consumption_value_rounded=StrSQL(F('consumption_values__vale_consumption_value'), 21, 3),
            metering_days_ccee_rounded=StrSQL(F('consumption_values__ccee_metering_days'), 21, 2),
            metering_days_vale_rounded=StrSQL(F('consumption_values__vale_metering_days'), 21, 2),
        ).filter(
            report=pk, 
            ccee_code__contains=params.get('ccee_code', ''), 
            gauge_tag__contains=params.get('gauge_tag', ''), 
            associated_company__contains=params.get('associated_company', ''), 
            ccee_consumption_value_rounded__contains=gross_consumption_ccee, 
            vale_consumption_value_rounded__contains=gross_consumption_vale,
            metering_days_ccee_rounded__contains=params.get('metering_days_ccee', ''),
            metering_days_vale_rounded__contains=params.get('metering_days_vale', '')
        ).annotate(
            report_name=F('report__report_name'), 
            gross_consumption_ccee=F('consumption_values__ccee_consumption_value'), 
            metering_days_ccee=F('consumption_values__ccee_metering_days'), 
            gross_consumption_vale=F('consumption_values__vale_consumption_value'), 
            metering_days_vale=F('consumption_values__vale_metering_days'), 
            limit_value=F('report__limit_value'),
            referenced_report_name=F('report__id_reference'),
            referencing_month = F('report__month'), 
            referencing_year=F('report__year')
        ).order_by('associated_company', 'gauge_tag')


class DetailedConsumptionReportRepository(ReportRepository):
    """Class responsible for generating the detailed projected consumption report"""
    report_type = 'RCD'
    report_type_id = 3

    def generate_data(self, referenced_report_id, search_list, year, month, request):
        """Make queries and perform the calculations for generating the detailed detailed projected consumption report"""
        clear_temporary_reports()
        reports = Report.objects.get(pk=referenced_report_id)
        metering_report_datas = MeteringReportData.objects.filter(report=reports)
        if metering_report_datas.count() == 0:
            return Response('error_no_metering_data', 400)

        associated_companies = []
        vale_gauge_tags = []
        for data in metering_report_datas:
            associated_companies.append(data.associated_company)
            if data.data_source == 'VALE':
                vale_gauge_tags.append(data.gauge_tag)

        month_peak_time, month_off_peak_time = get_peak_time(month, year, 'BR')
        only_asset_with_show_balance = Q(id_company__company_name__in=associated_companies, show_balance__exact='Assets')
        only_asset_without_show_balance = Q(id_company__company_name__in=associated_companies, show_balance__exact='Asset items')
        asset_item_with_show_balance = Q(asset_items__id_company__company_name__in=associated_companies, show_balance__exact='Assets')
        asset_item_without_show_balance = Q(asset_items__id_company__company_name__in=associated_companies, show_balance__exact='Asset items')
        queryset = Assets.objects.filter(only_asset_with_show_balance | asset_item_with_show_balance).annotate(
            director_board = F('asset_composition__id_energy_composition__id_director__description'),
            business = F('asset_composition__id_energy_composition__id_business__description'),
            consumer = F('id_company__company_name'),
            kpi_formulae = F('asset_composition__id_energy_composition__kpi_formulae'),
            projected_consumption_off_peak = Value('0', output_field=DecimalField()),
            projected_consumption_on_peak = Value('0', output_field=DecimalField()),
            total_projected_consumption = Value('0', output_field=DecimalField()),
            projected_consumption_off_peak_rounded = Value('0', output_field=CharField()),
            projected_consumption_on_peak_rounded = Value('0', output_field=CharField()),
            total_projected_consumption_rounded = Value('0', output_field=CharField()),
            ccee_consumption_value = Value('0', output_field=DecimalField()),
            vale_consumption_value = Value('0', output_field=DecimalField()),
            loss_percentage = F('asset_composition__id_energy_composition__composition_loss'),
            total_projected_consumption_more_loss_type_1 = ExpressionWrapper(Sum(F('id_company__gauge_points__gauge_data__value'), filter=Q(id_company__gauge_points__gauge_data__id_measurements__measurement_name__exact='Active Energy CCEE')) * (1.0 + F('loss_percentage')/100.0), output_field=DecimalField()),
            total_projected_consumption_more_loss_type_2 = ExpressionWrapper(Sum(F('id_company__gauge_points__gauge_data__value'), filter=Q(id_company__gauge_points__gauge_data__id_measurements__measurement_name__exact='Active Energy CCEE')) / (1.0 - F('loss_percentage')/100.0), output_field=DecimalField()),
            metering_days = F('id_company'),
            id_company_asset_item = F('id_company'), # won't be used, added this for union to work
        ).union(Assets.objects.filter(only_asset_without_show_balance | asset_item_without_show_balance).annotate(
            director_board = F('asset_items__id_energy_composition__id_director__description'),
            business = F('asset_items__id_energy_composition__id_business__description'),
            consumer = F('asset_items__id_company__company_name'),
            kpi_formulae = F('asset_items__id_energy_composition__kpi_formulae'),
            projected_consumption_off_peak = Value('0', output_field=DecimalField()),
            projected_consumption_on_peak = Value('0', output_field=DecimalField()),
            total_projected_consumption = Value('0', output_field=DecimalField()),
            projected_consumption_off_peak_rounded = Value('0', output_field=CharField()),
            projected_consumption_on_peak_rounded = Value('0', output_field=CharField()),
            ccee_consumption_value = Value('0', output_field=DecimalField()),
            vale_consumption_value = Value('0', output_field=DecimalField()),
            total_projected_consumption_rounded = Value('0', output_field=CharField()),
            loss_percentage = F('asset_items__id_energy_composition__composition_loss'),
            total_projected_consumption_more_loss_type_1 = ExpressionWrapper(Sum(F('asset_items__id_company__gauge_points__gauge_data__value'), filter=Q(asset_items__id_company__gauge_points__gauge_data__id_measurements__measurement_name__exact='Active Energy CCEE')) * (1.0 + F('loss_percentage')/100.0), output_field=DecimalField()),
            total_projected_consumption_more_loss_type_2 = ExpressionWrapper(Sum(F('asset_items__id_company__gauge_points__gauge_data__value'), filter=Q(asset_items__id_company__gauge_points__gauge_data__id_measurements__measurement_name__exact='Active Energy CCEE')) / (1.0 - F('loss_percentage')/100.0), output_field=DecimalField()),
            metering_days = F('id_company'),
            id_company_asset_item = F('asset_items__id_company'),
        ), all=True).order_by('consumer', 'business')

        for i, asset in enumerate(queryset):
            kpi_formulae = asset.kpi_formulae
            off_peak = kpi_formulae
            on_peak = kpi_formulae
            total = kpi_formulae
            ccee_consumption_value = Decimal()
            vale_consumption_value = Decimal()
            data_source = ''

            if asset.id_company.characteristics == 'consumidora' and (kpi_formulae is None or kpi_formulae == ''):
                raise PreconditionFailed({'asset': asset.consumer})

            for formulae in re.finditer(r'(?:\{(?P<express>[^}{]+)\})', kpi_formulae.replace('\"', '')):
                formulae = formulae.groupdict()
                gross_off_peak_sum = Decimal('0.0')
                measured_off_peak_hours = Decimal('0.0')
                gross_on_peak_sum = Decimal('0.0')
                measured_on_peak_hours = Decimal('0.0')
                gross_total_sum = Decimal('0.0')
                total_mensured_hours = Decimal('0.0')

                if 'express' in formulae:
                    express_json = re.sub(r'(?i)([\w_\-\d]+)\:', r'"\1":', formulae['express'])
                    express_dic = json.loads('{'+express_json.replace('\'','"')+'}')

                    if 'id' in express_dic:
                        id_gauce = express_dic['id']
                        data_source = 'CCEE'
                        gauge_point = GaugePoint.objects.get(pk=id_gauce)

                        if gauge_point.id_source.display_name in vale_gauge_tags:
                            data_source = 'VALE'
                        
                        gross_off_peak_sum = GaugeData.objects.filter(id_gauge=id_gauce, utc_gauge__year=year, utc_gauge__month=month, id_measurements__measurement_name__exact=f"Active Energy {data_source} Fora Ponta").aggregate(
                            Sum('value')
                        )['value__sum'] or 0.0

                        measured_off_peak_hours = GaugeData.objects.filter(id_gauge=id_gauce, utc_gauge__year=year, utc_gauge__month=month, id_measurements__measurement_name__exact=f"Active Energy {data_source} Fora Ponta").aggregate(
                            Count('utc_gauge')
                        )['utc_gauge__count'] or 0.0

                        gross_on_peak_sum = GaugeData.objects.filter(id_gauge=id_gauce, utc_gauge__year=year, utc_gauge__month=month, id_measurements__measurement_name__exact=f"Active Energy {data_source} Ponta").aggregate(
                            Sum('value')
                        )['value__sum'] or 0.0

                        measured_on_peak_hours = GaugeData.objects.filter(id_gauge=id_gauce, utc_gauge__year=year, utc_gauge__month=month, id_measurements__measurement_name__exact=f"Active Energy {data_source} Ponta").aggregate(
                            Count('utc_gauge')
                        )['utc_gauge__count'] or 0.0

                        gross_total_sum = GaugeData.objects.filter(id_gauge=id_gauce, utc_gauge__year=year, utc_gauge__month=month, id_measurements__measurement_name__exact=f"Active Energy {data_source}").aggregate(
                            Sum('value')
                        )['value__sum'] or 0.0

                        total_mensured_hours = Decimal(measured_off_peak_hours + measured_on_peak_hours)

                        if not bool(measured_off_peak_hours):
                            gauge_point_off_peak = Decimal('0.0')
                        else:
                            gauge_point_off_peak = ((Decimal(month_off_peak_time) / Decimal(measured_off_peak_hours)) * Decimal(gross_off_peak_sum)) / 1000

                        if not bool(measured_on_peak_hours):
                            gauge_point_on_peak = Decimal('0.0')
                        else:
                            gauge_point_on_peak = ((Decimal(month_peak_time) / Decimal(measured_on_peak_hours)) * Decimal(gross_on_peak_sum)) / 1000

                        if not bool(total_mensured_hours):
                            gauge_point_total = Decimal('0.0')
                        else:
                            gauge_point_total = ((Decimal(month_off_peak_time)+Decimal(month_peak_time))/(total_mensured_hours)) * Decimal(gross_total_sum) / 1000

                        off_peak = off_peak.replace(formulae['express'], str(gauge_point_off_peak)).replace('{','(').replace('}', ')')
                        on_peak = on_peak.replace(formulae['express'], str(gauge_point_on_peak)).replace('{','(').replace('}', ')')
                        total = total.replace(formulae['express'], str(gauge_point_total)).replace('{', '(').replace('}', ')')

                        kpi_formulae = kpi_formulae.replace(formulae['express'], '').replace('{', '(').replace('}', ')')

            try:
                gross_off_peak_value = eval(off_peak)
            except:
                gross_off_peak_value = Decimal()

            try:
                gross_on_peak_value = eval(on_peak)
            except:
                gross_on_peak_value = Decimal()

            try:
                total_value = eval(total)
            except:
                total_value = Decimal()

            try:
                asset.projected_consumption_off_peak = Decimal(gross_off_peak_value)
            except:
                asset.projected_consumption_off_peak = Decimal()

            try:
                asset.projected_consumption_on_peak = Decimal(gross_on_peak_value)
            except:
                asset.projected_consumption_on_peak = Decimal()

            try:
                asset.total_projected_consumption = Decimal(gross_off_peak_value) + Decimal(gross_on_peak_value)
            except:
                asset.total_projected_consumption = Decimal()

            loss_percentage = asset.loss_percentage if asset.loss_percentage is not None else Decimal('0.0')
            asset.total_projected_consumption_more_loss_type_1 = asset.total_projected_consumption * (1 + (loss_percentage/100))
            asset.total_projected_consumption_more_loss_type_2 = asset.total_projected_consumption / (1 - (loss_percentage/100))
            if data_source == 'VALE':
                asset.vale_consumption_value = asset.total_projected_consumption
            else:
                asset.ccee_consumption_value = asset.total_projected_consumption
            asset.loss_type = '1'
            asset.total_consumption_loss = asset.total_projected_consumption_more_loss_type_1
            
        return queryset, metering_report_datas, reports

    def get_queryset(self, params, pk):
        """Returns a saved report using parameters and primary key"""
        director_board = params.get('director_board', '')
        director_board_null = True if director_board == '' else False
        business = params.get('business', '')
        business_null = True if business == '' else False
        consumer = params.get('consumer', '')
        projected_consumption_off_peak = params.get('projected_consumption_off_peak', '')
        projected_consumption_on_peak = params.get('projected_consumption_on_peak', '')
        total_projected_consumption = params.get('total_projected_consumption', '')
        loss_percentage = params.get('loss_percentage', '')
        loss_type = params.get('loss_type', '').replace('type', '')
        total_projected_contumption_with_losses = params.get('total_projected_consumption_more_loss_type_1', '')
        report = Report.objects.get(pk=pk)
        referenced = Report.objects.get(pk=report.id_reference.id)
        director_criterion = Q(director_board__isnull=True)
        business_criterion = Q(business__isnull=True)

        return MeteringReportData.objects.prefetch_related('consumption_values').annotate(
            data_source_value=F('data_source')
        ).filter(
            report=pk,
        ).annotate(
            report_name=F('report__report_name'), 
            consumer=F('associated_company'),
            projected_consumption_ccee=F('consumption_values__ccee_consumption_value'), 
            metering_days_ccee=F('consumption_values__ccee_metering_days'), 
            projected_consumption_vale=F('consumption_values__vale_consumption_value'), 
            metering_days_vale=F('consumption_values__vale_metering_days'), 
            limit_value=F('report__limit_value'),
            referenced_report_name=F('report__id_reference__report_name'),
            referencing_month = F('report__month'), 
            referencing_year=F('report__year'),
            projected_consumption_off_peak=F('consumption_values__off_peak_consumption_value'),
            projected_consumption_on_peak=F('consumption_values__on_peak_consumption_value'),
            total_projected_consumption=Case(
                When(
                    projected_consumption_vale=Value(Decimal('0.0'), output_field=DecimalField()), 
                    then=F('projected_consumption_ccee')
                    ),
                When(
                    projected_consumption_ccee=Value(Decimal('0.0'), output_field=DecimalField()), 
                    then=F('projected_consumption_vale')
                ),
                default=F('projected_consumption_ccee'),
                output_field=DecimalField()
            ),
            loss_percentage_temp=F('consumption_values__loss'),
            loss_percentage=Coalesce('loss_percentage_temp', Value('0.0')),
            total_projected_consumption_with_losses=F('consumption_values__total_consumption_loss'),
        ).annotate(
            total_projected_consumption_more_loss_type_1=F('total_projected_consumption')*(1.0 + F('loss_percentage')/100.0),
            total_projected_consumption_more_loss_type_2=F('total_projected_consumption')/(1.0 - F('loss_percentage')/100.0),
            projected_consumption_off_peak_rounded=StrSQL(F('projected_consumption_off_peak'), 21, 3),
            projected_consumption_on_peak_rounded=StrSQL(F('projected_consumption_on_peak'), 21, 3),
            total_projected_consumption_rounded=StrSQL(F('total_projected_consumption'), 21, 3),
            loss_percentage_rounded=StrSQL(F('loss_percentage'), 21, 3),
            total_projected_consumption_with_losses_rounded=StrSQL(F('total_projected_consumption_with_losses'), 21, 3),
            director_board_filter=Value(director_board, output_field=CharField()),
            business_filter=Value(business, output_field=CharField()),
        ).filter(
            (Q(director_board__isnull=director_board_null) & Q(director_board__contains=director_board)) |
            Q(director_board_filter='')
        ).filter(
            (Q(business__isnull=business_null) & Q(business__contains=business)) |
            Q(business_filter='')
        ).filter(
            associated_company__contains=consumer,
            projected_consumption_off_peak_rounded__contains=projected_consumption_off_peak,
            projected_consumption_on_peak_rounded__contains=projected_consumption_on_peak,
            total_projected_consumption_rounded__contains=total_projected_consumption,
            loss_percentage_rounded__contains=loss_percentage,
            loss_type__contains=loss_type,
            total_projected_consumption_with_losses_rounded__contains=total_projected_contumption_with_losses,
        ).order_by('consumer', 'business')






#================================================================================
#================================================================================
#================================================================================
#================================================================================
class DetailedConsumptionReportRepositoryNew(ReportRepository):
    """Class responsible for generating the detailed projected consumption report"""
    report_type = 'RPD'
    report_type_id = 6

    def generate_data(self, year, month, request):
        """Make queries and perform the calculations for generating the detailed detailed projected consumption report"""
        clear_temporary_reports()

        reference_report = None        
        is_edit_report = request.data['params'].get("referenced_report_id", None) is not None
        consumptions_to_update = request.data['params'].get("update_consumptions", []) or []
        filter_only_edits_assets = Q()
        filter_only_edits_asset_items = Q()
        not_change_metering_datas = []
        get_data = lambda asset, asset_items: None
        
        if is_edit_report:
            reference_report = Report.objects.filter(id=request.data['params'].get("referenced_report_id")).first()
            reference_report_data = reference_report.metering_report_data.all()
            list_assets = list(reference_report_data.filter(id_assets__isnull=False, id__in=consumptions_to_update)) #.values_list('id_assets', flat=True)
            filter_only_edits_assets = Q(id_assets__in=list(map(lambda x: x.id_assets_id, list_assets)))
            list_asset_items = list(reference_report_data.filter(id_asset_items__isnull=False, id__in=consumptions_to_update)) #.values_list('id_asset_items', flat=True)
            filter_only_edits_asset_items = Q(asset_items__id_asset_items__in=list(map(lambda x: x.id_asset_items_id, list_asset_items)))
            not_change_metering_datas = reference_report_data.exclude(id__in=consumptions_to_update)

            datas = list_assets + list_asset_items
            get_data = lambda asset, asset_items: next(filter(lambda x: x.id_assets_id==asset and x.id_asset_items_id==asset_items, datas), None)


        only_asset_with_show_balance = Q(show_balance__exact='Assets', status='S', id_company__characteristics='consumidora')
        only_asset_without_show_balance = Q(show_balance__exact='Asset items', status='S', id_company__characteristics='consumidora')

        queryset = list(Assets.objects.filter(only_asset_with_show_balance).filter(filter_only_edits_assets).annotate(
            director_board = F('asset_composition__id_energy_composition__id_director__description'),
            business = F('asset_composition__id_energy_composition__id_business__description'),
            consumer = F('id_company__company_name'),
            kpi_formulae = F('asset_composition__id_energy_composition__kpi_formulae'),
            loss_percentage = F('asset_composition__id_energy_composition__composition_loss'),
            id_company_asset_item = F('id_company'), # won't be used, added this for union to work
            id_asset_items=Value(value=None, output_field=DecimalField())
        ).union(Assets.objects.filter(only_asset_without_show_balance).filter(filter_only_edits_asset_items).annotate(
            director_board = F('asset_items__id_energy_composition__id_director__description'),
            business = F('asset_items__id_energy_composition__id_business__description'),
            consumer = F('asset_items__id_company__company_name'),
            kpi_formulae = F('asset_items__id_energy_composition__kpi_formulae'),
            loss_percentage = F('asset_items__id_energy_composition__composition_loss'),
            id_company_asset_item = F('asset_items__id_company'),
            id_asset_items=F('asset_items__id_asset_items')
        ), all=True).order_by('consumer', 'business'))
        
        comsumptions = self.prefetch_asset_comsumption(queryset, year, month)
        
        for asset in queryset:
            if is_edit_report:
                asset.updated_consumption = True    
                asset_data = get_data(asset.id_assets if not asset.id_asset_items else None, asset.id_asset_items)
                if asset_data:
                    asset.data_source = asset_data.data_source
                    asset.loss_type = asset_data.loss_type

            self.calculate_asset_comsumption(asset, year, month, asset.data_source, comsumptions)

        queryset = list(queryset) + list(not_change_metering_datas)
            
        return queryset, reference_report

    def prefetch_asset_comsumption(self, queryset, year, month):
        id_gauges = []
        for asset in queryset:
            if not getattr(asset, "data_source", None):
                asset.data_source = "CCEE"

            kpi_formulae = getattr(asset, "kpi_formulae", None)
            if not kpi_formulae:
                if getattr(asset, 'id_assets_id', False):
                    all_composition = list(asset.id_assets.asset_composition.all())
                    if all_composition and all_composition[0].id_energy_composition:
                        kpi_formulae = all_composition[0].id_energy_composition.kpi_formulae
                if getattr(asset, 'asset_composition', False):
                    all_composition = list(asset.asset_composition.all())
                    if all_composition and all_composition[0].id_energy_composition:
                        kpi_formulae = all_composition[0].id_energy_composition.kpi_formulae
                if getattr(asset, 'id_asset_items_id', False):
                    if asset.id_asset_items.id_energy_composition:
                        kpi_formulae = asset.id_asset_items.id_energy_composition.kpi_formulae
            setattr(asset, "kpi_formulae", kpi_formulae)

            if not kpi_formulae:
                raise PreconditionFailed({'asset': asset.consumer or asset.id_company.company_name})

            for formulae in re.finditer(r'(?:\{(?P<express>[^}{]+)\})', kpi_formulae.replace('\"', '')):
                formulae = formulae.groupdict()

                if 'express' in formulae:
                    express_json = re.sub(r'(?i)([\w_\-\d]+)\:', r'"\1":', formulae['express'])
                    express_dic = json.loads('{'+express_json.replace('\'','"')+'}')

                    if 'id' in express_dic:
                        id_gauges.append(express_dic['id'])


        gauge_data_values = list(GaugeData.objects.filter(
            id_gauge__in=id_gauges, utc_gauge__year=year, utc_gauge__month=month, 
            id_measurements__id_measurements__in=[3,4,11,12]). \
            values("id_gauge", "id_measurements__id_measurements"). \
            annotate(Count('utc_gauge'), Sum('value'), 
            frequency=Max(F('id_measurements__frequency'), output_field=FloatField()), 
            metering_days=Case(When(utc_gauge__count__gt=0, then=F('utc_gauge__count') / (24.0 * F('frequency'))), default=Value('0'), output_field=DecimalField())))

        comsumptions = {}
        
        for values in gauge_data_values:
            key = f"{values['id_gauge']}_{values['id_measurements__id_measurements']}"
            comsumptions[key] = values['value__sum'], values['utc_gauge__count'], values['metering_days']

        def comsumptions_find(id_gauge, id_measurements):
            key = f"{id_gauge}_{id_measurements}"
            return comsumptions.get(key) or (0,0,0)

        return comsumptions_find



    def calculate_asset_comsumption(self, asset, year, month, data_source, comsumptions):
        kpi_formulae = getattr(asset, "kpi_formulae")
        
        off_peak = kpi_formulae
        on_peak = kpi_formulae
        ccee_off_peak = kpi_formulae
        ccee_on_peak = kpi_formulae
        vale_off_peak = kpi_formulae
        vale_on_peak = kpi_formulae
        month_peak_time, month_off_peak_time = get_peak_time(int(month), int(year), 'BR')
        vale_max_metering_days = Decimal(0.0)
        ccee_max_metering_days = Decimal(0.0)        

        if asset.id_company.characteristics == 'consumidora' and (kpi_formulae is None or kpi_formulae == ''):
            raise PreconditionFailed({'asset': asset.consumer})

        for formulae in re.finditer(r'(?:\{(?P<express>[^}{]+)\})', kpi_formulae.replace('\"', '')):
            formulae = formulae.groupdict()
            gross_off_peak_sum = Decimal('0.0')
            measured_off_peak_hours = Decimal('0.0')
            gross_on_peak_sum = Decimal('0.0')
            measured_on_peak_hours = Decimal('0.0')
            
            if 'express' in formulae:
                express_json = re.sub(r'(?i)([\w_\-\d]+)\:', r'"\1":', formulae['express'])
                express_dic = json.loads('{'+express_json.replace('\'','"')+'}')

                if 'id' in express_dic:
                    id_gauce = express_dic['id']
                    
                    vale_gross_on_peak_sum, vale_measured_on_peak_hours, vale_metering_on_peak_days = comsumptions(id_gauce, 3)
                    vale_gross_off_peak_sum, vale_measured_off_peak_hours, vale_metering_off_peak_days = comsumptions(id_gauce, 4)
                    ccee_gross_on_peak_sum, ccee_measured_on_peak_hours, ccee_metering_on_peak_days = comsumptions(id_gauce, 11)
                    ccee_gross_off_peak_sum, ccee_measured_off_peak_hours, ccee_metering_off_peak_days = comsumptions(id_gauce, 12)
                    
                    if data_source == "VALE":
                        gross_off_peak_sum = vale_gross_off_peak_sum
                        measured_off_peak_hours = vale_measured_off_peak_hours
                        gross_on_peak_sum = vale_gross_on_peak_sum
                        measured_on_peak_hours = vale_measured_on_peak_hours
                    else:
                        gross_off_peak_sum = ccee_gross_off_peak_sum
                        measured_off_peak_hours = ccee_measured_off_peak_hours
                        gross_on_peak_sum = ccee_gross_on_peak_sum
                        measured_on_peak_hours = ccee_measured_on_peak_hours

                    if not bool(measured_off_peak_hours):
                        gauge_point_off_peak = Decimal('0.0')
                    else:
                        gauge_point_off_peak = ((Decimal(month_off_peak_time) / Decimal(measured_off_peak_hours)) * Decimal(gross_off_peak_sum)) / 1000

                    if not bool(measured_on_peak_hours):
                        gauge_point_on_peak = Decimal('0.0')
                    else:
                        gauge_point_on_peak = ((Decimal(month_peak_time) / Decimal(measured_on_peak_hours)) * Decimal(gross_on_peak_sum)) / 1000


                    if not bool(vale_measured_off_peak_hours):
                        vale_gauge_point_off_peak = Decimal('0.0')
                    else:
                        vale_gauge_point_off_peak = ((Decimal(month_off_peak_time) / Decimal(vale_measured_off_peak_hours)) * Decimal(vale_gross_off_peak_sum)) / 1000

                    if not bool(vale_measured_on_peak_hours):
                        vale_gauge_point_on_peak = Decimal('0.0')
                    else:
                        vale_gauge_point_on_peak = ((Decimal(month_peak_time) / Decimal(vale_measured_on_peak_hours)) * Decimal(vale_gross_on_peak_sum)) / 1000

                    if not bool(ccee_measured_off_peak_hours):
                        ccee_gauge_point_off_peak = Decimal('0.0')
                    else:
                        ccee_gauge_point_off_peak = ((Decimal(month_off_peak_time) / Decimal(ccee_measured_off_peak_hours)) * Decimal(ccee_gross_off_peak_sum)) / 1000

                    if not bool(ccee_measured_on_peak_hours):
                        ccee_gauge_point_on_peak = Decimal('0.0')
                    else:
                        ccee_gauge_point_on_peak = ((Decimal(month_peak_time) / Decimal(ccee_measured_on_peak_hours)) * Decimal(ccee_gross_on_peak_sum)) / 1000

                    off_peak = off_peak.replace(formulae['express'], str(gauge_point_off_peak)).replace('{','(').replace('}', ')')
                    on_peak = on_peak.replace(formulae['express'], str(gauge_point_on_peak)).replace('{','(').replace('}', ')')
                   
                    vale_off_peak = vale_off_peak.replace(formulae['express'], str(vale_gauge_point_off_peak)).replace('{','(').replace('}', ')')
                    vale_on_peak = vale_on_peak.replace(formulae['express'], str(vale_gauge_point_on_peak)).replace('{','(').replace('}', ')')
                    ccee_off_peak = ccee_off_peak.replace(formulae['express'], str(ccee_gauge_point_off_peak)).replace('{','(').replace('}', ')')
                    ccee_on_peak = ccee_on_peak.replace(formulae['express'], str(ccee_gauge_point_on_peak)).replace('{','(').replace('}', ')')
                    vale_max_metering_days = max(vale_max_metering_days, vale_metering_on_peak_days + vale_metering_off_peak_days)
                    ccee_max_metering_days = max(ccee_max_metering_days, ccee_metering_on_peak_days + ccee_metering_off_peak_days)

                    kpi_formulae = kpi_formulae.replace(formulae['express'], '').replace('{', '(').replace('}', ')')

        try:
            gross_off_peak_value = eval(off_peak)
        except:
            gross_off_peak_value = Decimal()
        try:
            ccee_gross_off_peak_value = eval(ccee_off_peak)
        except:
            ccee_gross_off_peak_value = Decimal()
        try:
            vale_gross_off_peak_value = eval(vale_off_peak)
        except:
            vale_gross_off_peak_value = Decimal()

        try:
            gross_on_peak_value = eval(on_peak)
        except:
            gross_on_peak_value = Decimal()
        try:
            ccee_gross_on_peak_value = eval(ccee_on_peak)
        except:
            ccee_gross_on_peak_value = Decimal()
        try:
            vale_gross_on_peak_value = eval(vale_on_peak)
        except:
            vale_gross_on_peak_value = Decimal()
        

        try:
            asset.projected_consumption_off_peak = Decimal(gross_off_peak_value)
        except:
            asset.projected_consumption_off_peak = Decimal()

        try:
            asset.projected_consumption_on_peak = Decimal(gross_on_peak_value)
        except:
            asset.projected_consumption_on_peak = Decimal()

        try:
            asset.total_projected_consumption = Decimal(gross_off_peak_value) + Decimal(gross_on_peak_value)
            asset.ccee_total_projected_consumption = Decimal(ccee_gross_off_peak_value) + Decimal(ccee_gross_on_peak_value)
            asset.vale_total_projected_consumption = Decimal(vale_gross_off_peak_value) + Decimal(vale_gross_on_peak_value)
        except:
            asset.total_projected_consumption = Decimal()

        loss_percentage = asset.loss_percentage if asset.loss_percentage is not None else Decimal('0.0')
        asset.total_projected_consumption_more_loss_type_1 = asset.total_projected_consumption * (1 + (loss_percentage/100))
        asset.total_projected_consumption_more_loss_type_2 = asset.total_projected_consumption / (1 - (loss_percentage/100))
        asset.ccee_consumption_value = asset.ccee_total_projected_consumption
        asset.vale_consumption_value = asset.vale_total_projected_consumption
        asset.ccee_metering_days = ccee_max_metering_days
        asset.vale_metering_days = vale_max_metering_days
        
        if not getattr(asset, 'loss_type', None):
            asset.loss_type = '1'

        if asset.loss_type == '1':
            asset.total_consumption_loss = asset.total_projected_consumption_more_loss_type_1
        else:
            asset.total_consumption_loss = asset.total_projected_consumption_more_loss_type_2

    def get_queryset(self, params, pk):
        """Returns a saved report using parameters and primary key"""
        director_board = params.get('director_board', '') 
        director_board_null = True if director_board == '' else False
        
        business = params.get('business', '')
        business_null = True if business == '' else False        
        consumer = params.get('consumer', '')
        projected_consumption_ccee = params.get('projected_consumption_ccee', '')
        metering_days_ccee = params.get('metering_days_ccee', '')
        projected_consumption_vale = params.get('projected_consumption_vale', '')
        metering_days_vale = params.get('metering_days_vale', '')
        ccee_vs_vale = params.get('ccee_vs_vale', '')
        projected_consumption_off_peak = params.get('projected_consumption_off_peak', '')        
        projected_consumption_on_peak = params.get('projected_consumption_on_peak', '')        
        total_projected_consumption = params.get('total_projected_consumption', '')
        loss_percentage = params.get('loss_percentage', '')                
        total_projected_contumption_with_losses = params.get('total_projected_consumption_more_loss_type_1', '')        
        data_source_criterion = Q(data_source=params.get('data_source')) if params.get('data_source', None) else Q()        
        loss_type_criterion = Q(loss_type=params.get('loss_type')) if params.get('loss_type', None) else Q()        
        
        id_criterion = Q(id=params.get('id')) if params.get('id', None) else Q()
        
        return MeteringReportData.objects.prefetch_related('consumption_values').annotate(
            data_source_value=F('data_source')
        ).filter(
            report=pk,
        ).annotate(
            report_name=F('report__report_name'), 
            consumer=F('associated_company'),
            projected_consumption_ccee=F('consumption_values__ccee_consumption_value'), 
            metering_days_ccee=F('consumption_values__ccee_metering_days'), 
            projected_consumption_vale=F('consumption_values__vale_consumption_value'), 
            metering_days_vale=F('consumption_values__vale_metering_days'), 
            limit_value=F('report__limit_value'),
            referencing_month = F('report__month'), 
            referencing_year=F('report__year'),
            projected_consumption_off_peak=F('consumption_values__off_peak_consumption_value'),
            projected_consumption_on_peak=F('consumption_values__on_peak_consumption_value'),
            total_projected_consumption=Case(
                When(
                    data_source_value=Value('CCEE'), 
                    then=F('projected_consumption_ccee')
                    ),
                When(
                    data_source_value=Value('VALE'), 
                    then=F('projected_consumption_vale')
                ),
                default=F('projected_consumption_ccee'),
                output_field=DecimalField()
            ),
            ccee_vs_vale=Case(
                When(Q(projected_consumption_vale=0) & Q(projected_consumption_ccee=0),
                then=Value('0')),
                When(projected_consumption_vale__gt=0, 
                then=AbsSQL((1 - (F('projected_consumption_ccee') / F('projected_consumption_vale'))) * Value('100'))),
                default=Value('100'), 
                output_field=DecimalField()                
            ),
            loss_percentage_temp=F('consumption_values__loss'),
            loss_percentage=Coalesce('loss_percentage_temp', Value('0.0')),
            total_projected_consumption_with_losses=F('consumption_values__total_consumption_loss'),
        ).annotate(
            total_projected_consumption_more_loss_type_1=F('total_projected_consumption')*(1.0 + F('loss_percentage')/100.0),
            total_projected_consumption_more_loss_type_2=F('total_projected_consumption')/(1.0 - F('loss_percentage')/100.0),
            
            projected_consumption_ccee_rounded=StrSQL(F('projected_consumption_ccee'), 21, 3),
            metering_days_ccee_rounded=StrSQL(F('metering_days_ccee'), 21, 2),
            projected_consumption_vale_rounded=StrSQL(F('projected_consumption_vale'), 21, 3),
            metering_days_vale_rounded=StrSQL(F('metering_days_vale'), 21, 2),
            
            projected_consumption_off_peak_rounded=StrSQL(F('projected_consumption_off_peak'), 21, 3),
            projected_consumption_on_peak_rounded=StrSQL(F('projected_consumption_on_peak'), 21, 3),
            total_projected_consumption_rounded=StrSQL(F('total_projected_consumption'), 21, 3),
            ccee_vs_vale_rounded=StrSQL(F('ccee_vs_vale'), 21, 2),
            referenced_report_name=F('report__id_reference__report_name'),
            loss_percentage_rounded=StrSQL(F('loss_percentage'), 21, 2),
            total_projected_consumption_with_losses_rounded=StrSQL(F('total_projected_consumption_with_losses'), 21, 3),
            director_board_filter=Value(director_board, output_field=CharField()),
            business_filter=Value(business, output_field=CharField()),
        ) \
        .filter(
            (Q(director_board__isnull=director_board_null) & Q(director_board__contains=director_board)) |
            Q(director_board_filter='')) \
        .filter(id_criterion) \
        .filter(data_source_criterion) \
        .filter(loss_type_criterion) \
        .filter(
            (Q(business__isnull=business_null) & Q(business__contains=business)) |
            Q(business_filter='')) \
        .filter(
            associated_company__contains=consumer,
            projected_consumption_ccee_rounded__contains=projected_consumption_ccee,
            metering_days_ccee_rounded__contains=metering_days_ccee,
            projected_consumption_vale_rounded__contains=projected_consumption_vale,
            metering_days_vale_rounded__contains=metering_days_vale,
            ccee_vs_vale_rounded__contains=ccee_vs_vale,
            projected_consumption_off_peak_rounded__contains=projected_consumption_off_peak,
            projected_consumption_on_peak_rounded__contains=projected_consumption_on_peak,
            total_projected_consumption_rounded__contains=total_projected_consumption,
            loss_percentage_rounded__contains=loss_percentage,
            total_projected_consumption_with_losses_rounded__contains=total_projected_contumption_with_losses,            
        ) \
        .order_by('consumer', 'business')
        