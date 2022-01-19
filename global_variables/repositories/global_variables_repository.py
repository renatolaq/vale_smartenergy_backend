from django.db.models import F, Value, DecimalField, CharField
from django.utils.text import slugify
from ..serializers import (GlobalVariablesSerializer, StateSerializer, LogSerializer, LogTaxesTariffsSerializer,
                           LogICMSSerializer)
from ..models import GlobalVariable, Unity, Variable, State, Log
from decimal import Decimal
import locale
import unicodedata


def insert_log_repository(field_pk, table_name, action_type, new_value, old_value, user, observation):
    new_log = LogSerializer(data={'field_pk':field_pk, 'table_name':table_name, 'action_type':action_type, 'new_value':str(new_value), 'old_value':str(old_value), 'observation':observation, 'user':user}, many=False) 
    if new_log.is_valid(True):
        new_log.save()


def get_states_repository():
    queryset = State.objects.all()
    serialized_state = StateSerializer(queryset, many=True)
    return serialized_state.data


def get_icms_logs_repository():
    queryset = Log.objects.filter(observation='ICMS Global Variable').order_by('-date')
    serialized_logs = LogICMSSerializer(queryset, many=True)
    return serialized_logs.data


def get_taxes_tariffs_logs_repository():
    TAXES_AND_TARIFFS_TRANSLATION = {
        'PIS': 'PIS',
        'COFINS': 'COFINS',
        'COTAÇÃO DO DÓLAR': 'DOLLAR EXCHANGE RATE',
        'TARIFA FIXA DE RATEIO': 'FIXED APPORTIONMENT RATE',
    }
    TAXES_AND_TARIFFS = list(TAXES_AND_TARIFFS_TRANSLATION.keys())
    slugified_variables = {variable: slugify(strip_accents(TAXES_AND_TARIFFS_TRANSLATION[variable])).replace('-','_') for variable in TAXES_AND_TARIFFS}
    variable_ids = {variable: GlobalVariable.objects.get(variable__name=variable).id for variable in TAXES_AND_TARIFFS}
    queryset = Log.objects.filter(observation='Taxe and Tariff Global Variable')
    variable_querysets = {variable: queryset.filter(field_pk=variable_ids[variable]).order_by('-date') for variable in TAXES_AND_TARIFFS}
    final_queryset = variable_querysets[TAXES_AND_TARIFFS[0]].annotate(
        **{slugified_variables[variable]: Value('0.0', output_field=DecimalField()) for variable in TAXES_AND_TARIFFS},
        **{f'{slugified_variables[variable]}_changed': Value('', output_field=CharField()) for variable in TAXES_AND_TARIFFS}
    )

    for i, log in enumerate(final_queryset):
        for variable in TAXES_AND_TARIFFS:
            current_log = variable_querysets[variable][i]
            old_value = eval(current_log.old_value)
            new_value = eval(current_log.new_value)
            setattr(log, slugified_variables[variable], new_value['value'])
            if old_value is None:
                setattr(log, f'{slugified_variables[variable]}_changed', True)
            else:
                setattr(log, f'{slugified_variables[variable]}_changed', old_value['value'] != new_value['value'])
    serialized_logs = LogTaxesTariffsSerializer(final_queryset, many=True)
    return serialized_logs.data


def get_indexes_logs_repository():
    queryset = Log.objects.filter(observation='Index Global Variable').order_by('-date')
    serialized_logs = LogSerializer(queryset, many=True)
    return serialized_logs.data


def get_icmss_repository():
    queryset = GlobalVariable.objects.filter(
        variable_id__name__exact='ICMS',
        status=True
    ).annotate(
        variable_name=F('variable_id__name'),
        state_name=F('state_id__name'),
        unity_type=F('unity_id__name')
    )
    serialized_global_variables = GlobalVariablesSerializer(queryset, many=True)
    return serialized_global_variables.data


def get_tax_taxes_tariffs_by_id_repository(id):
    queryset = GlobalVariable.objects.filter(
        id=id,
        status=True,
        variable_id__name__in=['PIS', 'COFINS', 'COTAÇÃO DO DÓLAR', 'TARIFA FIXA DE RATEIO']
    ).annotate(
        variable_name=F('variable_id__name'),
        state_name=F('state_id__name'),
        unity_type=F('unity_id__name')
    )
    serialized_global_variables = GlobalVariablesSerializer(queryset, many=True)
    for value in serialized_global_variables.data:
        old_value = dict(value)
        old_value['variable'] = old_value.get('variable_name')
        old_value['unity'] = old_value.get('unity_type')
        del old_value['variable_name']
        del old_value['formated_value']
        del old_value['month']
        del old_value['year']
        del old_value['state_name']
        del old_value['unity_type']
        return old_value


