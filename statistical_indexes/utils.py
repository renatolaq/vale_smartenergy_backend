from django.db.models import Value
from calendar import monthcalendar, weekday, monthrange
from functools import reduce
from workalendar.america import Brazil
from datetime import datetime, date
import pytz, sys, time, unicodedata
from collections import namedtuple
from enum import Enum

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

def get_user_username(request):
    return f'{request.auth.get("cn")} - {request.auth.get("UserFullName")}'

def get_local_timezone():
    return pytz.timezone(f'Etc/GMT+{int(time.timezone / 3600)}')

def strip_accents(s):
   return ''.join(c for c in unicodedata.normalize('NFD', s)
                  if unicodedata.category(c) != 'Mn')


class OldIndexesCheck(Enum):
    UNFINISHED_CHARGEBACK = -1
    NO_CHARGEBACK = 0
    OK = 1

ChargebackCheck = namedtuple('ChargebackCheck', ['status', 'index_name'])