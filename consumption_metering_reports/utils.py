from rest_framework.pagination import PageNumberPagination
from functools import reduce
from calendar import monthcalendar, weekday, Calendar, monthrange
from datetime import date
from datetime import datetime
import holidays
from workalendar.america import Brazil
from django.db.models.functions import Cast
from django.db.models import Sum, Count, Q, F, FloatField, ExpressionWrapper, Func, Case, When, CharField
import sys, pytz, time



class Paginator(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 1000

def get_week_days(year, month):
    return [day for day in filter(lambda day: day > 0 and weekday(year, month, day) < 5, reduce(lambda first, next: first + next, monthcalendar(year, month)))]

def get_peak_time(month, year, coutry):
        return get_peek_time(year, month, coutry)

def get_peek_time(year, month, country):
    days = []
    cal = Calendar()
    year = int(year)
    month = int(month)

    _holidays = holidays.BR()

    if country == 'CA':
        _holidays = holidays.CA()
    if country == 'UK':
        _holidays = holidays.UK()

    for week in cal.monthdayscalendar(year, month):
        total_days = list(filter(lambda a: a!= 0, week))
        list_days = list(filter(lambda a: a!= 0, week[:5]))
        for d in list_days:
            if date(year, month, d) in _holidays:
                continue
            days.append(d)

    total_hours = monthrange(year,month)[1] * 24
    peek_time = len(days) * 3
    off_peek_time = total_hours - peek_time
    return peek_time, off_peek_time

def get_last_month_date():
    datetime_now = datetime.now(get_local_timezone())
    if(datetime_now.month == 1):
        lat_month = date(int(datetime_now.year)-1, 12, 1)
    else:
        lat_month = date(int(datetime_now.year), int(datetime_now.month)-1, 1)
    return lat_month

def replace_comma_with_dot(value: str) -> str:
        return value.replace(',', '.')

def get_user_username(request):
    try:
        return f'{request.auth.get("cn")} - {request.auth.get("UserFullName")}'
    except:
        return 'System'


class MeteringDaysExpressionBuilder:
    @classmethod
    def with_measurement(cls, measurement_name):
        cls.__measurement_name = measurement_name
        return cls
    @classmethod
    def build(cls):
        return ExpressionWrapper(Count('gauge_data__utc_gauge', filter=Q(gauge_data__id_measurements__measurement_name__contains=cls.__measurement_name)) / (24 * Sum(Cast('gauge_data__id_measurements__frequency', FloatField()), filter=Q(gauge_data__id_measurements__measurement_name__contains=cls.__measurement_name))), output_field=FloatField())


class GrossConsumptionExpressionBuilder:
    @classmethod
    def with_measurement(cls, measurement_name):
        cls.__measurement_name = measurement_name
        return cls
    @classmethod
    def build(cls):

        return ExpressionWrapper(Sum('gauge_data__value', filter=Q(gauge_data__id_measurements__measurement_name__exact=cls.__measurement_name)) / 1000, output_field=FloatField())


class ProjectedConsumptionExpressionBuilder:
    @classmethod
    def with_measurement(cls, measurement_name):
        cls.__measurement_name = measurement_name
        return cls
    @classmethod
    def to_year(cls, year):
        cls.__year = int(year)
        return cls
    @classmethod
    def to_month(cls, month):
        cls.__month = int(month)
        return cls
    @classmethod
    def build(cls):
        total_of_month_hours = len(get_week_days(cls.__year, cls.__month)) * 24
        metered_on_peak_hours = Count('gauge_data__utc_gauge', filter=Q(gauge_data__id_measurements__measurement_name__exact=f'{cls.__measurement_name} Ponta'))
        metered_off_peak_hours = Count('gauge_data__utc_gauge', filter=Q(gauge_data__id_measurements__measurement_name__exact=f'{cls.__measurement_name} Fora Ponta'))
        on_peak_gross_consumption = GrossConsumptionExpressionBuilder.with_measurement(f'{cls.__measurement_name} Ponta').build()
        off_peak_gross_consumption = GrossConsumptionExpressionBuilder.with_measurement(f'{cls.__measurement_name} Fora Ponta').build()
        return ExpressionWrapper((total_of_month_hours / metered_off_peak_hours) * off_peak_gross_consumption + (total_of_month_hours / metered_on_peak_hours) * on_peak_gross_consumption, output_field=FloatField())


class GetConsumptionFunction(Func):
    function = 'ABS'
    def __init__(self, vale_gauge_tags, on_peak=False, items=False):
        if items:
            filter_ccee = Q(asset_items__id_company__gauge_points__gauge_data__id_measurements__measurement_name__exact=f"Active Energy CCEE {'Ponta' if on_peak else 'Fora Ponta'}")
            filter_vale = Q(asset_items__id_company__gauge_points__gauge_data__id_measurements__measurement_name__exact=f"Active Energy Vale {'Ponta' if on_peak else 'Fora Ponta'}")
            sum_expression = Case(
                When(asset_items__id_company__gauge_points__id_source__display_name__in=vale_gauge_tags, then=Sum(F('asset_items__id_company__gauge_points__gauge_data__value'), filter=filter_vale)),
                default=Sum(F('asset_items__id_company__gauge_points__gauge_data__value'), filter=filter_ccee)
            )
        else:
            filter_ccee = Q(id_company__gauge_points__gauge_data__id_measurements__measurement_name__exact=f"Active Energy CCEE {'Ponta' if on_peak else 'Fora Ponta'}")
            filter_vale = Q(id_company__gauge_points__gauge_data__id_measurements__measurement_name__exact=f"Active Energy Vale {'Ponta' if on_peak else 'Fora Ponta'}")
            sum_expression = Case(
                When(id_company__gauge_points__id_source__display_name__in=vale_gauge_tags, then=Sum(F('id_company__gauge_points__gauge_data__value'), filter=filter_vale)),
                default=Sum(F('id_company__gauge_points__gauge_data__value'), filter=filter_ccee)
            )
        super().__init__(sum_expression)


class StrSQL(Func):
  function = 'STR'
  arity = 3
  output_field = CharField()


class AbsSQL(Func):
  function = 'ABS'


class ValidationError(Exception):
    pass


def get_local_timezone():
    return pytz.timezone(f'Etc/GMT+{int(time.timezone / 3600)}')

