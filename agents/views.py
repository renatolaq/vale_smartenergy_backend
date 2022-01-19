import json

from django.db.models.fields import BigIntegerField
from agents.models import Agents
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db.models import IntegerField
from django.db.models.functions import Cast
from agents.serializers import CCEESerializerAgents, AgentsSerializerView, AgentsSerializerBasicView, CompanySerializerViewFind, CCEESerializerAgentsBasic
from company.models import Company
from core.attachment_utility import get_leaves, generic_pdf, generic_csv, generic_xls, generic_data_csv_list
from core.models import CceeDescription
from core.views import generic_queryset_filter, generic_paginator, generic_detail_log, validates_data_used_file
import collections
from core.views import generic_log_search, generic_log_search_basic
from locales.translates_function import translate_language, translate_language_header, translate_language_error
from SmartEnergy.auth import check_module, check_module
import SmartEnergy.auth.permissions as permissions
import SmartEnergy.auth.modules as modules
from profiles.models import Profile

# list agents
@api_view(['GET'])
@check_module(modules.agent, [permissions.VIEW, permissions.EDITN1])
def get_data_agents(request, format=None):
    """
        List all source pme
    """
    serializer_context = {
        'request': request,

    }
    try:
        if request.method == 'GET':
            kwargs = {'vale_name_agent': 'vale_name_agent__contains'}
            ids = generic_queryset_filter(request, Agents, 'id_agents', **kwargs)
            source = Agents.objects.filter(id_agents__in=ids, status='S').order_by('vale_name_agent')
            serializer = AgentsSerializerView(source, many=True, context=serializer_context)
            return Response(serializer.data)

    except Agents.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
# list agents basic
@api_view(['GET'])
@check_module(modules.agent,[ permissions.VIEW, permissions.EDITN1])
def get_data_agents_basic(request, format=None):
    """
        List all source pme
    """
    serializer_context = {
        'request': request,

    }
    try:
        if request.method == 'GET':
            kwargs = {'vale_name_agent': 'vale_name_agent__contains'}
            ids = generic_queryset_filter(request, Agents, 'id_agents', **kwargs)
            source = Agents.objects\
                .select_related('id_company')\
                .filter(id_agents__in=ids, status='S').order_by('vale_name_agent')
            try:
                serializer=[]
                for item in source:
                    itemJson=AgentsSerializerBasicView(item, many=False, context=serializer_context).data
                    itemJson['company_detail']=CompanySerializerViewFind(item.id_company, many=False, context=serializer_context).data if item.id_company else ""
                    serializer.append(itemJson)
            except:
                serializer = AgentsSerializerView(source, many=True, context=serializer_context).data
            return Response(serializer)
    except Agents.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@check_module(modules.agent,[ permissions.VIEW, permissions.EDITN1])
def session_agents_get_find_basic(request, format=None):
    """
        List all companies or create a new agents
    """
    if request.method == 'GET':
        data_object = function_find_basic(request)
        data, page_count, page_next, page_previous = generic_paginator(request, data_object)
        serializer = function_format_data_find(request, data)

        response = collections.OrderedDict([
            ('count', page_count),
            ('next', page_next),
            ('previous', page_previous),
            ('results', serializer)
        ])
        return Response(response)


@api_view(['GET'])
@check_module(modules.agent,[ permissions.VIEW, permissions.EDITN1])
def session_agents_get(request, format=None):
    """
        List all companies or create a new agents
    """
    observation_log = ""
    if 'observation_log' in request.data:
        observation_log = request.data['observation_log']

    serializer_context = {
        'request': request,
        'observation_log': observation_log
    }

    if request.method == 'GET':
        kwargs = {'code_ccee': 'id_ccee__code_ccee__contains',
                  'name_ccee': 'id_ccee__name_ccee__contains',
                  'vale_name_agent': 'vale_name_agent__contains',
                  'company_name': 'id_company__company_name__contains',
                  'status_agent': 'status__contains'
                  }

        kwargs_order = {'code_ccee': 'code_ccee',
                        'name_ccee': 'name_ccee',
                        'vale_name_agent': 'ccee_agent__vale_name_agent',
                        'company_name': 'ccee_agent__id_company__company_name',
                        'status_agent': 'ccee_agent__status',

                        '-code_ccee': '-code_ccee',
                        '-name_ccee': '-name_ccee',
                        '-vale_name_agent': '-ccee_agent__vale_name_agent',
                        '-company_name': '-ccee_agent__id_company__company_name',
                        '-status_agent': '-ccee_agent__status',
                        }
    
        ids = generic_queryset_filter(request, Agents, 'id_ccee', **kwargs)
        if request.query_params.get('ordering') in kwargs_order:
            order_by = kwargs_order[request.query_params.get('ordering')]
        else:
            order_by = kwargs_order['name_ccee']
        ccee = CceeDescription.objects.filter(id_ccee__in=ids).order_by(order_by)
        data, page_count, page_next, page_previous = generic_paginator(request, ccee)
        serializer = CCEESerializerAgents(data, many=True, context=serializer_context)

        response = collections.OrderedDict([
            ('count', page_count),
            ('next', page_next),
            ('previous', page_previous),
            ('results', serializer.data)
        ])
        return Response(response)