def get_taxes_tariffs_repository():
    queryset = GlobalVariable.objects.filter(
        status=True,
        variable_id__name__in=['PIS', 'COFINS', 'COTAÇÃO DO DÓLAR', 'TARIFA FIXA DE RATEIO']
    ).annotate(
        variable_name=F('variable_id__name'),
        state_name=F('state_id__name'),
        unity_type=F('unity_id__name')
    )
    serialized_global_variables = GlobalVariablesSerializer(queryset, many=True)
    return serialized_global_variables.data


def get_indexes_repository():
    queryset = GlobalVariable.objects.filter(
        status=True,
        variable_id__name__in=['IGP-M', 'IPCA']
    ).order_by('-year', '-month').annotate(
        variable_name=F('variable_id__name'),
        state_name=F('state_id__name'),
        unity_type=F('unity_id__name')
    )
    serializer_indexes = GlobalVariablesSerializer(queryset, many=True)
    data = serializer_indexes.data
    for item in data:
        item['month'] = str(item['month']).zfill(2)
    return data


def insert_global_variable_repository(global_variable):
    new_variable = GlobalVariablesSerializer(data=global_variable, many=False)
    if new_variable.is_valid(True):
        new_variable.save()
        added_global_variable = GlobalVariable.objects.last()
        return added_global_variable.id


def check_marketing_exists():
    marketing_flag = GlobalVariable.objects.filter(marketing=True, status=True)
    return marketing_flag.exists()


def check_state_exists(global_variable):
    state_result = GlobalVariable.objects.filter(state=global_variable.get('state'), status=True)
    return state_result.exists()


def update_by_id_state_value(global_variable):
    GlobalVariable.objects.filter(id=global_variable.get('id'))\
        .update(value=global_variable.get('value'),
                variable=global_variable.get('variable'),
                unity=global_variable.get('unity'),
                month=get_month(global_variable),
                year=global_variable.get('year'),
                state=global_variable.get('state'),
                marketing=global_variable.get('marketing'),
                status=global_variable.get('status'))


def update_marketing_flag_value(global_variable):
    GlobalVariable.objects.filter(pk=global_variable.get('id'), status=True)\
        .update(value=global_variable.get('value'),
                variable=global_variable.get('variable'),
                unity=global_variable.get('unity'),
                month=get_month(global_variable),
                year=global_variable.get('year'),
                state=global_variable.get('state'),
                marketing=global_variable.get('marketing'),
                status=global_variable.get('status'))


def insert_taxes_tariffs_repository(global_variable):
    data = GlobalVariablesSerializer(data=global_variable, many=False)
    if data.is_valid(True):
        data.save()
        added_global_variable = GlobalVariable.objects.last()
        return added_global_variable.id
    else:
        return data.errors


def update_taxes_tariffs_repository(global_variable):
    GlobalVariable.objects.filter(pk=global_variable.get('id'), status=True).update(value=float(global_variable.get('value')))


def has_variables_been_changed(global_variables):
    GLOBAL_VARIABLES = ['PIS', 'TARIFA FIXA DE RATEIO', 'COTAÇÃO DO DÓLAR', 'COFINS']

    current_variables = GlobalVariable.objects.filter(variable__name__in=GLOBAL_VARIABLES)
    database_variables = {variable.variable.name: variable.value for variable in current_variables}
    variable_has_changed = []

    for variable in global_variables:
        try:
            database_variable = database_variables[variable['variable']]
            variable_has_changed.append(database_variable != Decimal(variable['value']))
        except KeyError:
            variable_has_changed.append(True) # if variable doesnt exist, set True
    return any(variable_has_changed)


def is_index_repository(global_variable):
    global_variable_index = GlobalVariable.objects.filter(
        status=True,
        variable=get_variable(global_variable),
        month=get_month(global_variable),
        year=get_year(global_variable)
    )
    return global_variable_index.exists()


def find_index_by_id(global_variable):
    queryset = GlobalVariable.objects.filter(
        id=global_variable.get('id'),
        status=True,
        variable_id__name__in=['IGP-M', 'IPCA']
    ).annotate(
        variable_name=F('variable_id__name'),
        state_name=F('state_id__name'),
        unity_type=F('unity_id__name')
    ).order_by('-year', '-month')
    serializer_indexes = GlobalVariablesSerializer(queryset, many=True)
    for value in serializer_indexes.data:
        return value


