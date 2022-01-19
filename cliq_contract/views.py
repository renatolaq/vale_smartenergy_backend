import json
import re
import os
import pandas as pd
import calendar
import datetime
from dateutil.relativedelta import relativedelta
from django.core.serializers.json import DjangoJSONEncoder
from cliq_contract.models import CliqContract, SeasonalityCliq
from core.attachment_utility import generic_pdf, generic_csv, generic_data_csv_list, generic_xls
from core.models import Seasonality, CceeDescription
from cliq_contract.serializers import CliqContractSerializer, CliqContractSerializerView, \
    SeasonalityCliqSerializer, SeasonalitySerializerView, SeasonalityCliqSerializerView
from core.serializers import log
from energy_contract.models import Seasonal, EnergyContract, Flexibilization, Precification, Variable, GlobalVariable
from transfer_contract_priority.serializers import TransferContractPrioritySerializer, \
    TransferContractPriority
from profiles.models import Profile
from assets.models import Assets, Submarket
from asset_items.models import AssetItems
from django.db.models import Max
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from core.views import generic_queryset_filter, generic_paginator, generic_log_search, alter_number, \
    generic_log_search_basic, validates_data_used_file
import collections
from locales.translates_function import translate_language_header, translate_language, translate_language_error, translate_language_log
import numpy as np

from SmartEnergy.auth import check_module
import SmartEnergy.auth.permissions as permissions
import SmartEnergy.auth.modules as modules
from SmartEnergy import settings
from locales.translates_function import translate_label
from django.http import HttpResponse
from openpyxl import load_workbook
from uuid import uuid4

def get_pv(kwargs_validation):
    if 'id_contract' in kwargs_validation:
        try:
            energy = EnergyContract.objects.get(pk=kwargs_validation['id_contract'])
        except EnergyContract.DoesNotExist:
            return 0
        try:
            precification = Precification.objects.get(pk=energy.id_contract)
        except Precification.DoesNotExist:
            return 0
        try:
            if precification.id_variable is None:
                return precification.base_price_mwh
            else:
                numexp = re.compile(r'[-]?\d[\d,]*[\.]?[\d{2}]*')  # optional - in front
                numbers = numexp.findall(str(precification.id_variable))
                numbers = [x.replace(',', '') for x in numbers]
                variable_id = int(numbers[0])
                variable = Variable.objects.get(pk=variable_id)
                if variable.name not in ('IPCA', 'IGP-M'):
                    return precification.base_price_mwh
                mask = '%Y-%m-%d'
                birthday_date = precification.birthday_date.strftime(mask)
                actual_date = datetime.now().strftime(mask)
                base_date = precification.base_price_date.strftime(mask)
                if birthday_date > actual_date:
                    return precification.base_price_mwh
                else:
                    now = datetime.now()
                    birthday_date = precification.birthday_date.replace(year=now.year).strftime(mask)
                    month_list = [i.strftime("%m-%Y") for i in
                                  pd.date_range(start=base_date, end=birthday_date, freq='MS')]
                    acum_ir = 0
                    for search in month_list:
                        month = int(search[:2])
                        year = int(search[3::])
                        for global_variable in GlobalVariable.objects.filter(id_variable=variable_id, month=month,
                                                                             year=year):
                            acum_ir += global_variable.value if global_variable.value else 0
                return precification.base_price_mwh + (precification.base_price_mwh * acum_ir)
        except:
            return precification.base_price_mwh if precification else 0
    return 0


def genereal_validation(kwargs_validation, request):
    try:
        message = ""
        message_array= []            
        energy = EnergyContract.objects.get(pk=kwargs_validation['id_contract'])
        if request.data['cliqcontract']['status'] == 'S' and request.method == 'PUT':
            cliq_contract = cliq_contract = CliqContract.objects.get(pk=request.data['cliqcontract']['id_contract_cliq'])
            if energy.id_energy_product.id_energy_product != 1 and cliq_contract.id_vendor_profile.encouraged_energy == False:
                message_array.append(translate_language_error('error_seller_profile_cliqContract', request))
                return False, message_array
            elif energy.id_energy_product.id_energy_product == 1 and cliq_contract.id_vendor_profile.encouraged_energy != False:
                message_array.append(translate_language_error('error_seller_profile_cliqContract', request))
                return False, message_array
        if energy.volume_mwm:
            mwm_volume = float(energy.volume_mwm)
        else:
            return True, ""
        try:
            seasonal = Seasonal.objects.get(pk=energy.id_contract)
            season_max_pu = seasonal.season_max_pu if seasonal.season_max_pu else 1
            season_min_pu = seasonal.season_min_pu if seasonal.season_min_pu else 1
        except Seasonal.DoesNotExist:
            season_max_pu=1
            season_min_pu=1     
        flexibilization = Flexibilization.objects.get(pk=energy.id_contract)
        if energy.flexib_energy_contract.flexibility_type == 'Flat' and request.method == 'PUT' and request.data['cliqcontract']['status'] == 'S':
            if cliq_contract.transaction_type != 'VOLUME_FIXO' or cliq_contract.flexibility != 'CONVENCIONAL':
                 message_array.append(translate_language_error('error_transaction_type', request))
                 return False, message_array
        elif energy.flexib_energy_contract.flexibility_type == 'Flexivel' and energy.flexib_energy_contract.id_flexibilization_type.flexibilization == 'OTHERS' and request.method == 'PUT' and request.data['cliqcontract']['status'] == 'S':            
            if energy.flexib_energy_contract.min_flexibility_pu_peak is None or energy.flexib_energy_contract.max_flexibility_pu_peak is None:
                message_array.append(translate_language_error('error_minmaxflexibility_type', request))
                return False, message_array
            elif cliq_contract.flexibility == 'PONTA E FORA PONTA':
                message_array.append(translate_language_error('error_transaction_type', request))
                return False, message_array
        elif energy.flexib_energy_contract.flexibility_type == 'Flexivel' and energy.flexib_energy_contract.id_flexibilization_type.flexibilization == 'PEAK AND OFF PEAK' and request.method == 'PUT' and request.data['cliqcontract']['status'] == 'S':
            if energy.flexib_energy_contract.min_flexibility_pu_peak is None or energy.flexib_energy_contract.max_flexibility_pu_peak is None or energy.flexib_energy_contract.min_flexibility_pu_offpeak is None or energy.flexib_energy_contract.max_flexibility_pu_offpeak is None:
                message_array.append(translate_language_error('error_minmaxflexibility_type', request))
                return False, message_array
            elif cliq_contract.id_buyer_asset_items is None:
                message_array.append(translate_language_error('error_buyerassetitem_type', request))
                return False, message_array
            elif cliq_contract.flexibility != 'PONTA E FORA PONTA':
                message_array.append(translate_language_error('error_transaction_type', request))
                return False, message_array

        mwm_volume_cliq = float(kwargs_validation.get('mwm_volume') or 0)
        mwm_volume_cliq += float(kwargs_validation.get('mwm_volume_peak') or 0)
        mwm_volume_cliq += float(kwargs_validation.get('mwm_volume_offpeak') or 0)
        total = mwm_volume_cliq
        if 'id_contract_cliq' in kwargs_validation:
            cliqs = CliqContract.objects.filter(id_contract=energy.id_contract,status='S').exclude(
                id_contract_cliq=int(kwargs_validation['id_contract_cliq']))
        else:
            cliqs = CliqContract.objects.filter(id_contract=energy.id_contract, status='S')
        for cliq in cliqs:
            total += float(cliq.mwm_volume or 0) + float(cliq.mwm_volume_peak or 0) + float(cliq.mwm_volume_offpeak or 0)
        if total > mwm_volume and request.method == 'PUT' and request.data['cliqcontract']['status'] == 'S':
            show = total - mwm_volume_cliq
            message_array.append(translate_language_error('error_cliq_value_max_part_1', request) + " %.6f. " % float(mwm_volume))   
            message_array.append(translate_language_error('error_cliq_value_max_part_2', request) + " %.6f. " % float(show))
            message_array.append(translate_language_error('error_cliq_value_max_part_3', request) + " %.6f. " % float(total))
            return False, message_array

        return True, message
    except Exception as e:
        return False, str(e)