# Create your views here.
@api_view(['POST'])
@check_module(modules.agent, [permissions.EDITN1])
def session_agents_post(request, format=None):
    """
        List all companies or create a new agents
    """
    observation_log = ""
    if 'observation_log' in request.data:
        observation_log = request.data['observation_log']

    serializer_context = {
        'request': request,
        'observation_log': observation_log
    }

    if request.method == 'POST':
        serializer = CCEESerializerAgents(data=request.data, context=serializer_context)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT'])
@check_module(modules.agent, [permissions.EDITN1])
def session_agents_put(request, pk, format=None):
    """
        Retrieve, update or delete a specific agent.
    """
    observation_log = ""
    if 'observation_log' in request.data:
        observation_log = request.data['observation_log']

    serializer_context = {
        'request': request,
        'observation_log': observation_log
    }
    try:
        try:
            agent = Agents.objects.get(pk=pk)
        except Agents.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        ccee = CceeDescription.objects.get(pk=agent.id_ccee_id)
        if ccee.type != 'A/P': # pragma: no cover
            kwargs = {'type': ( translate_language_error('error_ccee_type', request)+"A/P" ) }
            serializer = collections.OrderedDict(kwargs)
            return Response(serializer, status=status.HTTP_400_BAD_REQUEST)
    except CceeDescription.DoesNotExist:  # pragma: no cover
        # by database constraint will never happen
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'PUT':
        serializer = CCEESerializerAgents(ccee, data=request.data, context=serializer_context)
        if serializer.is_valid():
            serializer.save()

            alpha_profile=Profile.objects.filter(id_agents_id=pk, alpha='S').first()
            if alpha_profile:
                alpha_profile.name_profile = request.data['ccee_agent']['vale_name_agent']
                alpha_profile.save()

            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@check_module(modules.agent,[ permissions.VIEW, permissions.EDITN1])
def session_agents_get_detail(request, pk, format=None):
    """
        Specific agent.
    """
    observation_log = ""
    if 'observation_log' in request.data:
        observation_log = request.data['observation_log']

    serializer_context = {
        'request': request,
        'observation_log': observation_log
    }
    try:
        try:
            agent = Agents.objects.get(pk=pk)
        except Agents.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        ccee = CceeDescription.objects.get(pk=agent.id_ccee_id)
        if ccee.type != 'A/P':# pragma: no cover
            kwargs = {'type': ( translate_language_error('error_ccee_type', request)+"A/P" ) }
            serializer = collections.OrderedDict(kwargs)
            return Response(serializer, status=status.HTTP_400_BAD_REQUEST)
    except CceeDescription.DoesNotExist:  # pragma: no cover
        # by database constraint will never happen
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = CCEESerializerAgents(ccee, context=serializer_context)
        return Response(serializer.data)

