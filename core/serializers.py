from typing import Union
from rest_framework import serializers
from core.models import *
from django.forms.models import model_to_dict
from django.core.serializers.json import DjangoJSONEncoder
from datetime import datetime
from django.utils import timezone
import json
from django.core.exceptions import FieldError
from locales.translates_function import translate_language_error

class LogSerializer(serializers.ModelSerializer):
    class Meta:
        fields = (
            'url', 'id_log', 'field_pk', 'table_name', 'action_type', 'old_value', 'new_value', 'observation',
            'date', 'user')
        model = Log

def generic_insert_user_and_observation_in_self(self, **kwargs):
    if 'context' in kwargs and kwargs['context']['request']._auth:
        self.user = kwargs['context']['request']._auth['cn'] + " - " + kwargs['context']['request']._auth['UserFullName']
        self.observation_log = kwargs['context']['observation_log']
    else:
        self.user = ''
        self.observation_log = ''

def log(instance, pk, log_obj_old: Union[dict, models.Model], log_obj_new: Union[dict, models.Model], user: str, observation_log: str, action:str="UPDATE"):
    try:
        log_old = {}
        if isinstance(log_obj_new, models.Model):
            log_obj_new = model_to_dict(log_obj_new)

        log_new = json.loads(json.dumps(log_obj_new, cls=DjangoJSONEncoder))
        if log_obj_old:
            if isinstance(log_obj_old, models.Model):
                log_obj_old = model_to_dict(log_obj_old)

            log_old = json.loads(json.dumps(log_obj_old, cls=DjangoJSONEncoder))
            for key in log_old.keys():
                if key not in log_new:                    
                    log_new[key] = log_old[key]
                if str(log_new[key]).isdigit and type(log_new[key]) != type(log_old[key]):
                    log_new[key] = str(log_new[key])
                    log_old[key] = str(log_old[key])
        log_old = str(log_old)
        log_new = str(log_new)
        if log_old != log_new:
            send = {"field_pk": pk, "table_name": instance._meta.db_table, "action_type": action,
                    "old_value": str(log_old), "new_value": str(log_new), "user": str(user),
                    "date": datetime.now(tz=timezone.utc), 'observation': observation_log}
            serializer = LogSerializer(data=send)
            if serializer.is_valid():
                serializer.save()
    except Exception:
        pass


def generic_update(model_class, pk, data, user='AnonymousUser', observation_log="", generate_log=True, extra_data_old={}, extra_data_new={}):
    obj_old = model_class.objects.get(pk=pk)
    instance = model_class.objects.get(pk=pk)
    for key, value in data.items():
        field = model_class._meta.get_field(key)
        if not field:
            continue
        if isinstance(field, models.ManyToManyField):
            # can't add m2m until parent is saved
            continue
        elif isinstance(field, models.ForeignKey) and hasattr(value, 'items'):
            rel_instance = generic_update(field.rel.to, value, observation_log, generate_log)
            setattr(instance, key, rel_instance)
        else:
            setattr(instance, key, value)
    instance.save()
    # now add the m2m relations
    for field in model_class._meta.many_to_many:
        if field.name in data and hasattr(data[field.name], 'append'):
            for obj in data[field.name]:
                rel_instance = generic_update(field.rel.to, obj, observation_log, generate_log)
                getattr(instance, field.name).add(rel_instance)

    if generate_log:
        log(model_class, pk, {**model_to_dict(obj_old), **extra_data_old}, 
            {**model_to_dict(instance), **extra_data_new}, user, observation_log)
    return instance


def generic_validation_status(pk, table_name, kwargs, self):
    array_dependence = []
    queryset=[]
    for instance in kwargs.keys():
        try:
            queryset = instance.objects.filter(**{kwargs[instance]: pk, 'status': 'S'})
        except FieldError:
            queryset = instance.objects.filter(**{kwargs[instance]: pk})
        if len(queryset) > 0:
            array_dependence.append(translate_language_error(instance._meta.db_table, self.context['request']))
    if len(array_dependence) > 0:
        return (translate_language_error('error_status', self.context['request']) + " {}")\
            .format(
                ', '.join(array_dependence)
            )
    return 'S'

def generic_validation_changed(pk, table_name, kwargs, request):
    relateds=[]
    for instance, value in kwargs.items():
        try:
            if instance.objects.filter(**{value:pk, 'status':'S'}):
                relateds.append(str(instance._meta.db_table))
        except FieldError:
            if instance.objects.filter(**{value:pk}):
                relateds.append(str(instance._meta.db_table))
    if relateds: 
        status_message = translate_language_error('error_change', request)
        for item_related in relateds:
            status_message = status_message+" "+item_related+","
        return status_message
    return "S"

def is_valid_str_time(str_t):
    # h:mm:ss ~ hhhh:mm:ss
    if len(str_t.split(':')) != 3:
        return False
    try:
        hh, mm, ss = str_t.split(':')
        return len(mm) == 2 and len(ss) == 2\
        and int(hh) >= 0 and int(mm) >= 0 and int(mm) <= 59 and int(ss) >= 0 and int(ss) <= 59
    except:
        return False


def str_time_to_seconds(str_t):
    # h:mm:ss ~ hhhh:mm:ss
    hh, mm, ss = map(lambda x: int(x), str_t.split(':'))
    return (hh * 3600) + (mm * 60) + ss

def seconds_to_str_time(seconds):
    hh = int(seconds / 3600)
    hh_seconds = hh * 3600
    mm = int((seconds - hh_seconds) / 60)
    mm_seconds = mm * 60
    ss = int(seconds - hh_seconds - mm_seconds)
    return '{}:{:02d}:{:02d}'.format(hh, mm, ss)