def _years_duplicate(seasonalities):
    years = np.array(list(map(lambda x: x['year'], seasonalities)))
    if len(years) != len(np.unique(years)):
        return True
    return False

@api_view(['GET'])
def modulation_template(request):
    try:
        _file_name = 'template_Modulation.xlsx'
        file_path = settings.MEDIA_ROOT + '/templates/'
        full_path = file_path + _file_name

        if os.path.exists(file_path):

            if _file_name.__len__() == 0:
                # Retonar vazio porque o template requisitado não existe
                resp = {'msg': translate_label('error_ima_template', request)}
                return HttpResponse(resp, content_type="text/plain")

            with open(full_path, 'rb') as file:
                _file = file.read()

            response = HttpResponse(_file, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = f'attachment; filename={_file_name}'
            return response
        else:
            # Retonar vazio porque o template requisitado não existe
            resp = {translate_label('error_ima_template',request)}
            return HttpResponse(resp, content_type="text/plain")

    except Exception as e:
        print(e.args)
        # Erro ao tentar baixar template
        resp = {translate_label("error_ima_template_download", request)}
        return HttpResponse(resp, content_type="text/plain")

@api_view(['POST'])
@check_module(modules.energy_contract, [permissions.VIEW, permissions.EDITN1])
def session_cliq_contract_modulation_read(request, format=None):
    excel = pd.read_excel(request.FILES['file_path'],None,skiprows=0)
    df = pd.DataFrame([excel], columns=excel.keys())
    excel_rows = []
    errors = {
        "id": uuid4(),
        "errors": []
    }
    result_verified = []
    current_months = set()
    data = df.to_dict()

    for worksheet in data.values():
        if worksheet[0].empty:
            errors['errors'].append({
                            "code": "BLANK",
                            "detail": {
                                "data": "Non-existed",
                                "value": "Non-existed",
                            },
                            "message": f"Import Error"
                })
        for row in worksheet[0].values:
            if (pd.isna(row[0]) and pd.isna(row[1]) and pd.isna(row[2]) or pd.isna(row[0]) and pd.isna(row[1]) or pd.isna(row[1]) and pd.isna(row[2]) or pd.isna(row[0]) and pd.isna(row[2])):
                errors['errors'].append({
                            "code": "EMPTY_ROW_ERROR",
                            "detail": {
                                "data": "Empty",
                                "value": "Invalid",
                            },
                            "message": f"Import Error"
                })
                return Response(errors, status=status.HTTP_400_BAD_REQUEST)

            if isinstance(row[0], datetime.date):
                if pd.isna(row[0]):
                    date = datetime.date.today()
                    errors['errors'].append({
                                "code": "DATA_ROW_ERROR",
                                "detail": {
                                    "data": "Invalid",
                                    "time": row[1],
                                    "value": row[2],
                                },
                                "message": f"Import Error"
                    })
                else:
                    date = row[0].date()
            else:
                date = datetime.date.today()
                errors['errors'].append({
                                "code": "DATA_ROW_ERROR",
                                "detail": {
                                    "data": "Invalid",
                                    "time": row[1],
                                    "value": row[2],
                                },
                                "message": f"Import Error"
                    })
                
            if isinstance(row[1], datetime.time):
                time = row[1]
            else:
                time = datetime.time()
                errors['errors'].append({
                                "code": "TIME_ROW_ERROR",
                                "detail": {
                                    "data": row[0],
                                    "time": "Invalid",
                                    "value": row[2],
                                },
                                "message": f"Import Error"
                    })
            try:
                value = float(row[2])
                if(pd.isna(value)):
                    value = None
                    errors['errors'].append({
                                "code": "VALUE_ROW_ERROR",
                                "detail": {
                                    "data": row[0],
                                    "time": row[1],
                                    "value": "Invalid",
                                },
                                "message": f"Import Error"
                    })
                else:
                    pass
            except:
                value = None
                errors['errors'].append({
                                "code": "VALUE_ROW_ERROR",
                                "detail": {
                                    "data": row[0],
                                    "time": row[1],
                                    "value": "Invalid",
                                },
                                "message": f"Import Error"
                    })
               

            excel_rows.append({
                "time": datetime.datetime.combine(date, time) ,
                "value": value
            })
            current_months.add(date.strftime("%Y%m"))

    if errors['errors']:
        return Response(errors, status=status.HTTP_400_BAD_REQUEST)
    sorted(excel_rows, key=lambda x: x["time"])

    first_excelvalue = excel_rows[0]["time"]
    last_excelvalue = excel_rows[-1]["time"]
      
    first_excelvalue = first_excelvalue.replace(day=1,hour=0,minute=0,second=0)
    last_excelvalue = last_excelvalue.replace(day=calendar.monthrange(last_excelvalue.year,last_excelvalue.month)[1],hour=23,minute=0,second=0)

    while first_excelvalue <= last_excelvalue:
        if(first_excelvalue.strftime("%Y%m") not in current_months):
            first_excelvalue = first_excelvalue + relativedelta(months=1)
            continue

        value = [element for idx, element in enumerate(excel_rows) if element["time"] == first_excelvalue]
        
        if not value:
            value = "-"
        elif len(value) > 1:
            errors['errors'].append({
                                "code": "DUPLICATE_ROW_ERROR",
                                "detail": {
                                    "data": first_excelvalue,
                                    "value": "Invalid",
                                },
                                "message": f"Import Error"
                    })
            return Response(errors, status=status.HTTP_400_BAD_REQUEST,content_type="application/json")
        else:
            value = value[0]["value"]
        
        result_verified.append({
            "time": first_excelvalue,
            "value": value
            })
        first_excelvalue = first_excelvalue + relativedelta(hours=1)

    return Response(result_verified, content_type="application/json")

@api_view(['GET'])
@check_module(modules.energy_contract, [permissions.VIEW, permissions.EDITN1])
def session_cliq_contract_get(request, format=None):
    """
        List all Cliq Contracts or create a new one
    """
    observation_log = ""
    if 'observation_log' in request.data:
        observation_log = request.data['observation_log']

    serializer_context = {
        'request': request,
        'observation_log': observation_log
    }

    if request.method == 'GET':
        cliq_contract = function_filter(request)
        data, page_count, page_next, page_previous = generic_paginator(request, cliq_contract)
        serializer = CliqContractSerializerView(data, many=True, context=serializer_context)
        response = collections.OrderedDict([
            ('count', page_count),
            ('next', page_next),
            ('previous', page_previous),
            ('results', serializer.data)
        ])

        return Response(response)

@api_view(['POST'])
@check_module(modules.energy_contract, [permissions.EDITN1])
def session_cliq_contract_post(request, format=None):
    """
        create a new one
    """
    observation_log = ""
    if 'observation_log' in request.data:
        observation_log = request.data['observation_log']

    serializer_context = {
        'request': request,
        'observation_log': observation_log
    }

    if request.method == 'POST':
        #return Response({}, status=status.HTTP_400_BAD_REQUEST)
        kwargs = {'id_contract': request.data['cliqcontract']['id_contract'],
                  'mwm_volume': request.data['cliqcontract'].get('mwm_volume'),
                  'mwm_volume_peak': request.data['cliqcontract'].get('mwm_volume_peak'),
                  'mwm_volume_offpeak': request.data['cliqcontract'].get('mwm_volume_offpeak'),
                  'seasonality': request.data['seasonality']}
        energy_contract = EnergyContract.objects.get(pk=kwargs['id_contract'])
        serializer_context['energy_contract'] = energy_contract

        current_price = get_pv(kwargs)
        status_validation, message_validation = genereal_validation(kwargs, request)
        if not status_validation:
            return Response(message_validation, status=status.HTTP_400_BAD_REQUEST)
        seasonalities = request.data.pop('seasonality')
        serializer_season = []
        energy = EnergyContract.objects.get(pk=kwargs['id_contract'])

        # if ((len(seasonalities)) > 0) and request.method == 'POST' and energy.season_energy_contract.type_seasonality == 'Sazonalizado':
            # for season in seasonalities:
                # if (int(season['year']) < energy.start_supply.year) or (int(season['year']) > energy.end_supply.year):
                #     return Response({translate_language_error('error_sazonality_years_supply', request)},\
                #         status=status.HTTP_400_BAD_REQUEST)
                # else:
                #     pass

        if ((len(seasonalities)) == 0) and request.method == 'POST' and energy.season_energy_contract.type_seasonality == 'Sazonalizado':
            return Response({translate_language_error('error_sazonality_not_filled', request)},\
                status=status.HTTP_400_BAD_REQUEST)
              
        if _years_duplicate(seasonalities):
            return Response({translate_language_error('error_year_duplicate', request)},\
                status=status.HTTP_400_BAD_REQUEST)

        # gets all seasonalities and appends its serialized data to an array for future commit to db
        for seasonality in seasonalities:
            season_serialize = SeasonalitySerializerView(data=seasonality, context=serializer_context)
            if not season_serialize.is_valid():
                return Response(season_serialize.errors, status=status.HTTP_400_BAD_REQUEST)
            serializer_season.append(season_serialize)

        # gets CliqContract data
        contract_cliq = request.data.pop('cliqcontract')

        serializer_cliq = CliqContractSerializer(data=contract_cliq, context=serializer_context)

        if serializer_cliq.is_valid():
            new_cliq_contract = serializer_cliq.save()

            # deals with TransferContractPriority
            energy_contract = EnergyContract.objects.get(pk=serializer_cliq.data['id_contract'])
            if energy_contract and energy_contract.modality.upper() in ['TRANSFERENCIA', 'TRANSFERÊNCIA']:
                priority = TransferContractPriority.objects.filter(status='S').exclude(priority_number__isnull=True) \
                    .aggregate(Max('priority_number'))

                new_priority = (priority['priority_number__max'] if priority['priority_number__max'] else 0) + 1

                transf_contract_priority = {'id_contract_cliq': new_cliq_contract.pk,
                                            'priority_number': new_priority,
                                            'status': 'S'}

                serializer_transf_contract_priority = TransferContractPrioritySerializer(data=transf_contract_priority,
                                                                                         context=serializer_context)

                if serializer_transf_contract_priority.is_valid():
                    serializer_transf_contract_priority.save()

            # after all, persists seasonality data and creates SeasonalityCliq relationship record
            for seasonality in serializer_season:
                new_seasonality = seasonality.save()

                seasonality_cliq = {'id_seasonality': new_seasonality.pk,
                                    'id_contract_cliq': new_cliq_contract.pk}

                serializer_season_cliq = SeasonalityCliqSerializer(data=seasonality_cliq,
                                                                   context=serializer_context)

                if serializer_season_cliq.is_valid():
                    serializer_season_cliq.save()
            kwargs = serializer_cliq.data
            kwargs['message_validation'] = message_validation
            kwargs['current_price'] = current_price
            serializer = collections.OrderedDict(kwargs)
            return Response(serializer, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer_cliq.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT'])
@check_module(modules.energy_contract, [permissions.EDITN1])
def session_cliq_contract_put(request, pk, format=None):
    """
        Retrieve, update or delete a specific Cliq Contract.
    """

    observation_log = ""
    if 'observation_log' in request.data:
        observation_log = request.data['observation_log']

    serializer_context = {
        'request': request,
        'observation_log': observation_log
    }

    try:
        cliq_contract = CliqContract.objects.get(pk=pk)

    except CliqContract.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
  
    if request.method == 'PUT':
        kwargs = {'id_contract': request.data['cliqcontract']['id_contract'],
                  'mwm_volume': request.data['cliqcontract']['mwm_volume'],
                  'seasonality': request.data['seasonality'],
                  'id_contract_cliq': request.data['cliqcontract']['id_contract_cliq'],
                  }
        if request.data['cliqcontract']['flexibility'] == 'PONTA E FORA PONTA':
            kwargs['mwm_volume_offpeak'] = request.data['cliqcontract']['mwm_volume_offpeak']
            kwargs['mwm_volume_peak'] = request.data['cliqcontract']['mwm_volume_peak']
        elif request.data['cliqcontract']['flexibility'] == 'FORA PONTA':
            kwargs['mwm_volume_offpeak'] = request.data['cliqcontract']['mwm_volume_offpeak']
        else:
             kwargs['mwm_volume_peak'] = request.data['cliqcontract']['mwm_volume_peak']

        energy_contract = EnergyContract.objects.get(pk=kwargs['id_contract'])
        serializer_context['energy_contract'] = energy_contract
        
        status_validation, message_validation = genereal_validation(kwargs, request)
        if not status_validation:
            return Response(message_validation, status=status.HTTP_400_BAD_REQUEST)
        current_price = get_pv(kwargs)
        contract_cliq = request.data.pop('cliqcontract')
        serializer_cliq = CliqContractSerializer(cliq_contract, data=contract_cliq, context=serializer_context)

        # gets all seasonality ids related to the cliq contract
        seasonality_ids = SeasonalityCliq.objects.filter(id_contract_cliq=pk).values_list('id_seasonality', flat=True)
        energy = EnergyContract.objects.get(pk=kwargs['id_contract'])

        seasonalities = request.data.pop('seasonality')
        
        # if ((len(seasonalities)) > 0) and request.method == 'PUT' and contract_cliq['status'] == 'S' and energy.season_energy_contract.type_seasonality == 'Sazonalizado':
            # for season in seasonalities:
                # if (season['year'] < energy.start_supply.year) or (season['year'] > energy.end_supply.year):
                #     return Response({translate_language_error('error_sazonality_years_supply', request)},\
                #         status=status.HTTP_400_BAD_REQUEST)
                # else:
                #     pass

        if ((len(seasonalities)) == 0) and request.method == 'PUT' and contract_cliq['status'] == 'S' and energy.season_energy_contract.type_seasonality == 'Sazonalizado':
            return Response({translate_language_error('error_sazonality_not_filled', request)},\
                status=status.HTTP_400_BAD_REQUEST)
        elif (request.method == 'PUT' and contract_cliq['status'] == 'S' and (energy.season_energy_contract.type_seasonality == 'Flat' or energy.season_energy_contract.type_seasonality != 'Sazonalizado')):
            seasonalities = []
        
        serializer_season = []
        request_seasonality_ids = []
        
        if _years_duplicate(seasonalities):
            return Response({translate_language_error('error_year_duplicate', request)},\
                status=status.HTTP_400_BAD_REQUEST)

        for seasonality in seasonalities:
            try:
                seasonality_exists = Seasonality.objects.get(pk=seasonality['id_seasonality'])
                request_seasonality_ids.append(seasonality['id_seasonality'])

            except Seasonality.DoesNotExist:
                seasonality_exists = None
            except KeyError:
                seasonality_exists = None

            # if seasonality exists, updates it
            if seasonality_exists:
                op = 1  # update
                serializer_tmp = SeasonalitySerializerView(seasonality_exists, data=seasonality,
                                                           context=serializer_context)
            else:
                # if not exists, checks if year is duplicated in any of other seasonality ids related to the cliq contract
                try:
                    seasonality_exists = Seasonality.objects.get(id_seasonality__in=seasonality_ids,
                                                                 year=seasonality['year'])
                except Seasonality.DoesNotExist:
                    seasonality_exists = None

                if seasonality_exists:
                    return Response(translate_language_error('error_year_already_register', request) + str(seasonality['year'])  ,\
                         status=status.HTTP_304_NOT_MODIFIED)
                op = 0  # insert
                serializer_tmp = SeasonalitySerializerView(data=seasonality, context=serializer_context)

            if not serializer_tmp.is_valid():
                return Response(serializer_tmp.errors['non_field_errors'],
                                status=status.HTTP_400_BAD_REQUEST)

            # if it passes all validations, append to the array for future commit to db
            serializer_season.append([op, serializer_tmp])

            if not serializer_season[len(serializer_season) - 1][1].is_valid():
                return Response(serializer_season[len(serializer_season) - 1][1].errors,
                                status=status.HTTP_400_BAD_REQUEST)

        # validates which seasonlaity id, if any, was removed
        for seasonality_id in seasonality_ids:
            if seasonality_id not in request_seasonality_ids:
                seasonality_exists = Seasonality.objects.filter(pk=seasonality_id)
                # if seasonality exists, marks it for deletion
                if seasonality_exists:
                    op = 2  # delete

                    # if it passes all validations, append to the array for future commit to db
                    serializer_season.append([op, {"id_seasonality": seasonality_id}])

        if serializer_cliq.is_valid():
            serializer_cliq.save()

            # deals with TransferContractPriority
            energy_contract = EnergyContract.objects.get(pk=serializer_cliq.data['id_contract'])
            if energy_contract and energy_contract.modality.upper() in ['TRANSFERENCIA', 'TRANSFERÊNCIA']:
                if serializer_cliq.data['status'] == 'S':
                    # if cliq contract is related to an energy contract, checks if it exists on
                    # TransferContractPriority. If not, creates a record
                    try:
                        priority_exists = TransferContractPriority.objects.get(id_contract_cliq=pk, status='S')
                    except TransferContractPriority.DoesNotExist:
                        priority = TransferContractPriority.objects.filter(status='S').exclude(
                            priority_number__isnull=True) \
                            .aggregate(Max('priority_number'))

                        new_priority = (priority['priority_number__max'] if priority['priority_number__max'] else 0) + 1

                        transf_contract_priority = {'id_contract_cliq': pk,
                                                    'priority_number': new_priority,
                                                    'status': 'S'}

                        serializer_transf_contract_priority = TransferContractPrioritySerializer(
                            data=transf_contract_priority, \
                            context=serializer_context)

                        if serializer_transf_contract_priority.is_valid():
                            serializer_transf_contract_priority.save()
                else:
                    # if cliq contract is not related to an energy contract or is being deactivated, it should
                    # be deactivated in TransferContractPriority as well, if exists
                    try:
                        priority_exists = TransferContractPriority.objects.get(id_contract_cliq=pk, status='S')

                        greater_priorities = TransferContractPriority.objects.filter(status='S', \
                                                                                     priority_number__gt=priority_exists.priority_number) \
                            .exclude(priority_number__isnull=True)

                        # updates all priorities greater than the current one being deactivated to reorder them
                        for priority in greater_priorities:
                            new_priority = (priority.priority_number if priority.priority_number else 2) - 1

                            transf_contract_priority = {'id_transfer': priority.id_transfer,
                                                        'id_contract_cliq': priority.id_contract_cliq.id_contract_cliq,
                                                        'priority_number': new_priority,
                                                        'status': priority.status}

                            serializer_transf_contract_priority = TransferContractPrioritySerializer(priority, \
                                                                                                     data=transf_contract_priority,
                                                                                                     context=serializer_context)

                            if serializer_transf_contract_priority.is_valid():
                                serializer_transf_contract_priority.save()

                        # deactivates TransferContractPriority record related to the cliq contract
                        transf_contract_priority = {'id_transfer': priority_exists.id_transfer,
                                                    'id_contract_cliq': priority_exists.id_contract_cliq.id_contract_cliq,
                                                    'priority_number': None,
                                                    'status': 'N'}

                        serializer_transf_contract_priority = TransferContractPrioritySerializer(priority_exists, \
                                                                                                 data=transf_contract_priority,
                                                                                                 context=serializer_context)

                        if serializer_transf_contract_priority.is_valid():
                            serializer_transf_contract_priority.save()

                    # if cliq contract is not related to an energy contract and doesn't exists on
                    # TransferContractPriority, does nothing
                    except TransferContractPriority.DoesNotExist:
                        pass

            # after dealing with TransferContractPriority
            # creates/updates all seasonality and seasonality cliq data
            for seasonality in serializer_season:
                if seasonality[0] == 2:  # delete seasonality cliq, then seasonality
                    try:
                        seasonality_cliq_obj = SeasonalityCliq.objects.get(
                            id_seasonality=seasonality[1]['id_seasonality'], \
                            id_contract_cliq=pk)
                        log(SeasonalityCliq, seasonality_cliq_obj.id_seasonality_cliq, seasonality_cliq_obj, {},
                            request.user, \
                            observation_log, action="DELETE")
                        seasonality_cliq_obj.delete()
                    except SeasonalityCliq.DoesNotExist:
                        pass

                    try:
                        seasonality_obj = Seasonality.objects.get(pk=seasonality[1]['id_seasonality'])
                        log(Seasonality, seasonality_obj.id_seasonality, seasonality_obj, {}, request.user, \
                            observation_log, action="DELETE")
                        seasonality_obj.delete()
                    except Seasonality.DoesNotExist:
                        pass

                else:  # creates/updates seasonality
                    seasonality_obj = seasonality[1].save()

                    if seasonality[0] == 0:  # insert
                        # if inserting seasonality, inserts seasonality cliq as well
                        seasonality_cliq = {'id_seasonality': seasonality_obj.pk,
                                            'id_contract_cliq': pk}

                        serializer_season_cliq = SeasonalityCliqSerializer(data=seasonality_cliq,
                                                                           context=serializer_context)

                        if serializer_season_cliq.is_valid():
                            serializer_season_cliq.save()
            kwargs = serializer_cliq.data
            kwargs['message_validation'] = message_validation
            kwargs['current_price'] = current_price
            kwargs = json.loads(json.dumps(kwargs, cls=DjangoJSONEncoder))
            serializer = collections.OrderedDict(kwargs)
            return Response(serializer, status=status.HTTP_200_OK)

        return Response(serializer_cliq.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@check_module(modules.energy_contract, [permissions.VIEW, permissions.EDITN1])
def session_cliq_contract_get_detail(request, pk, format=None):
    """
        specific Cliq Contract.
    """

    observation_log = ""
    if 'observation_log' in request.data:
        observation_log = request.data['observation_log']

    serializer_context = {
        'request': request,
        'observation_log': observation_log
    }

    try:
        cliq_contract = CliqContract.objects.get(pk=pk)
    except CliqContract.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        kwargs = {'id_contract': pk}
        current_price = get_pv(kwargs)
        serializer = CliqContractSerializerView(cliq_contract, context=serializer_context)
        kwargs = serializer.data
        kwargs['current_price'] = current_price
        serializer = collections.OrderedDict(kwargs)
        return Response(serializer)

@api_view(['GET'])
@check_module(modules.energy_contract, [permissions.VIEW, permissions.EDITN1])
def session_cliq_contract_file(request, format=None):
    """
    API endpoint cliq contract filtered
    """
    observation_log = ""
    if 'observation_log' in request.data:
        observation_log = request.data['observation_log']

    serializer_context = {
        'request': request,
        'observation_log': observation_log
    }

    format_file = None
    if not (request.query_params.get('format_file', None) == None):
        format_file = request.query_params.get('format_file', None)
    else:
        return Response({'error': translate_language_error('error_format_file_csv_or_pdf', request) }, status=status.HTTP_400_BAD_REQUEST)



    cliq_contract = function_filter(request)
    serializer = CliqContractSerializerView(cliq_contract, many=True, context=serializer_context).data

    # let empty to use de mapping (original) names: header = {}
    # must be in the same order of mapping
    try:
        payload = json.dumps(serializer, indent=9, default=str).encode('utf-8')
        rest = json.loads(payload)
        header = {
            'contract_name': 'field_contract_name',
            'cliq_contract': 'field_cliq_contract',
            'ccee_type_contract': 'field_ccee_type_contract',
            'transaction_type': 'field_transaction_type',
            'flexibility': 'field_flexibility_title',
            'id_vendor_profile__name_profile': 'field_seller_profile',
            'id_buyer_profile__name_profile': 'field_buyer_profile',
            'contractual_loss': 'field_contractual_loss_title',
            'Buyer_Consumer': 'field_buyer_consumer',
            'id_submarket__description': 'field_submarket',
            'submarket': 'field_contract_submarket',
            'status': 'field_cliq_status'            
        }

        header['mwm_volume_peak'] = 'field_mwm_volume_peak_title'
        header['mwm_volume_offpeak'] = 'field_volume_offpeak_title'
        header['mwm_volume'] = 'field_mwm_volume_title'
        header['year'] = 'field_year'
        header['measure_unity'] = 'field_measureUnity'
        header['january'] = 'field_january'
        header['february'] = 'field_february'
        header['march'] = 'field_march'
        header['april'] = 'field_april'
        header['may'] = 'field_may'
        header['june'] = 'field_june'
        header['july'] = 'field_july'
        header['august'] = 'field_august'
        header['september'] = 'field_september'
        header['october'] = 'field_october'
        header['november'] = 'field_november'
        header['december'] = 'field_december'

        header = translate_language_header(header, request)
        mapping = [
            'contract_name',
            'cliq_contract',
            'ccee_type_contract',
            'transaction_type',
            'flexibility',
            'id_vendor_profile__name_profile',
            'id_buyer_profile__name_profile',
            "mwm_volume",
            "mwm_volume_peak",
            "mwm_volume_offpeak",
            'contractual_loss',
            'Buyer_Consumer',
            'id_submarket__description',
            'submarket',
            'status',

            'year',
            "measure_unity",
            "january",
            "february",
            "march",
            "april",
            "may",
            "june",
            "july",
            "august",
            "september",
            "october",
            "november",
            "december"
        ]

        rest = generic_data_csv_list(rest, ['seasonality_cliq_details'])
        rest_data = []
        type_format_number=0 if format_file=='pdf' else 1
        for index in range(len(rest)):
            kwargs = rest[index]
            new = {
                'contract_name': validates_data_used_file(kwargs, ['id_contract', 'contract_name'], 0),
                'cliq_contract': validates_data_used_file(kwargs, ['cliq_contract'], type_format_number), #number
                'ccee_type_contract': validates_data_used_file(kwargs, ['ccee_type_contract'], 0),
                'transaction_type': translate_language(kwargs['transaction_type'], request),
                'flexibility': translate_language(kwargs['flexibility'], request) if kwargs['flexibility'] else "",
                'id_vendor_profile__name_profile': validates_data_used_file(kwargs, ['id_vendor_profile',  'name_profile'], 0),
                'id_buyer_profile__name_profile': validates_data_used_file(kwargs, ['id_buyer_profile',  'name_profile'], 0),
                'mwm_volume': validates_data_used_file(kwargs, ['mwm_volume'], type_format_number), #number
                'mwm_volume_peak': validates_data_used_file(kwargs, ['mwm_volume_peak'], type_format_number), #number
                'mwm_volume_offpeak': validates_data_used_file(kwargs, ['mwm_volume_offpeak'], type_format_number), #number
                'contractual_loss': validates_data_used_file(kwargs, ['contractual_loss'], type_format_number), #number
                'id_submarket__description': validates_data_used_file(kwargs, ['id_submarket', 'description'], 0),
                'submarket': translate_language("field_contract_market_"+validates_data_used_file(kwargs, ['submarket'], 0), request),
                'status': translate_language("field_status_"+( kwargs['status'] if kwargs['status'] else ""), request),
                'year': validates_data_used_file(kwargs, ['seasonality_cliq_details', 'seasonality_detail.year'], type_format_number), #number
                'measure_unity': validates_data_used_file(kwargs, ['seasonality_cliq_details', 'seasonality_detail.measure_unity'], 0),
                'january': validates_data_used_file(kwargs, ['seasonality_cliq_details', 'seasonality_detail.january'], type_format_number), #number
                'february': validates_data_used_file(kwargs, ['seasonality_cliq_details', 'seasonality_detail.february'], type_format_number), #number
                'march': validates_data_used_file(kwargs, ['seasonality_cliq_details', 'seasonality_detail.march'], type_format_number), #number
                'april': validates_data_used_file(kwargs, ['seasonality_cliq_details', 'seasonality_detail.april'], type_format_number), #number
                'may': validates_data_used_file(kwargs, ['seasonality_cliq_details', 'seasonality_detail.may'], type_format_number), #number
                'june': validates_data_used_file(kwargs, ['seasonality_cliq_details', 'seasonality_detail.june'], type_format_number), #number
                'july': validates_data_used_file(kwargs, ['seasonality_cliq_details', 'seasonality_detail.july'], type_format_number), #number
                'august': validates_data_used_file(kwargs, ['seasonality_cliq_details', 'seasonality_detail.august'], type_format_number), #number
                'september': validates_data_used_file(kwargs, ['seasonality_cliq_details', 'seasonality_detail.september'], type_format_number), #number
                'october': validates_data_used_file(kwargs, ['seasonality_cliq_details', 'seasonality_detail.october'], type_format_number), #number
                'november': validates_data_used_file(kwargs, ['seasonality_cliq_details', 'seasonality_detail.november'], type_format_number), #number
                'december': validates_data_used_file(kwargs, ['seasonality_cliq_details', 'seasonality_detail.december'], type_format_number), #number
            }
            try:
                new['Buyer_Consumer'] = ""
                if kwargs['id_buyer_assets']:
                    asset = Assets.objects.get(pk=kwargs['id_buyer_assets']['id_assets'])
                    new['Buyer_Consumer'] = translate_language('field_Assets', request)+": " + str((asset.id_ccee_siga).code_ccee) + " - " \
                                            + (asset.id_company).company_name

                elif kwargs['id_buyer_asset_items']:
                    asset_item = AssetItems.objects.get(pk=kwargs['id_buyer_asset_items']['id_asset_items'])
                    new['Buyer_Consumer'] = translate_language('field_Asset_items', request)+": "  + str(asset_item.id_asset_items)  + " - " \
                                            + (asset_item.id_company).company_name
            except:
                new['Buyer_Consumer'] = "Error"
            rest_data.append(new)

        if format_file == 'csv':
            return generic_csv(mapping, header, rest_data, translate_language("label_cliqContract_download", request) )
        elif format_file == 'xlsx':
            styles=[
                {
                    'fields': [
                        "cliq_contract", "year"
                    ], 
                    "number_format":'0'
                },
                {
                    'fields': [
                        "mwm_volume", "mwm_volume_peak", "mwm_volume_offpeak",
                        "january", "february", "march", 
                        "april", "may", "june", "july", 
                        "august", "september", "october", 
                        "november", "december"
                    ], 
                    "number_format":'#,##0.0000'
                },
                {
                    'fields': [
                        "contractual_loss"
                    ], 
                    'number_format': '#,##0.0000\\%'
                }
            ]
            return generic_xls(mapping, header, rest_data, translate_language("label_cliqContract_download", request), styles)
        elif format_file == 'pdf':
            return generic_pdf(mapping, header, rest_data, translate_language("label_cliqContract_download", request) )
        else:
            return Response({'error': translate_language_error('error_unknown_format_file', request) }, status=status.HTTP_400_BAD_REQUEST)
    except:  # pragma: no cover
        # just to protect endpoint
        return Response({'error': translate_language_error('error_undefined', request) }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@check_module(modules.energy_contract, [permissions.VIEW, permissions.EDITN1])
def session_log_basic_cliq_contract(request, pk, format=None):
    """
        List all logs about Cliq Contract and children
    """

    kwargs = {'core': CliqContract, 'core_pk': 'id_contract_cliq', 'core+': [{CceeDescription: 'id_ccee'}],
              'child': []}
    try:
        log = generic_log_search(pk, **kwargs)
    except CliqContract.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    array = []
    kwargs = {'core': SeasonalityCliq, 'core_pk': 'id_seasonality_cliq',
              'core+': [{Seasonality: 'id_seasonality'}],
              'child': []}
    for a in SeasonalityCliq.objects.filter(id_contract_cliq=pk):
        array.append(generic_log_search(a.id_seasonality_cliq, **kwargs))

    kwargs = log.copy()
    new_seasonality = []
    new_seasonalityCliq = []
    for index in range(len(array)):
        if 'seasonality' in array[index]:
            for intern_index in range(len(array[index]['seasonality'])):
                new_seasonality.append(array[index]['seasonality'][intern_index])
    for index in range(len(array)):
        if 'SEASONALITY_CLIQ' in array[index]:
            for intern_index in range(len(array[index]['SEASONALITY_CLIQ'])):
                new_seasonalityCliq.append(array[index]['SEASONALITY_CLIQ'][intern_index])

    kwargs['SEASONALITY_CLIQ'] = new_seasonalityCliq
    kwargs['SEASONALITY'] = new_seasonality

    kwargsAux = generic_log_search_basic(kwargs)
    log = {'logs': kwargsAux}

    # profile
    id_array = []
    profile_array = []
    for items in kwargsAux:
        if items['CLIQ_CONTRACT']:
            if type(items['CLIQ_CONTRACT'])!=dict:
                items['CLIQ_CONTRACT']=items['CLIQ_CONTRACT'][0]
                
            if items['CLIQ_CONTRACT']['new_value']['id_vendor_profile']:
                a = items['CLIQ_CONTRACT']['new_value']['id_vendor_profile']
                if 'value' in a:
                    id_num = a['value']
                else:
                    id_num = a
                if id_num not in id_array:
                    id_array.append(id_num)
                    profile_array.append(
                        {'id_profile': id_num, 'profile_name': Profile.objects.get(pk=id_num).name_profile})

            if items['CLIQ_CONTRACT']['new_value']['id_buyer_profile']:
                a = items['CLIQ_CONTRACT']['new_value']['id_buyer_profile']
                if 'value' in a:
                    id_num = a['value']
                else:
                    id_num = a
                if id_num not in id_array:
                    id_array.append(id_num)
                    profile_array.append(
                        {'id_profile': id_num, 'profile_name': Profile.objects.get(pk=id_num).name_profile})

    # contract
    id_array.clear()
    contract_array = []
    for items in kwargsAux:
        if items['CLIQ_CONTRACT']:
            if items['CLIQ_CONTRACT']['new_value']['id_contract']:
                a = items['CLIQ_CONTRACT']['new_value']['id_contract']
                if 'value' in a:
                    id_num = a['value']
                else:
                    id_num = a
                if id_num not in id_array:
                    id_array.append(id_num)
                    contract_array.append(
                        {'id_contract': id_num, 'contract_name': EnergyContract.objects.get(pk=id_num).contract_name})

    # submarket
    id_array.clear()
    submarket_Array = []
    for items in kwargsAux:
        if items['CLIQ_CONTRACT']:
            if items['CLIQ_CONTRACT']['new_value']['id_submarket']:
                a = items['CLIQ_CONTRACT']['new_value']['id_submarket']
                if 'value' in a:
                    id_num = a['value']
                else:
                    id_num = a
                if id_num not in id_array:
                    id_array.append(id_num)
                    submarket_Array.append(
                        {'id_submarket': id_num, 'description': Submarket.objects.get(pk=id_num).description})

    # assets
    id_array.clear()
    assets_array = []
    for items in kwargsAux:
        if items['CLIQ_CONTRACT']:
            if items['CLIQ_CONTRACT']['new_value']['id_buyer_assets']:
                a = items['CLIQ_CONTRACT']['new_value']['id_buyer_assets']
                if 'value' in a:
                    if a['value']:
                        id_num = a['value']
                else:
                    id_num = a
                if id_num and id_num != 'None' and id_num not in id_array:
                    id_array.append(id_num)
                    asset = Assets.objects.get(pk=id_num)
                    assets_array.append(
                        {'id_assets': id_num, 'code_ccee': asset.id_ccee_siga.code_ccee,
                         'company_name': asset.id_company.company_name})

    # assetItems
    id_array.clear()
    assetitems = []
    for items in kwargsAux:
        if items['CLIQ_CONTRACT']:
            if items['CLIQ_CONTRACT']['new_value']['id_buyer_asset_items']:
                a = items['CLIQ_CONTRACT']['new_value']['id_buyer_asset_items']
                if 'value' in a:
                    id_num = a['value']
                else:
                    id_num = a
                if id_num and id_num != 'None' and id_num not in id_array:
                    id_array.append(id_num)
                    assetitems.append({'id_assets_items': id_num,
                                       'company_name': (AssetItems.objects.get(pk=id_num).id_company).company_name})

    log['statics_relateds'] = {'profile': profile_array, 'energy_contract': contract_array, 'assets': assets_array,
                               'assets_items': assetitems, 'submarket': submarket_Array}

    return Response(log)

@api_view(['GET'])
@check_module(modules.energy_contract, [permissions.VIEW, permissions.EDITN1])
def session_calculator_value_max(request, pk_contract,format=None):
    energy = EnergyContract.objects.get(pk=pk_contract)

    mwm_volume = energy.volume_mwm if energy.volume_mwm else 0    
    
    return Response({"id": energy.id_contract, "Max_value":mwm_volume}, status=status.HTTP_200_OK)

def function_filter(request):
    kwargs = {
        'id_contract_cliq':'id_contract_cliq',
        'cliq_contract': 'id_ccee__code_ccee__contains',
        'contract_name': 'id_contract__contract_name__contains',
        'id_contract': 'id_contract',
        'buyer_profile': 'id_buyer_profile__name_profile__contains',
        'vendor_profile': 'id_vendor_profile__name_profile__contains',
        'transaction_type': 'transaction_type__contains', 'status': 'status__contains',
        'status': 'status__contains'
    }
    kwargs_order = {
        'contract_name': 'id_contract__contract_name', 
        'cliq_contract': 'id_ccee__code_ccee',
        'buyer_profile': 'id_buyer_profile__name_profile',
        'vendor_profile': 'id_vendor_profile__name_profile',
        'transaction_type': 'transaction_type', 'status': 'status',
        '-contract_name': '-id_contract__contract_name', 
        '-cliq_contract': '-id_ccee__code_ccee',
        '-buyer_profile': '-id_buyer_profile__name_profile',
        '-vendor_profile': '-id_vendor_profile__name_profile',
        '-transaction_type': '-transaction_type', '-status': '-status'
    }
    
    ids = generic_queryset_filter(request, CliqContract, 'id_contract_cliq', **kwargs)

    if request.query_params.get('ordering') in kwargs_order:
        order_by = kwargs_order[request.query_params.get('ordering')]
    else:
        order_by = kwargs_order['cliq_contract']
    cliq_contract = CliqContract.objects.filter(id_contract_cliq__in=ids).order_by(order_by)\
        .select_related('id_vendor_profile').select_related('id_buyer_profile')\
        .select_related('id_contract').select_related('id_ccee')\
        .select_related('id_buyer_assets').select_related('id_buyer_asset_items')\
        .select_related('id_submarket')\
        .prefetch_related('seasonalityCliq_cliqContract').prefetch_related('seasonalityCliq_cliqContract__id_seasonality')

    return cliq_contract

