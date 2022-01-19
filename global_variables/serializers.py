from rest_framework import serializers
from django.db.models import F, When, Case, Q, Value, Count
from django.db import transaction, DatabaseError
from .models import GlobalVariable, State, Variable, Unity, Log
from rest_framework.exceptions import ValidationError, APIException
from django.utils.log import logging

from decimal import Decimal


class ConflictError(APIException):
    def __init__(self, detail, code):
        super().__init__(detail=detail, code=code)


class GlobalVariablesListSerializer(serializers.ListSerializer):
    def update_icms(self, icms_variables):
        with transaction.atomic():
            for global_variable in icms_variables:
                GlobalVariable.objects.filter(id=global_variable['id']).update(
                state = Case(When(state=global_variable['state'], then=Value(global_variable['state'])), default=State.objects.filter(id = global_variable['state']).annotate(counter = Count('global_variable')).filter(Q(counter=0) | Q(global_variable__id=global_variable['id'])).first().id),
                value = global_variable['value']
                )

    def update_ipca(self, ipca_variables):
        with transaction.atomic():
            for global_variable in ipca_variables:
                GlobalVariable.objects.filter(variable__name__exact=global_variable['variable']).update(
                month = global_variable['month'],
                year = global_variable['year'],
                value = global_variable['value']
                )

    def update(self, instance, validated_data):
        try:
            self.update_icms(filter(lambda global_variable: global_variable['variable'] == 'ICMS', validated_data))
            self.update_ipca(filter(lambda global_variable: global_variable['variable'] == 'IPCA', validated_data))
        except Exception as some_erro:
            raise ConflictError(f'Já há um ICMS cadastrado para o estado informado. {some_erro}', 409)


class LogSerializer(serializers.ModelSerializer):

    class Meta:
        model = Log
        fields = ['id', 'table_name', 'action_type', 'field_pk', 'old_value', 'new_value', 'observation', 'date', 'user']


class LogTaxesTariffsSerializer(serializers.ModelSerializer):
    cofins = serializers.CharField()
    dollar_exchange_rate = serializers.CharField()
    pis = serializers.CharField()
    fixed_apportionment_rate = serializers.CharField()
    cofins_changed = serializers.BooleanField()
    dollar_exchange_rate_changed = serializers.BooleanField()
    pis_changed = serializers.BooleanField()
    fixed_apportionment_rate_changed = serializers.BooleanField()

    class Meta:
        model = Log
        fields = ['id', 'table_name', 'action_type', 'observation', 'date', 'user',
        'cofins', 'dollar_exchange_rate', 'pis', 'fixed_apportionment_rate',
        'cofins_changed', 'dollar_exchange_rate_changed', 'pis_changed', 'fixed_apportionment_rate_changed',]


class LogICMSSerializer(serializers.ModelSerializer):
    states = serializers.SerializerMethodField()
    class Meta:
        model = Log
        fields = ['id', 'table_name', 'action_type', 'observation', 'date', 'user', 'states']

    def get_states(self, serialized_object):
        new_icms_log = eval(serialized_object.new_value)['states']
        old_icms_log = eval(serialized_object.old_value)['states']
        for i, log in enumerate(new_icms_log):
            log['old_value'] = old_icms_log[i]['value']
        return LogICMSStateSerializer(new_icms_log, many=True).data


class LogICMSStateSerializer(serializers.Serializer):
    state = serializers.SerializerMethodField()
    value = serializers.SerializerMethodField()
    changed = serializers.SerializerMethodField()

    def get_state(self, serialized_object):
        return serialized_object['state']

    def get_value(self, serialized_object):
        return serialized_object['value']

    def get_changed(self, serialized_object):
        return serialized_object['value'] != serialized_object['old_value']


class GlobalVariablesSerializer(serializers.ModelSerializer):
    variable_name = serializers.SerializerMethodField()
    state_name = serializers.SerializerMethodField()
    unity_type = serializers.SerializerMethodField()
    formated_value = serializers.SerializerMethodField()

    def get_formated_value(self, serialized_object):
        return f'{serialized_object.value:.4f}'

    def get_variable_name(self, serialized_object):
        return serialized_object.variable_name

    def get_state_name(self, serialized_object):
        return serialized_object.state_name

    def get_unity_type(self, serialized_object):
            return serialized_object.unity_type
    class Meta:
        list_serializer_class = GlobalVariablesListSerializer
        model = GlobalVariable
        fields = ['id', 'variable', 'unity', 'state', 'variable_name', 'value', 'formated_value', 'month', 'year', 'state_name', 'unity_type', 'marketing', 'status']


class StateSerializer(serializers.ModelSerializer):
    class Meta:
        model = State
        fields = '__all__'