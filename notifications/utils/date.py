from dateutil.rrule import rrule
from dateutil.parser import isoparse
from datetime import datetime, timedelta, date


def transform_django_datetime(value_string):
    date_string = value_string.split(":")[1]
    result = datetime.strptime(date_string, "%d/%m/%Y")

    return result


def add_day_to_date(date, days):
    new_date = date + timedelta(days=days)

    return new_date


def check_pass_date_condition(condition, date_start, current_date, condition_cont=1):
    matches = list(
        rrule(
            condition, interval=condition_cont, dtstart=date_start, until=current_date
        )
    )

    for match in matches:
        if isoparse(str(match)) == isoparse(str(current_date)):
            return True

    return False


def check_if_is_29_february(date):
    return date.month == 2 and date.day == 29