def find_index_by_variable_month_year_repository(global_variable):
    queryset = GlobalVariable.objects.filter(
        variable=get_variable(global_variable),
        month=get_month(global_variable),
        year=get_year(global_variable),
        status=True,
        variable_id__name__in=['IGP-M', 'IPCA']
    ).order_by('-year', '-month').annotate(
        variable_name=F('variable_id__name'), 
        state_name=F('state_id__name'),
        unity_type=F('unity_id__name')
    )
    serializer_indexes = GlobalVariablesSerializer(queryset, many=True)
    return serializer_indexes.data
        

def update_index_repository(global_variable):
    GlobalVariable.objects.filter(
        pk=global_variable.get('id'),
        status=True
    ).update(
        value=global_variable.get('value'),
        variable= global_variable.get('variable'),
        unity= global_variable.get('unity'),
        month=get_month(global_variable),
        year=global_variable.get('year'),
        state=global_variable.get('state'),
        status=True
    )


def set_variable_unity_value(global_variable):
    if global_variable['variable'] is not None:
        global_variable['variable'] = get_variable(global_variable)
    if global_variable['unity'] is not None:
        global_variable['unity'] = get_unity(global_variable)
    if global_variable['value'] is not None:
        global_variable['value'] = get_value(global_variable)
    return global_variable


def set_value_variable_name_unity_type(global_variable):
    if global_variable['value'] is not None:
        global_variable['value'] = get_value(global_variable)
    if global_variable['variable'] is not None:
        global_variable['variable'] = global_variable.get('variable')
    if global_variable['unity'] is not None:
        global_variable['unity'] = global_variable.get('unity')

    return global_variable
    

def get_value(global_variable):
    if global_variable.get('value') is not None:
        try:
            locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
            return locale.atof(global_variable.get('value'))
        except:
            return float(global_variable.get('value'))
    else:
        return None


def get_month(global_variable):
    if global_variable.get('month') is not None:
        return int(global_variable.get('month'))


def get_year(global_variable):
    if global_variable.get('year') is not None:
        return int(global_variable.get('year'))


def get_marketing(global_variable):
    if global_variable.get('marketing') is not None:
        return global_variable.get('marketing')


def get_unity_by_id(global_variable):
    try:
        unity = Unity.objects.get(id=global_variable)
        return unity.name
    except Unity.DoesNotExist:
        return None


def get_unity(global_variable):
    try:
        if global_variable.get('unity') is not None:
            unity = Unity.objects.get(name=global_variable.get('unity'))
            return unity.id
        else:
            return None
    except Unity.DoesNotExist:
        return None


def get_variable_by_id(global_variable):
    try:
        variable = Variable.objects.get(id=global_variable)
        print('Variable', variable)
        return variable.name
    except Variable.DoesNotExist:
        return None


def get_variable(global_variable):
    try:
        if global_variable.get('variable') is not None:
            variable = Variable.objects.get(name=global_variable.get('variable'))
            return variable.id
        else:
            return None
    except Variable.DoesNotExist:
        return None


def get_user_firstname(request):
    return request.auth.get('UserFullName')


def strip_accents(text):
    """
    Strip accents from input String.

    :param text: The input string.
    :type text: String.

    :returns: The processed String.
    :rtype: String.
    """
    text = unicodedata.normalize('NFD', text)
    text = text.encode('ascii', 'ignore')
    text = text.decode("utf-8")
    return str(text)


def format_icms_log(variable='ICMS', unit='PERCENTUAL', status=True):
    """Creates a dictionary with the current values of ICMS for state and marketing"""
    states = State.objects.all()
    global_variables = GlobalVariable.objects.select_related('state').exclude(status=False).all()
    icms_by_state = global_variables.filter(state__isnull=False).distinct()
    marketing = global_variables.filter(marketing=True).distinct()
    icms_log = {
        'variable': variable, 
        'unity': unit,
        'status': status,
        'states': []
    }
    for state in states:
        try:
            icms_log['states'].append({
                'state': state.name,
                'value': icms_by_state.get(state=state, status=True).value,
            })
        except GlobalVariable.DoesNotExist:
            icms_log['states'].append({
                'state': state.name,
                'value': None,
            })
    if marketing.exists():
        icms_log['states'].insert(0, {
            'state': 'Marketing',
            'value': marketing.get().value,
        })
    else:
        icms_log['states'].insert(0, {
            'state': 'Marketing',
            'value': None,
        })
    return icms_log


def get_user_username(request):
    return f'{request.auth.get("cn")} - {request.auth.get("UserFullName")}'