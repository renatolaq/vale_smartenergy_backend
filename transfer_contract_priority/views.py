import json

from django.core.serializers.json import DjangoJSONEncoder
from django.forms import model_to_dict

from cliq_contract.models import CliqContract

from transfer_contract_priority.models import TransferContractPriority
from transfer_contract_priority.serializers import TransferContractPrioritySerializer, CliqContractPrioritySerializer

from django.db.models import F, Q
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from core.views import generic_queryset_filter, generic_paginator, generic_log_search, generic_log_search_basic
from core.serializers import generic_update
from core.attachment_utility import generic_csv, generic_pdf, generic_xls
import collections
from core.models import Log

from django.http import HttpResponse
from io import StringIO, BytesIO
import pandas as pd
import pdfkit
from locales.translates_function import translate_language_header, translate_language, translate_language_error, translate_language_log

# Create your views here.
@api_view(['GET'])
def session_transfer_contract_priority(request, format=None):
    """
        List all Transfer Contract Priority records or create a new one
    """

    observation_log = ""
    if 'observation_log' in request.data:
        observation_log = request.data['observation_log']

    serializer_context = {
        'request': request,
        'observation_log': observation_log,
    }

    if request.method == 'GET':

        kwargs_order = {
            'contract_name': 'id_contract_cliq__id_contract__contract_name',
            'code_ccee': 'id_contract_cliq__id_ccee__code_ccee',
            'buyer_profile': 'id_contract_cliq__id_buyer_profile__name_profile',
            'vendor_profile': 'id_contract_cliq__id_vendor_profile__name_profile',
            'transaction_type': 'id_contract_cliq__transaction_type',
            'priority_number': 'priority_number',
            '-contract_name': '-id_contract_cliq__id_contract__contract_name',
            '-code_ccee': '-id_contract_cliq__id_ccee__code_ccee',
            '-buyer_profile': '-id_contract_cliq__id_buyer_profile__name_profile',
            '-vendor_profile': '-id_contract_cliq__id_vendor_profile__name_profile',
            '-transaction_type': '-id_contract_cliq__transaction_type',
            '-priority_number': '-priority_number',
        }

        if request.query_params.get('ordering') in kwargs_order:
            order_by = kwargs_order[request.query_params.get('ordering')]
        else:
            order_by = kwargs_order["priority_number"]

        filter_params = Q()

        def add_query(param, filter=''):
            value_param = request.query_params.get(param, None)
            if value_param is not None and value_param.strip():
                key = kwargs_order[param] + filter
                dct = {key: value_param}
                filter_params.add(Q(**dct), Q.AND)

        add_query('contract_name', '__contains')
        add_query('code_ccee', '__contains')
        add_query('buyer_profile', '__contains')
        add_query('vendor_profile', '__contains')
        add_query('transaction_type', '__contains')
        add_query('priority_number', '__contains')

        # returns only cliq_contracts related to an energy_contract
        contract_priority = TransferContractPriority.objects \
            .filter(status='S') \
            .filter(filter_params) \
            .order_by(F(order_by).asc(nulls_last=True))

        serializer = CliqContractPrioritySerializer(contract_priority, many=True, context=serializer_context)

        response = collections.OrderedDict([('results', serializer.data)])

        return Response(response)

@api_view(['GET'])
def session_log_transfer_contract_priority(request, pk, format=None):
    """
        List all logs about Transfer Contract Priority and children
    """

    kwargs = {'core': TransferContractPriority, 'core_pk': 'id_transfer', 'core+': [],
              'child': []}

    serializer = collections.OrderedDict(generic_log_search(pk, **kwargs))

    return Response(serializer)


# Individual posts to reorder current contract
# Expects dict {"id_contract_cliq": "Contract Cliq ID that is being (re)prioritized",
#              "new_priority_number": "New Contract Cliq priority number"}

