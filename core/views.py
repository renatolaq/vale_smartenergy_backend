import ast
import collections
import decimal
import json
import os
import re
import threading
import uuid
from numbers import Number
from ast import literal_eval
from calendar import Calendar, monthrange
from datetime import date, datetime, timedelta
from django.db.models.query import QuerySet

import holidays
import requests
from django.conf import settings
from django.core.paginator import PageNotAnInteger, Paginator, EmptyPage
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Q
from django.forms import model_to_dict
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from translate import Translator

from SmartEnergy.auth import is_administrator
from SmartEnergy.settings import PME_APP_URL, PME_APP_HOST
from core.models import *
from core.serializers import LogSerializer
from gauge_point.models import GaugePoint, SourcePme
from locales.translates_function import get_language
from .utils.pme_groups import pme_group
from .utils.quantity import quantity_list


@api_view(['GET'])
def validated_code_ccee(request, code_ccee_request, type_request, format=None):
    if type_request == "A.P":
        type_request = "A/P"

    if CceeDescription.objects.filter(code_ccee=code_ccee_request, type=type_request, status='S').exclude(
            id_ccee=request.query_params.get('id_ccee', None)):
        translator = Translator(to_lang=request.META['HTTP_ACCEPT_LANGUAGE'])
        translation = translator.translate("code_ccee already cadastred")
        return Response({translation + " ( %s )" % type_request}, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response(status=status.HTTP_200_OK)


def generic_log_search(pk, **kwargs):
    """
    :param kwargs:

    This kwargs need 4 keys.
    - core: You need to pass the core model as value, only one value. Not null
    - core_pk: You need to pass the model's primary key as value, only one value. Not null
    - core+: This key needs an array where each position must be a dict.
             In each dict you need to input only one key/value.
             The key is a model and the value is model's related_name about field. Allows an empty array
    - child: You need to input a array with models. Allows an empty array

    :return: dictionary with all data serializer
    """
    core_data = json.loads(json.dumps(model_to_dict(kwargs['core'].objects.get(pk=pk)), cls=DjangoJSONEncoder))
    kwargs_core = {kwargs['core']: core_data[kwargs['core_pk']]}
    for data in kwargs['core+']:
        for instance in data.keys():
            try:
                kwargs_core[instance] = json.loads(
                    json.dumps(model_to_dict(instance.objects.get(pk=core_data[data[instance]])),
                               cls=DjangoJSONEncoder))[instance._meta.pk.name]
            except instance.DoesNotExist:
                pass
            except KeyError:
                try:
                    kwargs_core[instance] = json.loads(
                        json.dumps(model_to_dict(instance.objects.get(**{data[instance]: pk})),
                                   cls=DjangoJSONEncoder))[instance._meta.pk.name]
                except:
                    pass
            except Exception:
                pass

    kwargs_log = {"counts": {}}
    for kwarg in kwargs_core:
        array = []
        for log in Log.objects.filter(table_name=kwarg._meta.db_table, field_pk=kwargs_core[kwarg]).values():
            array.append(json.loads(json.dumps(log, cls=DjangoJSONEncoder)))

        kwargs_log[kwarg._meta.db_table] = array

    for instance in kwargs['child']:
        array = []
        for log in Log.objects.filter(table_name=instance._meta.db_table).values():
            old_value = literal_eval(log['old_value'])
            new_value = literal_eval(log['new_value'])
            if old_value:
                if int(old_value[kwargs['core_pk']]) == int(core_data[kwargs['core_pk']]):
                    array.append(json.loads(json.dumps(log, cls=DjangoJSONEncoder)))
            elif int(new_value[kwargs['core_pk']]) == int(core_data[kwargs['core_pk']]) and \
                    log['action_type'] == "INSERT":
                array.append(json.loads(json.dumps(log, cls=DjangoJSONEncoder)))
        kwargs_log[instance._meta.db_table] = array
    for key in kwargs_log:
        if key != "counts":
            total = len(kwargs_log[key])
            kwargs_log["counts"][key] = {"total": total,
                                         "values": kwargs_log[key][total - 1]["new_value"]
                                         if total > 0 else "{}"}
    return kwargs_log


class LogViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Log manipulation
    """
    queryset = Log.objects.all()
    serializer_class = LogSerializer

def generic_queryset_filter_ex(request, model, **kwargs) -> QuerySet:
    """
        :param request:
        :param model:
        :param kwargs:

        This kwargs need 3 keys.
        - request: You need to pass request param of your view
        - model: You need to pass the core model as value, only one value
        - kwargs: You need to pass a dictionary, where keys are the request query parameters and values
                  are the method to filter on the query set

        :return: filtered queryset
    """
    queryset: QuerySet = getattr(model, "objects", model).all()
    request_kwargs = {k: v[0] if len(v) == 1 else v for k, v in request.query_params.lists()}
    request_kwargs['filter_date_range'] = ""
    filter_params = Q()

    for key in request_kwargs.keys():
        if key in kwargs and key != 'filter_date_range':
            field = kwargs[key]
            value = request_kwargs[key]
            if isinstance(field, collections.Mapping):
                if field.get('allow_null', None):
                    value = value if value != 'null' else None
                if field.get('converter', None):
                    if value is not None:
                        value = field['converter'](value)
                field = field['field']
            filter_params.add(Q(**{field: value}), Q.AND)
        elif key in kwargs and key == 'filter_date_range':
            for k in kwargs[key].keys():
                value = kwargs[key][k]
                filter_params.add(Q(**{k: value}), Q.AND)
    
    return queryset.filter(filter_params)


def generic_queryset_filter(request, model, key_return, **kwargs):
    """
        :param request:
        :param model:
        :param key_return:
        :param kwargs:

        This kwargs need 4 keys.
        - request: You need to pass request param of your view
        - model: You need to pass the core model as value, only one value
        - key_return: You need to pass the variable that you will use to serializer. Not null
        - kwargs: You need to pass a dictionary, where keys are the request query parameters and values
                  are the method to filter on the query set

        :return: array with all ids to serializer
    """
    array = []
    for query in generic_queryset_filter_ex(request, model, **kwargs):
        args = json.loads(json.dumps(model_to_dict(query), cls=DjangoJSONEncoder))
        if key_return in args:
            array.append(args[key_return])

    return array

def generic_paginator(request, queryset):
    page = 1
    try:
        page_size = request.query_params.get('page_size') or 10
        if page_size == "all":
            page_size = len(queryset) if queryset else 1
        paginator = Paginator(queryset, page_size)
    except Exception:
        paginator = Paginator(queryset, 10)
    try:
        page = request.query_params.get('page') or 1
        data = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        data = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999),
        # deliver last page of results.
        data = paginator.page(paginator.num_pages)
    page_count = 1
    page_next = 1
    page_previous = 1
    page = paginator.get_page(page)
    try:
        page_count = paginator.count
        page_next = page.next_page_number() if page.has_next() else None
        page_previous = page.previous_page_number() if page.has_previous() else None
    except Exception:
        pass
    return data, page_count, page_next, page_previous


def generic_detail_log(kwargs_edited, log):
    """

    :param kwargs_edited:
    :param log:

    - Log: This param is log returned in generic_log_search
    - kwargs_edited:
    This kwargs need:
        core: This key contains an array with models core that exists in log
        search: This key is connected to core. Here, you need to pass dicts that keys is a model and value is {}
        search_dependent: This key is connected to core and search. Here, you need to pass dicts that keys is a model
                          and value is {key[search_model._meta.db_table]: value[field to join]}

    :return: log to exhibition
    """
    array = []
    for table in kwargs_edited['core']:
        if table._meta.db_table in log:
            for l in log[table._meta.db_table]:
                old_value = literal_eval(l['old_value'])
                new_value = literal_eval(l['new_value'])
                for search_key in kwargs_edited['search']:
                    if search_key in new_value:
                        kwargs_generic_new = {}
                        kwargs_generic_old = {}
                        for instance in kwargs_edited['search'][search_key].keys():
                            if new_value[search_key] is not None:
                                r = model_to_dict(instance.objects.get(pk=new_value[search_key]))

                                kwargs_generic_new[instance._meta.db_table] = json.loads(
                                    json.dumps(r, cls=DjangoJSONEncoder))
                                if search_key in old_value:
                                    if old_value[search_key] is not None:
                                        r = model_to_dict(instance.objects.get(pk=old_value[search_key]))
                                        kwargs_generic_old[instance._meta.db_table] = json.loads(
                                            json.dumps(r, cls=DjangoJSONEncoder))
                        if search_key in kwargs_edited['search_dependent']:
                            for instance in kwargs_edited['search_dependent'][search_key].keys():
                                for n in kwargs_edited['search_dependent'][search_key][instance].keys():
                                    r = model_to_dict(instance.objects.get(
                                        pk=kwargs_generic_new[n][
                                            kwargs_edited['search_dependent'][search_key][instance][n]]))
                                    kwargs_generic_new[instance._meta.db_table] = json.loads(
                                        json.dumps(r, cls=DjangoJSONEncoder))
                                    if search_key in old_value:
                                        for n in kwargs_edited['search_dependent'][search_key][instance].keys():
                                            r = model_to_dict(instance.objects.get(
                                                pk=kwargs_generic_old[n][
                                                    kwargs_edited['search_dependent'][search_key][instance][n]]))
                                            kwargs_generic_old[instance._meta.db_table] = json.loads(
                                                json.dumps(r, cls=DjangoJSONEncoder))
                        if kwargs_generic_new:
                            array.append(
                                {'id_log': l['id_log'], 'old_value': kwargs_generic_old,
                                 'new_value': kwargs_generic_new})

    log['DETAILS'] = array
    return log


def generic_move_itens_log(array, kwargs, log_destroy):
    """

        :param array:
        :param kwargs:
        :param log_destroy:

        - array: Table that will be detail on kwargs
        - kwargs: Log that create to generic_log_search
        - log_destroy: Log that create to generic_log_search, without fields normal.

        :return: log to exhibition
        """
    for table in array:
        k, v = list(table)[0], table[list(table)[0]]
        for index in range(len(kwargs[k])):
            pk = int(literal_eval(kwargs[k][index]['new_value'])[v])
            array = []
            for index_destroy in range(len(log_destroy)):
                pk_destroy = int(log_destroy[index_destroy]['field_pk'])
                if pk == pk_destroy:
                    array.append(log_destroy[index_destroy])
            kwargs[k][index]['SEASONALITY'] = array
    return kwargs


def generic_log_search_basic(logs):
    def list_replace(list_to_replace):
        for item in list_to_replace:
            if type(item['date']) is not datetime:
                if "." not in item['date']:
                    item['date'] = item['date'].replace("Z", ".0Z")
                item['date'] = datetime.strptime(item['date'], '%Y-%m-%dT%H:%M:%S.%fZ')
            item['new_value'] = ast.literal_eval(item['new_value'])
            item['old_value'] = ast.literal_eval(item['old_value'])

        for item in list_to_replace:
            if item['action_type'] == 'UPDATE':
                for field, value in item['new_value'].items():
                    is_equal = item['old_value'][field] == value
                    if not is_equal and is_number_or_str_number_representation(item['old_value'][field]) and is_number_or_str_number_representation(value):
                        is_equal = decimal.Decimal(item['old_value'][field]) == decimal.Decimal(value)
                    if not is_equal \
                        and isinstance(item['old_value'][field], list) \
                        and isinstance(value, list):
                        list_old = set(map(lambda x: decimal.Decimal(x) if
                            is_number_or_str_number_representation(x) else x, item['old_value'][field]))
                        list_new = set(map(lambda x: decimal.Decimal(x) if
                            is_number_or_str_number_representation(x) else x, value))
                        is_equal = list_old == list_new


                    
                    if not is_equal:
                        item['new_value'][field] = {}
                        item['new_value'][field]['value'] = value
                        item['new_value'][field]['until'] = next(
                            (x['date'] for x in list_to_replace
                             if
                             x['date'] > item['date'] and x['field_pk'] == item['field_pk'] and x['new_value'][field] !=
                             x['old_value'][field]), 'NOW')

    def approx_item(list_items, approx_date):
        try:
            list_items_aux = list(
                filter(lambda a:
                       a['date'] - timedelta(seconds=4) < approx_date < a['date'] + timedelta(seconds=4),
                       list_items)
            )
            if len(list_items_aux) > 1:
                return list_items_aux
            else:
                return list_items_aux[-1]
        except IndexError:
            try:
                return {
                    **list(filter(lambda x: x['date'] - timedelta(seconds=4) <= approx_date, list_items))[-1],
                    'action_type': 'NONE'
                }
            except IndexError:
                return {}

    logs_dates = []
    for log in logs:
        if log != 'counts':
            list_replace(logs[log])
            if logs_dates:
                logs_dates += list(map(lambda x: x['date'], logs[log]))
            else:
                logs_dates = list(map(lambda x: x['date'], logs[log]))

    logs_dates = sorted(logs_dates)
    i = 1
    while i < len(logs_dates):
        if logs_dates[i - 1] - timedelta(seconds=4) < logs_dates[i] < logs_dates[i - 1] + timedelta(seconds=4):
            logs_dates.pop(i)
        else:
            i += 1

    logs_merged = []
    for date in logs_dates:
        logs_merged.append({'date': date})
        for log in logs:
            if log != 'counts':
                logs_merged[len(logs_merged) - 1][log] = approx_item(logs[log], date)
                if type(logs_merged[len(logs_merged) - 1][log]) == list:
                    if logs_merged[len(logs_merged) - 1][log][-1]['action_type'] != 'NONE':
                        logs_merged[len(logs_merged) - 1]['user'] = logs_merged[len(logs_merged) - 1][log][-1]['user']
                        logs_merged[len(logs_merged) - 1]['observation'] = logs_merged[len(logs_merged) - 1][log][-1][
                            'observation']
                elif type(logs_merged[len(logs_merged) - 1][log]) == dict and len(
                        logs_merged[len(logs_merged) - 1][log]):
                    if logs_merged[len(logs_merged) - 1][log]['action_type'] != 'NONE':
                        logs_merged[len(logs_merged) - 1]['user'] = logs_merged[len(logs_merged) - 1][log]['user']
                        logs_merged[len(logs_merged) - 1]['observation'] = logs_merged[len(logs_merged) - 1][log][
                            'observation']
    return sorted(logs_merged, key=lambda x: x['date'], reverse=True)


def alter_number(value_format):
    def format_number(data_format):
        conversao_numeros = [".", ","]

        array_of_number = str(data_format).split(".")
        posiPonto = len(array_of_number[0]) % 3
        if posiPonto == 0:
            posiPonto = 3
        format_finaly = ""
        for char in array_of_number[0]:
            if posiPonto != 0:
                format_finaly += char
                posiPonto -= 1
            else:
                format_finaly += conversao_numeros[0]
                format_finaly += char
                posiPonto = 2

        format_finaly += conversao_numeros[1] + array_of_number[1]
        return format_finaly

    if value_format:
        return format_number(value_format)
    else:
        return ""


def delete_file(path):
    file_path = os.path.join(settings.MEDIA_ROOT, path)
    if os.path.exists(file_path):
        os.remove(file_path)
    unique_name = path[:path.find(os.path.sep)]
    file_dir = os.path.join(settings.MEDIA_ROOT, unique_name)
    if os.path.exists(file_dir):
        os.rmdir(file_dir)

def save_file(file):
    unique_name = str(uuid.uuid4())
    directory = os.path.join(settings.MEDIA_ROOT, unique_name)
    os.makedirs(directory, exist_ok=True)
    filename = os.path.basename(file.name)
    locate = os.path.join(directory, filename)
    destination = open(locate, 'wb+')
    destination.write(file.read())
    destination.close() 
    return os.path.join(unique_name, filename)


def generic_subquery(query_params, kwargs):
    filter_params = Q()
    for k, field_param in kwargs.items():
        value_param = query_params.get(k, None)
        if value_param is not None and value_param.strip():
            dct = {field_param: value_param}
            filter_params.add(Q(**dct), Q.AND)

    return filter_params


def get_holidays(country):
    _holidays = holidays.BR()
    if country == 'CA':
        _holidays = holidays.CA()
    if country == 'UK':
        _holidays = holidays.UK()
    return _holidays


def get_peek_time_logic(year, month, country):
    days = []
    cal = Calendar()
    _holidays = get_holidays(country)

    for week in cal.monthdayscalendar(year, month):

        # Total days of the month
        # total = list(filter(lambda a: a != 0, week))

        # Remove Saturday and Sunday
        util_days = list(filter(lambda a: a != 0, week[:5]))

        for day in util_days:
            _day = date(year, month, day)

            # The day is a holiday
            if _day in _holidays:
                # If 'Quaresma' then not consider as a holiday
                if 'Quaresma' not in _holidays[_day]:
                    continue

            # Only add days without holidays
            days.append(day)

    total_days = monthrange(year, month)[1]
    total_hours = total_days * 24
    peek_time = len(days) * 3
    off_peek_time = total_hours - peek_time

    resp = {'country': country,
            'month': month,
            'year': year,
            'total_days_month': monthrange(year, month)[1],
            'working_days_month': len(days),
            'peek_time': peek_time,
            'off_peek_time': off_peek_time
            }

    return resp


@api_view(['GET'])
def get_peek_time(request, year, month, country):
    resp = get_peek_time_logic(year, month, country)
    return Response(resp, status=status.HTTP_200_OK)


def validates_data_used_file(data, location, type, qtd=4):  # type==> 0=string, 1=number, 2=number format for pdf
    retorno = data
    for key in location:
        if key in retorno and retorno[key]:
            retorno = retorno[key]
        else:
            return ""
    try:
        if type == 0:
            return str(retorno)
        elif type == 1:
            return float(retorno)
        elif type == 2:
            retorno = "%.{}f".format(qtd) % float(retorno)
            return alter_number(retorno)
    except:
        return 0


def check_user_pme(request):
    access_level = 0
    group_pme = {'groups': [], 'access_level': access_level, 'call_api': False}
    group_list = request.auth['groupMembership']
   
    for g in group_list:
        group_perm = g.split(',')[0].split('=')[1].split('_')
        if len(group_perm) >= 2:
            sap = group_perm[0]
            perm = group_perm[1]
            if "PME" in perm:
                if perm == "VISPME":
                    group_pme['call_api'] = True
                    group_pme['groups'].append(pme_group[sap])
                    if access_level <= 2:
                        access_level = 2

                if perm == "EPME":
                    group_pme['call_api'] = True
                    if is_administrator(request.user):
                        group_pme['groups'].append("Global")
                        access_level = 5
                    else:
                        group_pme['groups'].append(pme_group[sap])
                        if access_level <= 4:
                            access_level = 4

    group_pme['access_level'] = str(access_level)
    return group_pme


# Authentication PME
@api_view(['POST'])
def get_pme_token(request):
    try:
        group_pme = check_user_pme(request)
        if group_pme['call_api']:

            _user = request.auth['sub']
            data = {'UserName': _user,
                    'AccessLevel': group_pme['access_level'],
                    'Groups': group_pme['groups'],
                    'Token': 'l9RoaczivJ4tYhxU2WGBDLVQvXoO3JNXxBgokEeU9ZxqXM3sAo77zleKhNTrf'}

            url = PME_APP_HOST + "/iondatauser/systemdataservice/singleuser"
            _resp = requests.get(url, data=data, verify=False)

            resp_groups = _resp.text.replace("\"", "").split(' :: ')
            token = resp_groups[0]
            error_log = ''

            if len(resp_groups) == 2:
                if resp_groups[1].strip() != '':
                    error_log = resp_groups[1]

            resp = {"host": PME_APP_URL,
                    "url": "/systemdataservice/security/LogOnWithSingleUseToken",
                    'token': token,
                    'error': error_log}

            lang = get_language(request)
            data_lang = {'UserName': _user,
                         'Language': lang,
                         'Token': 'l9RoaczivJ4tYhxU2TOBFLVQvXoO3JNXxBgokEeU9ZxqXM3sAo77zleKhNTrf'}

            url_lang = PME_APP_HOST + "/iondatauser/systemdataservice/singleuserlanguage"
            _resp_lang = requests.post(url_lang, data=data_lang, verify=False)
            resp_lang = _resp_lang.text.replace("\"", "")

            return Response(resp, status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_403_FORBIDDEN)
    except Exception as e:
        resp = {'error': e.args}
        return Response(resp, status=status.HTTP_400_BAD_REQUEST)


# Change language PME
@api_view(['POST'])
def change_lang_pme(request, lang):
    try:

        user_pme = check_user_pme(request)
        if user_pme['call_api']:
            _user = request.auth['sub']
            data = {'UserName': _user,
                    'Language': lang,
                    'Token': 'l9RoaczivJ4tYhxU2TOBFLVQvXoO3JNXxBgokEeU9ZxqXM3sAo77zleKhNTrf'}

            url_pme = PME_APP_HOST + "/iondatauser/systemdataservice/singleuserlanguage"
            _resp = requests.post(url_pme, data=data, verify=False)
            resp = {'resp': _resp.text.replace("\"", "")}
            return Response(resp, status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_403_FORBIDDEN)

    except Exception as e:
        resp = {'error': e.args}
        print(e.args)
        return Response(resp, status=status.HTTP_400_BAD_REQUEST)


def call_api_delete_user(_user):
    _data = {'UserName': _user,
             'Token': 'l9RoaczivJ4tYhxUTOBFLVQvXoO3JNXxBgokEeU9ZxqXM3sAo77OPTKhNTrf'}

    url = PME_APP_HOST + "/iondatauser/systemdataservice/singleuser"
    _resp = requests.post(url, data=_data, verify=False)


# Delete User PME
@api_view(['POST'])
def logout_pme(request):
    try:
        _user = request.auth['sub']
        user_pme = check_user_pme(request)
        if user_pme['call_api']:
            api = threading.Thread(target=call_api_delete_user, args=(_user,))
            api.start()
            resp = {"data": 'Usuário deletado com sucesso.'}
            print(resp)
            return Response(resp, status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_403_FORBIDDEN)

    except Exception as e:
        resp = {'error': e.args}
        return Response(resp, status=status.HTTP_400_BAD_REQUEST)

def is_number_or_str_number_representation(value):
    return isinstance(value, Number) or \
        (isinstance(value, str) and re.compile('^\d+?(\.\d+)?$').match(value))

def only_number(lst):
    return filter(is_number_or_str_number_representation, lst)


def get_source_pme_name(id_gauge_point):
    try:
        gauge_point = GaugePoint.objects.get(pk=int(id_gauge_point))
        source_pme = SourcePme.objects.get(pk=str(gauge_point.id_source_id))
        return source_pme.display_name
    except Exception as e:
        print(e.args)
        return ''


def format_formula(f):

    dic = {'labels': []}

    c = ''
    formula = ''
    f += '@'
    f = f.replace("'", "\"")

    while c != '@':

        c = f[0]
        if c in ['+', '-', '*', '/', '(', ')']:
            formula += c
            f = f[1:]

        elif c == '{':
            i = f.find('}')
            dic_str = f[:i + 1]
            f = f[len(dic_str):]
            dic_aux = json.loads(dic_str)
            source_id = dic_aux['id']

            if source_id not in dic:
                source_name = get_source_pme_name(source_id)
                dic['labels'].append(dic_aux['key'])
                dic[source_id] = {'name': source_name, 'label': dic_aux['key']}
            formula += dic_aux['key']
        else:
            _list = f.replace("@","")
            if len(_list) > 0:
                number = str(_list[0])
                formula += number
                f = f[len(number):]

    return formula, dic


def insert_virtual_meter(kpi_formulae, id_destination, id_ec):
    month_to_date = 6
    utc_creation = datetime.now(tz=timezone.utc).replace(microsecond=0)
    destination = get_source_pme_name(id_destination)

    if 'VIRTUAL' in destination.upper():

        formulae, sources = format_formula(kpi_formulae)

        ec = EnergyComposition.objects.get(pk=id_ec)
        list_kpi = []
        for quantity in quantity_list:

            for info in sources:

                if info == 'labels':
                    continue

                label = sources[info]['label'].strip()
                source_name = sources[info]['name']
                
                kpi = KpiVirtualMeter()
                kpi.label = label.strip()
                kpi.formula = formulae.strip()
                kpi.id_energy_composition = ec
                kpi.kpi_source = destination
                kpi.quantity_id = quantity['origem']
                kpi.kpi_quantity = quantity['destino']
                kpi.source_id = source_name
                kpi.type = month_to_date
                kpi.utc_creation = utc_creation

                list_kpi.append(kpi)
        try:
            if len(list_kpi) > 0:
                KpiVirtualMeter.objects.bulk_create(list_kpi)
        except Exception as ex:
            # Erro ao inserir as informações no banco de dados
            print(ex.args)


def delete_vm(list_label, ec):

    for label in list_label:
        KpiVirtualMeter.objects.filter(id_energy_composition=ec, label=label).delete()


def add_vm(list_label, sources, destination, utc_creation, formula, ec):

    source_name = ''
    month_to_date = 6

    list_kpi = []
    for label in list_label:
        for quantity in quantity_list:

            for info in sources:
                if info == 'labels':
                    continue

                label_aux = sources[info]['label'].strip()
                if label_aux == label:
                    source_name = sources[info]['name']
                    break

            kpi = KpiVirtualMeter()
            kpi.label = label.strip()
            kpi.formula = formula.strip()
            kpi.id_energy_composition = ec
            kpi.kpi_source = destination
            kpi.quantity_id = quantity['origem']
            kpi.kpi_quantity = quantity['destino']
            kpi.source_id = source_name
            kpi.type = month_to_date
            kpi.utc_creation = utc_creation
            list_kpi.append(kpi)
    try:
        if len(list_kpi) > 0:
            KpiVirtualMeter.objects.bulk_create(list_kpi)
    except Exception as ex:
        # Erro ao inserir as informações no banco de dados
        print(ex.args)


def update_vm(sources, destination, utc_creation, formula, ec, list_label=None):
 
    if list_label is None:
        list_label = []

    month_to_date = 6
    if len(list_label) == 0:
        kpi_virtual_meter = KpiVirtualMeter.objects.filter(id_energy_composition=ec)
    else:
        kpi_virtual_meter = KpiVirtualMeter.objects.filter(id_energy_composition=ec, label__in=list_label)

    for vm in kpi_virtual_meter:

        # update formula
        if vm.formula != formula.strip():
            vm.formula = formula.strip()

        # udate kpisource
        if vm.kpi_source != destination.strip():
            vm.kpi_source = destination.strip()

        # update sourceid
        
        for info in sources:

            if info == 'labels':
                continue

            if sources[info]['label'] == vm.label.strip():
                source_name = sources[info]['name'].strip()
                if vm.source_id != source_name:
                    vm.source_id = source_name
                break

        vm.utc_creation = utc_creation
        vm.type = month_to_date
        vm.save()


def update_virtual_meter(kpi_formulae, id_destination, id_ec):

    utc_creation = datetime.now(tz=timezone.utc).replace(microsecond=0)
    destination = get_source_pme_name(id_destination)

    if 'VIRTUAL' in destination.upper():

        formulae, sources = format_formula(kpi_formulae)
        update_labels = set(sources['labels'])
        old_labels = set(list(KpiVirtualMeter.objects.values_list('label', flat=True).filter(id_energy_composition=int(id_ec))))

        ec = EnergyComposition.objects.get(pk=id_ec)
        # Se tem o mesmo numero de labels, apenas faz update
        if len(update_labels) == len(old_labels):
            update_vm(sources, destination, utc_creation, formulae, ec)
        else:
            # Se a lista atual eh menor que a antiga, foram removidos labels
            if len(update_labels) < len(old_labels):
                _list = list(old_labels.difference(update_labels))
                if len(_list) > 0:
                    delete_vm(_list, ec)

            # Se a lista atual eh maior que a antiga, foram adicionados labels
            if len(update_labels) > len(old_labels):
                _list = list(update_labels.difference(old_labels))
                if len(_list) > 0:
                    add_vm(_list, sources, destination, utc_creation, formulae, ec)

            # update dos labels comuns aos dois conjuntos
            _list = list(set(update_labels).intersection(set(old_labels)))
            if len(_list) > 0:
                update_vm(sources, destination, utc_creation, formulae, ec, _list)
