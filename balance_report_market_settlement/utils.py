from rest_framework.pagination import PageNumberPagination
from .models import Report
from consumption_metering_reports.models import MeteringReportData, MeteringReportValue
from workalendar.america import Brazil
from datetime import datetime, date
from calendar import monthrange
from decimal import Decimal, DecimalException
from collections import namedtuple
import pytz, hashlib, sys, time
from profiles.models import Profile
from SmartEnergy.handler_logging import HandlerLog


logger = HandlerLog()


class Paginator(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 1000

def create_nth_brazilian_workday(year, month, n):
    """Return the nth brazilian workday for the specified month and year"""
    cal = Brazil()
    first_day_of_the_month = datetime(year, month, 1)
    if cal.is_working_day(first_day_of_the_month):
        nth_work_day = cal.add_working_days(first_day_of_the_month, n - 1)
    else:
        nth_work_day = cal.add_working_days(first_day_of_the_month, n)
    return nth_work_day

def is_before_or_equal_nth_brazilian_workday(year, month, n):
    """Checks if today is before the nth workday of the specified month and year"""
    today = date.today()
    nth_work_day = create_nth_brazilian_workday(year, month, n)
    return today <= nth_work_day

def is_nth_brazilian_workday(day, n=8):
    """Checks if today is the nth work day of the month
    day: python datetime object to be checked
    n: number of workdays in the month
    """
    cal = Brazil()
    first_day_of_the_month = datetime(day.year, day.month, 1)
    if cal.is_working_day(first_day_of_the_month):
        nth_work_day = cal.add_working_days(first_day_of_the_month, n - 1)
    else:
        nth_work_day = cal.add_working_days(first_day_of_the_month, n)
    return day.date() == nth_work_day

def check_for_balances(year: str, month: str, status: str) -> bool:
    """Checks if there are balances in the specified month and year with the specified status"""
    queryset = Report.objects.filter(
        report_type__initials__exact='BDE',
        month__icontains=month,
        year__icontains=year,
        status__icontains=status
        )
    return queryset.exists()

def gen_report_name(initials, month, year):
        """Create the report name"""
        existing_balance = Report.objects.filter(month=month, year=year, report_type__initials=initials, status__in=['s', 'S', 'n', 'N', 'c', 'C']).count()
        sequential = 0
        if existing_balance != 999:
            sequential = 1 + existing_balance
        return f'{initials}_{str(month).zfill(2)}_{str(year).zfill(4)}_{str(sequential).zfill(3)}'

def mwm_to_mwh(year, month, volume_in_mwm):
    hours_in_month = 24*monthrange(year, month)[1]
    return volume_in_mwm*hours_in_month

def clamp(n, n_min, n_max):
    """Given an interval, values outside the interval are clipped to the interval edges"""
    return max(min(n_max, n), n_min)

def none_to_zero(n):
    """If the input is None, returns 0"""
    if n is None:
        return Decimal()
    else:
        return n

def get_user_username(request):
    try:
        return f'{request.auth.get("cn")} - {request.auth.get("UserFullName")}'
    except:
        return 'System'

def get_last_month_date():
    datetime_now = datetime.now(get_local_timezone())
    if(datetime_now.month == 1):
        lat_month = date(int(datetime_now.year)-1, 12, 1)
    else:
        lat_month = date(int(datetime_now.year), int(datetime_now.month)-1, 1)
    return lat_month



def calculate_flexible_proportional_cliq_volume(cliq, id_reference_report):
    """Given a projected report id calculates the volume for cliq contracts of the type flexible proportional"""
    buyer_profile = cliq.id_buyer_profile
    profiles_id_list = cliq.id_contract.cliq_contract.all().values_list('id_buyer_profile', flat=True)
    profile_list = Profile.objects.filter(pk__in=profiles_id_list)

    total_volume = Decimal('0.0')

    for profile in profile_list:
        profile_volume = Decimal('0.0')
        asset_list = profile.assets_profile.filter(
                id_company__type__in=['I', 'R']
            ).exclude(
                status__in=['0', 'n', 'N']
            )
        for asset in asset_list:
            asset_volume = Decimal('0.0')
            if asset.id_company.characteristics.lower() in 'consumidora':
                if asset.show_balance == 'Assets':
                    asset_volume = get_consumer_volume(id_reference_report, asset.id_company)
                elif asset.show_balance == 'Asset items':
                    asset_item_list = asset.assetitems_asset.filter(
                            id_company__type__in=['I', 'R']
                        ).exclude(
                            status__in=['0', 'n', 'N']
                            )
                    for asset_item in asset_item_list:
                        asset_item_volume = Decimal('0.0')
                        if asset_item.id_company.characteristics.lower() in 'consumidora':
                            asset_item_volume = get_consumer_volume(id_reference_report, asset_item.id_company)
                        asset_volume += asset_item_volume
            profile_volume += asset_volume
        total_volume += profile_volume

        if profile.name_profile == buyer_profile.name_profile:
            buyer_volume = profile_volume

    # The proportinal volume should be base on the energy contract volume
    try:
        cliq_volume = (buyer_volume/total_volume)*cliq.id_contract.volume_mwm
    except DecimalException:
        cliq_volume = Decimal('0.0')
    return cliq_volume

def get_consumer_volume(id_reference_report, id_company):
    """Returns consumer volume given a reference report id and the consumers company id"""
    return MeteringReportData.objects.get(
        report__id=id_reference_report, 
        id_company__id_company=id_company.id_company
        ).consumption_values.get().total_consumption_loss


def get_local_timezone():
    return pytz.timezone(f'Etc/GMT+{int(time.timezone / 3600)}')


def get_all(objects):
    try:
        response = []
        elements = list(objects.all().values())
        if len(elements) == 0:
            return []

        for element in elements:
            response.append(convert_dict_to_namedtuple(element))
        return response
    except Exception as e:
        logger.error(e)
        raise Exception(e)

def get_one_by_id(element_list, id_number):
    try:
        elements = list(filter(lambda x: x.id == Decimal(str(id_number)), element_list))
        if len(elements) == 0:
            raise Exception('Not found')
        if len(elements) > 1:
            raise Exception('More than one element founded.')

        return elements[0]
    except Exception as e:
        logger.error(f'{str(e)}')
        raise Exception(e)

def get_one_by_property_value(element_list, property_name, value):
    try:
        elements = list(filter(lambda x: getattr(x, property_name) == value, element_list))
        if len(elements) == 0:
            raise Exception('Not found')
        if len(elements) > 1:
            raise Exception('More than one element founded.')

        return elements[0]
    except Exception as e:
        logger.error(f'{str(e)}')
        raise Exception(e)

def get_many_by_property_value(element_list, property_name, value):
    try:
        elements = list(filter(lambda x: getattr(x, property_name) == value, element_list))
        if len(elements) == 0:
            return []

        response = []
        for element in elements:
            response.append(element)
        return response
    except Exception as e:
        logger.error(f'{str(e)}')
        raise Exception(e)

def convert_dict_to_namedtuple(dict_element):
    try:
        return namedtuple('Structure', dict_element.keys())(*dict_element.values())
    except Exception as e:
        logger.error(f'{str(e)}')
        raise Exception(e)