@api_view(['POST'])
def session_transfer_contract_priority_reorder(request, format=None):
    """
        Reorders Transfer Contract Priorities
    """

    observation_log = ""
    if 'observation_log' in request.data:
        observation_log = request.data['observation_log']

    serializer_context = {
        'request': request,
        'observation_log': observation_log
    }

    if request.method == 'POST':
        id_transfer = request.data.pop('id_transfer')
        new_priority_number = request.data.pop('new_priority_number')

        if new_priority_number <= 0 or new_priority_number > TransferContractPriority.objects.filter(status='S').count():
            return Response({'TransferContractPriority': translate_language_error('error_transfer_priority_out_range', request) }, status=status.HTTP_400_BAD_REQUEST)

        try:
            priority_cliq_contract = TransferContractPriority.objects.get(pk=id_transfer)
        except TransferContractPriority.DoesNotExist:
            return Response({'TransferContractPriority': translate_language_error('error_transfer_contract_not_found', request) }, status=status.HTTP_400_BAD_REQUEST)

        if new_priority_number < priority_cliq_contract.priority_number:
            # Increaase priority
            contracts_to_reorder = TransferContractPriority.objects \
                .filter(priority_number__gte=new_priority_number, status='S') \
                .exclude(pk=id_transfer) \
                .order_by('priority_number')

            i = new_priority_number

            for priority in contracts_to_reorder:
                i += 1
                p = json.loads(json.dumps(model_to_dict(priority), cls=DjangoJSONEncoder))
                p['priority_number'] = i
                p['id_contract_cliq'] = CliqContract.objects.get(pk=p['id_contract_cliq'])
                generic_update(TransferContractPriority, priority.id_transfer, dict(p), request.user,
                               observation_log)

        elif new_priority_number > priority_cliq_contract.priority_number:
            # Decrease priority
            contracts_to_reorder = TransferContractPriority.objects \
                .filter(priority_number__lte=new_priority_number, status='S') \
                .exclude(pk=id_transfer) \
                .order_by('-priority_number')

            i = new_priority_number

            for priority in contracts_to_reorder:
                i -= 1
                p = json.loads(json.dumps(model_to_dict(priority), cls=DjangoJSONEncoder))
                p['priority_number'] = i
                p['id_contract_cliq'] = CliqContract.objects.get(pk=p['id_contract_cliq'])
                generic_update(TransferContractPriority, priority.id_transfer, dict(p), request.user, observation_log)
                
        else:
            return Response(status=status.HTTP_304_NOT_MODIFIED)
        """
        old_priority = {
            "status": "N",
            "id_contract_cliq": int(priority_cliq_contract.id_contract_cliq.id_contract_cliq)
        }
        """
        new_priority_cliq_contract = {
            "id_contract_cliq": int(priority_cliq_contract.id_contract_cliq.id_contract_cliq),
            "priority_number": new_priority_number,
            "status": "S"}
        

        serializer = TransferContractPrioritySerializer(priority_cliq_contract, data=new_priority_cliq_contract,
                                                        context=serializer_context)
        if serializer.is_valid():
            serializer.save()
            """
            serializer_contract_priority = TransferContractPrioritySerializer(data=new_priority_cliq_contract,
                                                                              context=serializer_context)            
            if serializer_contract_priority.is_valid():
                serializer.save()
                serializer_contract_priority.save()
            else:
                serializer.delete()
                return Response(serializer_contract_priority.errors, status=status.HTTP_400_BAD_REQUEST)
            """
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    return Response(status=status.HTTP_200_OK)