@api_view(['GET'])
@check_module(modules.agent,[ permissions.VIEW, permissions.EDITN1])
def session_agents_file(request):
    if not (request.query_params.get('format_file', None) is None):
        format_file = request.query_params.get('format_file', None)
    else:
        return Response({'error': translate_language_error('error_format_file_csv_or_pdf', request) }, status=status.HTTP_400_BAD_REQUEST)

    data_object = function_find_basic(request)
    serializer = function_format_data_find(request, data_object)

    payload = json.dumps(serializer, indent=4, default=str).encode('utf-8')
    rest = json.loads(payload)
        
    header = {
        'code_ccee': 'ccee_code',
        'name_ccee': 'field_name_ccee',
        'vale_name_agent': 'field_vale_name_agent',
        'company_name': 'field_company_name',
        'status': 'Status'
    }
    header=translate_language_header(header, request)
    mapping = [
        'code_ccee', 
        'name_ccee', 
        'vale_name_agent', 
        'company_name', 
        'status'
    ]
    
    rest = generic_data_csv_list(rest, [])
    rest_data = []
    
    type_format_number=0 if format_file=='pdf' else 1
    for index in range(len(rest)):
        kwargs = rest[index]
        new={
            'code_ccee': validates_data_used_file(kwargs, ['code_ccee'], type_format_number), 
            'name_ccee': validates_data_used_file(kwargs, ['name_ccee'], 0),
            'vale_name_agent': validates_data_used_file(kwargs, ['ccee_agent', 'vale_name_agent'], 0),
            'company_name': validates_data_used_file(kwargs, ['ccee_agent', 'company_detail', 'company_name'], 0),
            'status': translate_language("field_status_"+ ( validates_data_used_file(kwargs, ['ccee_agent', 'status'], 0) ) , request),
        }
        rest_data.append(new)

    try:
        if format_file == 'csv':
            return generic_csv(mapping, header, rest_data, translate_language('label_agent_download', request) )
        if format_file == 'xlsx':
            styles=[
                {
                    'fields': [
                        "code_ccee"
                    ], 
                    'number_format': '0'
                }
            ]
            return generic_xls(mapping, header, rest_data, translate_language('label_agent_download', request), styles)
        elif format_file == 'pdf':
            return generic_pdf(mapping, header, rest_data, translate_language('label_agent_download', request) )
        else:
            return Response({'error': translate_language_error('error_unknown_format_file', request)}, status=status.HTTP_400_BAD_REQUEST)
    except:  # pragma: no cover
        # just to protect endpoint
        return Response({translate_language_error('error_undefined', request)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@check_module(modules.agent,[ permissions.VIEW, permissions.EDITN1])
def session_log_basic_agents(request, pk, format=None):
    """
        List all logs about agents
    """
    kwargs = {'core': Agents, 'core_pk': 'id_agents', 'core+': [{CceeDescription: 'id_ccee'}],
              'child': []}
    
    kwargsAux=generic_log_search_basic(generic_log_search(pk, **kwargs))
    kwargs={'logs':kwargsAux}

    id_array=[]
    company_Array=[]
    #company
    for items in kwargsAux:
        if items['AGENTS']['new_value']['id_company']:
            a=items['AGENTS']['new_value']['id_company']
            if 'value' in a:
                id_num=a['value']
            else:
                id_num=a
            if id_num not in id_array:
                id_array.append(id_num)
                company_Array.append({'id_company':id_num,'company_name':Company.objects.get(pk=id_num).company_name})
    
    kwargs['statics_relateds']={'Company':company_Array}
    return Response( kwargs )



def function_find_basic(request):
    kwargs = {
        'code_ccee': 'id_ccee__code_ccee__contains',
        'name_ccee': 'id_ccee__name_ccee__contains',
        'vale_name_agent': 'vale_name_agent__contains',
        'company_name': 'id_company__company_name__contains',
        'status_agent': 'status__contains'
    }
    kwargs_order = {
        'code_ccee': 'id_ccee__code_ccee',
        'name_ccee': 'id_ccee__name_ccee',
        'vale_name_agent': 'vale_name_agent',
        'company_name': 'id_company__company_name',
        'status_agent': 'status',

        '-code_ccee': '-id_ccee__code_ccee',
        '-name_ccee': '-id_ccee__name_ccee',
        '-vale_name_agent': '-vale_name_agent',
        '-company_name': '-id_company__company_name',
        '-status_agent': '-status',
    }
    ids = generic_queryset_filter(request, Agents, 'id_ccee', **kwargs)

    if request.query_params.get('ordering') in kwargs_order:
        order_by = kwargs_order[request.query_params.get('ordering')]
    else:
        order_by = kwargs_order['name_ccee']
    agents_obj = Agents.objects\
        .select_related('id_ccee').select_related('id_company')\
        .annotate(id_ccee__code_ccee=Cast('id_ccee__code_ccee', BigIntegerField()))\
        .filter(id_ccee__in=ids).order_by(order_by)

    return agents_obj

def function_format_data_find(request, data_object):
    observation_log = ""
    if 'observation_log' in request.data:
        observation_log = request.data['observation_log']

    serializer_context = {
        'request': request,
        'observation_log': observation_log
    }
    serializer=[]
    for item in data_object:
        try:
            itemJson=CCEESerializerAgentsBasic(item.id_ccee, many=False, context=serializer_context).data 
            ccee_agent = AgentsSerializerBasicView(item, many=False, context=serializer_context).data 
            company_detail = CompanySerializerViewFind(item.id_company, many=False, context=serializer_context).data
            itemJson['ccee_agent']= ccee_agent
            itemJson['ccee_agent']['company_detail']= company_detail
        except:
            itemJson = CCEESerializerAgents(item.id_ccee, many=False, context=serializer_context).data
        serializer.append(itemJson)
    return serializer