@api_view(['GET'])
def session_transfer_contract_priority_file(request, format=None):
    """
    API endpoint transfer contract priority filtered
    """
    serializer_context = {
        'request': request,
    }

    format_file = None

    if not(request.query_params.get('format_file',None) == None):
        format_file = request.query_params.get('format_file',None)
    else:
        return Response({'error': translate_language_error('error_format_file_csv_or_pdf', request) }, status=status.HTTP_400_BAD_REQUEST)

    kwargs_order = {
            'contract_name': 'id_contract_cliq__id_contract__contract_name',
            'code_ccee': 'id_contract_cliq__id_ccee__code_ccee',
            'buyer_profile': 'id_contract_cliq__id_buyer_profile__name_profile',
            'vendor_profile': 'id_contract_cliq__id_vendor_profile__name_profile',
            'transaction_type': 'id_contract_cliq__transaction_type',
            'priority_number': 'priority_number',
            '-contract_name': '-id_contract_cliq__id_contract__contract_name',
            '-code_ccee': '-id_contract_cliq__id_ccee__code_ccee',
            '-buyer_profile': '-id_contract_cliq__id_buyer_profile__name_profile',
            '-vendor_profile': '-id_contract_cliq__id_vendor_profile__name_profile',
            '-transaction_type': '-id_contract_cliq__transaction_type',
            '-priority_number': '-priority_number',
        }

    if request.query_params.get('ordering') in kwargs_order:
        order_by = kwargs_order[request.query_params.get('ordering')]
    else:
        order_by = kwargs_order["priority_number"]

    filter_params = Q()

    def add_query(param, filter=''):
        value_param = request.query_params.get(param, None)
        if value_param is not None and value_param.strip():
            key = kwargs_order[param] + filter
            dct = {key: value_param}
            filter_params.add(Q(**dct), Q.AND)

    add_query('contract_name', '__contains')
    add_query('code_ccee', '__contains')
    add_query('buyer_profile', '__contains')
    add_query('vendor_profile', '__contains')
    add_query('transaction_type', '__contains')
    add_query('priority_number', '__contains')

        # returns only cliq_contracts related to an energy_contract
    contract_priority = TransferContractPriority.objects \
            .filter(status='S') \
            .filter(filter_params) \
            .order_by(F(order_by).asc(nulls_last=True))
    array=[]
    for item in contract_priority:
        array.append(CliqContractPrioritySerializer(item, context=serializer_context).data )

    payload = array
    payload = json.dumps(payload, indent=4, default=str).encode('utf-8')
    rest = json.loads(payload)
    
    header =   {'contract_name' : 'field_name_priority_number',
                'code_ccee' : 'field_contract_cliq',
                'buyer_profile' : 'field_buyer_profile',
                'vendor_profile' : 'field_seller_profile',
                'transaction_type' : 'field_transaction_type',
                'priority_number' : 'field_priority_number'
            }
    header = translate_language_header(header, request)
    mapping =  ['contract_name',
                'code_ccee',
                'buyer_profile',
                'vendor_profile',
                'transaction_type',
                'priority_number']
    rest_data = []
    for index in range(len(rest)):
        kwargs = rest[index]
        new = {'contract_name': kwargs['cliq_contract']['id_contract']['contract_name'],
               'code_ccee': kwargs['cliq_contract']['id_ccee']['code_ccee'],
               'buyer_profile': kwargs['cliq_contract']['id_buyer_profile']['name_profile'],
               'vendor_profile': kwargs['cliq_contract']['id_vendor_profile']['name_profile'],
               'transaction_type': translate_language(kwargs['cliq_contract']['transaction_type'], request),
               'priority_number': kwargs['priority_number']
               }
        rest_data.append(new)
    try:
        if format_file == 'csv':  
            return generic_csv(mapping, header, rest_data, translate_language("label_transferContractPriority_download", request))
        elif format_file == 'xlsx':
            style=[]
            return generic_xls(mapping, header, rest_data, translate_language("label_transferContractPriority_download", request), style)                
        elif format_file == 'pdf':
            return generic_pdf(mapping, header, rest_data, translate_language("label_transferContractPriority_download", request))
        else:
            return Response({'error': translate_language_error('error_unknow_format_file', request) }, status=status.HTTP_400_BAD_REQUEST)
    except:  # pragma: no cover
        # just to protect endpoint
        return Response({}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def session_log_basic_transfer_contract_priority(request, pk, format=None):
    """
        List all logs about Transfer Contract Priority and children
    """
    
    transfer_pks = TransferContractPriority.objects.values_list('id_transfer', flat=True).filter(id_contract_cliq = pk)        
    logs = Log.objects.filter(table_name=TransferContractPriority._meta.db_table, field_pk__in=transfer_pks).values()
    logs = generic_log_search_basic({ 'TRANSFER_CONTRACT_PRIORITY': logs})

    cliq_contract_model = CliqContract.objects.get(pk=pk)
    cliq_contract_response = {
        'id_contract_cliq': pk,
        'name_buyer_profile': cliq_contract_model.id_buyer_profile.name_profile,
        'name_vendor_profile': cliq_contract_model.id_vendor_profile.name_profile,
        'name_contract': cliq_contract_model.id_contract.contract_name,
        'code_ccee': cliq_contract_model.id_ccee.code_ccee,
        'type_transition': translate_language_log(cliq_contract_model.transaction_type, request)
    }
    
    response = {
        'logs': logs,
        'statics_relateds': {
            'CLIQ_CONTRACT_CLIQ': cliq_contract_response          
        }
    }
    
    return Response(response)    