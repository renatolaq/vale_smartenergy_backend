import json

from rest_framework import status, serializers
from rest_framework.decorators import api_view
from rest_framework.response import Response

from core.attachment_utility import generic_csv, generic_pdf, generic_data_csv_list, generic_xls
from core.models import CceeDescription
from profiles.models import Profile, Agents
from profiles.serializers import CCEESerializerProfile, ProfileSerializer, CCEESerializer,\
        CCEESerializerProfileFindBasic, ProfileSerializerFindBasic,AgentsSerializerFindBasic
from core.views import generic_queryset_filter, generic_paginator, generic_log_search, \
    generic_detail_log,generic_log_search_basic, validates_data_used_file
import collections
from core.serializers import log, generic_update
from locales.translates_function import translate_language_header, translate_language, translate_language_error
from SmartEnergy.auth import check_module
import SmartEnergy.auth.permissions as permissions
import SmartEnergy.auth.modules as modules


@api_view(['GET'])
@check_module(modules.profile, [permissions.VIEW, permissions.EDITN1])
def session_profile_find_basic(request, format=None):
    """
        List all companies or create a new profile
    """
    if request.method == 'GET':
        profile_object = function_find_generic(request)
        data, page_count, page_next, page_previous = generic_paginator(request, profile_object)
        serializer = function_formart_return_find(request, data)
            
        response = collections.OrderedDict([
            ('count', page_count),
            ('next', page_next),
            ('previous', page_previous),
            ('results', serializer)
        ])
        return Response(response)

@api_view(['GET'])
@check_module(modules.profile, [permissions.VIEW, permissions.EDITN1])
def session_profile_get(request, format=None):
    """
        List all profiles 
    """
    observation_log = ""
    if 'observation_log' in request.data:
        observation_log = request.data['observation_log']

    serializer_context = {
        'request': request,
        'observation_log': observation_log
    }
    if request.method == 'GET':
        kwargs = {'vale_name_agent': 'id_agents__vale_name_agent__contains',
                    'alpha': 'alpha',
                    'code_ccee': 'id_ccee__code_ccee__contains',
                    'name_ccee': 'id_ccee__name_ccee__contains', 
                    'name_profile': 'name_profile__contains',
                    'status_profile':'status__contains'
                }
        kwargs_order = {'vale_name_agent': 'profile_ccee__id_agents__vale_name_agent',
                        'alpha': 'profile_ccee__alpha',
                        'code_ccee': 'code_ccee',
                        'name_ccee': 'name_ccee', 
                        'name_profile': 'profile_ccee__name_profile',
                        'status_profile':'profile_ccee__status',

                        '-vale_name_agent': '-profile_ccee__id_agents__vale_name_agent',
                        '-alpha': '-profile_ccee__alpha',
                        '-code_ccee': '-code_ccee',
                        '-name_ccee': '-name_ccee', 
                        '-name_profile': '-profile_ccee__name_profile',
                        '-status_profile':'-profile_ccee__status'
                    }
        ids = generic_queryset_filter(request, Profile, 'id_ccee', **kwargs)
        if request.query_params.get('ordering') in kwargs_order:
            order_by = kwargs_order[request.query_params.get('ordering')]
        else:
            order_by = kwargs_order['name_ccee']
        ccee = CceeDescription.objects.filter(id_ccee__in=ids).order_by(order_by)
        data, page_count, page_next, page_previous = generic_paginator(request, ccee)
        serializer = CCEESerializerProfile(data, many=True, context=serializer_context)
        response = collections.OrderedDict([
            ('count', page_count),
            ('next', page_next),
            ('previous', page_previous),
            ('results', serializer.data)
        ])
        return Response(response)

@api_view(['POST'])
@check_module(modules.profile, [permissions.EDITN1])
def session_profile_post(request, format=None):
    """
        create a new profile
    """
    observation_log = ""
    if 'observation_log' in request.data:
        observation_log = request.data['observation_log']

    serializer_context = {
        'request': request,
        'observation_log': observation_log
    }

    if request.method == 'POST':
        data = request.data
        profile_request = data.get('profile_ccee')
        ccee_serializer=None
        if profile_request.get('alpha') == 'N':
            ccee_serializer = CCEESerializer(data=data, context=serializer_context)
            if ccee_serializer.is_valid():
                ccee_serializer.save()
            else:
                return Response(ccee_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            profile_request['id_ccee'] = ccee_serializer.instance.pk
        profile_serializer = ProfileSerializer(data=profile_request, context=serializer_context)
        #verificar
        if not profile_serializer.is_valid():
            if not ccee_serializer is None:
                ccee_serializer.instance.delete()
            return Response(profile_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        profile_serializer.save()
    return Response(profile_serializer.data)

@api_view(['PUT'])
@check_module(modules.profile, [permissions.EDITN1])
def session_profile_put(request, pk, format=None):
    """
        Retrieve, update or delete a specific profile.
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
            profile = Profile.objects.get(pk=pk)
        except Profile.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        ccee = CceeDescription.objects.get(pk=profile.id_ccee_id)
    except CceeDescription.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'PUT':
        data = request.data
        profile_request = data.get('profile_ccee')
        profile = Profile.objects.get(pk=profile_request.get('id_profile'))
       
        if profile.alpha == 'S' and profile_request.get('alpha') == 'N':
            # Alpha foi desabilitado, então criará um novo ccee para o perfil
            ccee_serializer = CCEESerializer(data=data, context=serializer_context)
            if ccee_serializer.is_valid():
                ccee_serializer.save()
                profile_request['id_ccee'] = ccee_serializer.instance.pk
                profile_serializer = ProfileSerializer(profile, data=dict(profile_request), context=serializer_context)
                if profile_serializer.is_valid():
                    profile_serializer.save()
                else:
                    ccee_serializer.instance.delete()
                    return Response(profile_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response(ccee_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
      
        elif profile.alpha == 'N' and profile_request.get('alpha') == 'S':
            # Alpha foi habilitado, profile ja vira com id_ccee do agente, então precisa validar, salvar e desabilitar o ccee do perfil
            profile_serializer = ProfileSerializer(profile, data=data.get('profile_ccee'), context=serializer_context)
            if profile_serializer.is_valid():
                profile_serializer.save()
            else:
                return Response(profile_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            ccee_disabled = {
                'id_ccee': profile.id_ccee_id,
                'code_ccee': profile.id_ccee.code_ccee,
                'name_ccee': profile.id_ccee.name_ccee,
                'status': 'N'
            }
            user = request.auth['cn'] + " - " + request.auth['UserFullName']
            generic_update(CceeDescription, profile.id_ccee_id, ccee_disabled, user, observation_log)
       
        else:
            profile_serializer = ProfileSerializer(profile, data=profile_request, context=serializer_context)
            if not profile_serializer.is_valid():
                return Response(profile_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            if profile_request.get('alpha') == 'N':
                ccee = CceeDescription.objects.get(pk=data.get('id_ccee'))
                ccee_serializer = CCEESerializer(ccee, data=data, context=serializer_context)
                if not ccee_serializer.is_valid():
                    return Response(ccee_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                ccee_serializer.save()

            profile_serializer.save()

        return Response(profile_serializer.data)

@api_view(['GET'])
@check_module(modules.profile, [permissions.VIEW, permissions.EDITN1])
def session_profile_get_detail(request, pk, format=None):
    """
        specific profile.
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
            profile = Profile.objects.get(pk=pk)
        except Profile.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        ccee = CceeDescription.objects.get(pk=profile.id_ccee_id)
    except CceeDescription.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = CCEESerializerProfile(ccee, context=serializer_context)
        return Response(serializer.data)

@api_view(['GET'])
@check_module(modules.profile, [permissions.VIEW, permissions.EDITN1])
def session_profile_file(request):
    if not (request.query_params.get('format_file', None) is None):
        format_file = request.query_params.get('format_file', None)
    else:
        return Response({'error': translate_language_error('error_format_file_csv_or_pdf', request)}, status=status.HTTP_400_BAD_REQUEST)
    
    obj_profile = function_find_generic(request)
    serializer = function_formart_return_find(request, obj_profile)

    payload = serializer
    payload = json.dumps(payload, indent=4, default=str).encode('utf-8')
    rest = json.loads(payload)

    # let empty to use de mapping (original) names: header = {}
    # must be in the same order of mapping
    header = {
        'vale_name_agent':'field_vale_name_agent', 
        'alpha':'Alpha',
        'code_ccee':'ccee_code',
        'name_ccee': 'field_profile_ccee',
        'name_profile': 'field_profile_vale', 
        'status':'field_profile_status'
    }
    header = translate_language_header(header, request)
    mapping = [
        'vale_name_agent',
        'alpha',
        'code_ccee',
        'name_ccee',
        'name_profile',
        'status'
    ]

    rest = generic_data_csv_list(rest, ['agents_detail'])
    rest_data = []

    type_format_number=0 if format_file=='pdf' else 1
    for index in range(len(rest)):
        kwargs = rest[index]
        new = {
            'code_ccee': validates_data_used_file(kwargs, ['code_ccee'], type_format_number), #number
            'name_ccee': validates_data_used_file(kwargs, ['name_ccee'], 0),
            'alpha': translate_language("field_response_"+( validates_data_used_file(kwargs, ['profile_ccee', 'alpha'], 0) ), request),
            'name_profile': validates_data_used_file(kwargs, ['profile_ccee', 'name_profile'], 0),
            'status': translate_language("field_status_"+( validates_data_used_file(kwargs, ['profile_ccee', 'status'], 0) ), request),

            'vale_name_agent': validates_data_used_file(kwargs, ['profile_ccee', 'agents_detail', 'vale_name_agent'], 0),
        }   
        rest_data.append(new)

    try:
        if format_file == 'csv':
            return generic_csv(mapping, header, rest_data, translate_language('label_profile_download', request) )
        elif format_file == 'xlsx':
            styles=[
                {
                    'fields': [
                        "code_ccee"
                    ], 
                    'number_format': '0'
                }
            ]
            return generic_xls(mapping, header, rest_data, translate_language('label_profile_download', request), styles)
        elif format_file == 'pdf':
            return generic_pdf(mapping, header, rest_data, translate_language('label_profile_download', request) )
        else:
            return Response({'error': translate_language_error('error_unknown_format_file', request)}, status=status.HTTP_400_BAD_REQUEST)
    except:  # pragma: no cover
        # just to protect endpoint
        return Response({'error':translate_language_error('error_undefined', request)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@check_module(modules.profile, [permissions.VIEW, permissions.EDITN1])
def session_log_basic_profile(request, pk, format=None):
    """
        List all logs about profile
    """

    kwargs = {'core': Profile, 'core_pk': 'id_profile', 'core+': [],
              'child': []}
    
    kwargsAux=generic_log_search_basic(generic_log_search(pk, **kwargs))    
    kwargs={'logs':kwargsAux}

    #ccee
    array_ccee=[]
    id_array=[]
    id_num=None
    kwargs = {'core': CceeDescription, 'core_pk': 'id_ccee', 'core+': [],
              'child': []}
    for items in kwargsAux:
        if items['PROFILE']:
            if items['PROFILE']['new_value']['id_ccee'] and items['PROFILE']['new_value']['alpha']:
                idCcee=items['PROFILE']['new_value']['id_ccee']
                alphaStatus=items['PROFILE']['new_value']['alpha']
                if type(alphaStatus)==dict:
                    if alphaStatus['value']!="S":
                        if type(idCcee)==dict:
                            id_num=idCcee['value']
                        else:
                            id_num=idCcee
                else:
                    if alphaStatus!="S":
                        if type(idCcee)==dict:
                            id_num=idCcee['value']
                        else:
                            id_num=idCcee

                if (id_num not in id_array) and id_num:
                    id_array.append(id_num)
                    for histoCcee in generic_log_search(id_num, **kwargs)['CCEE_DESCRIPTION']:
                        array_ccee.append(histoCcee)

    kwargs = {'core': Profile, 'core_pk': 'id_profile', 'core+': [],
              'child': []}
    geral=generic_log_search(pk, **kwargs).copy()
    geral['CCEE_DESCRIPTION']=array_ccee
    
    kwargsAux=generic_log_search_basic(geral)
    kwargs={'logs':kwargsAux}

    #statics

    #ccee Alpha
    array_ccee_alpha=[]
    ids_ccee = map(lambda x: 
        (x['PROFILE']['new_value']['id_ccee'].get('value')
        if type(x['PROFILE']['new_value']['id_ccee']) == dict
        else x['PROFILE']['new_value']['id_ccee'])if x['PROFILE'] else None,

        kwargs['logs'] )    
    array_ccee_alpha = CceeDescription.objects.filter(pk__in= ids_ccee)
    array_ccee_alpha = map(lambda x: { 'id_ccee': x.pk, 'name_ccee': x.name_ccee, 'code_ccee':x.code_ccee }, array_ccee_alpha)
    
    #agents    
    agents_array=[]
    ids_agent = map(lambda x:
        (x['PROFILE']['new_value']['id_agents'].get('value')
        if type(x['PROFILE']['new_value']['id_agents']) == dict
        else x['PROFILE']['new_value']['id_agents']) if x['PROFILE'] else None,
        kwargs['logs'])
    agents_array = Agents.objects.filter(pk__in= ids_agent)
    agents_array = map(lambda x: { 'id_agents': x.pk, 'vale_name_agent': x.vale_name_agent }, agents_array)    

    kwargs['statics_relateds']={'Agents':agents_array, 'Ccee_alpha':array_ccee_alpha}
    return Response(kwargs)



def function_find_generic(request):
    kwargs = {
        'vale_name_agent': 'id_agents__vale_name_agent__contains',
        'alpha': 'alpha',
        'code_ccee': 'id_ccee__code_ccee__contains',
        'name_ccee': 'id_ccee__name_ccee__contains', 
        'name_profile': 'name_profile__contains',
        'status_profile':'status__contains'
    }
    kwargs_order = {
        'vale_name_agent': 'id_agents__vale_name_agent',
        'alpha': 'alpha',
        'code_ccee': 'id_ccee__code_ccee',
        'name_ccee': 'id_ccee__name_ccee', 
        'name_profile': 'name_profile',
        'status_profile':'status',

        '-vale_name_agent': '-id_agents__vale_name_agent',
        '-alpha': '-alpha',
        '-code_ccee': '-id_ccee__code_ccee',
        '-name_ccee': '-id_ccee__name_ccee', 
        '-name_profile': '-name_profile',
        '-status_profile':'-status'
    }
    ids = generic_queryset_filter(request, Profile, 'id_ccee', **kwargs)
    if request.query_params.get('ordering') in kwargs_order:
        order_by = kwargs_order[request.query_params.get('ordering')]
    else:
        order_by = kwargs_order['name_ccee']
    
    profile_object = Profile.objects\
        .select_related('id_ccee').select_related('id_agents')\
        .filter(id_ccee__in=ids).order_by(order_by)
    return profile_object

def function_formart_return_find(request, data):
    observation_log = ""
    if 'observation_log' in request.data:
        observation_log = request.data['observation_log']

    serializer_context = {
        'request': request,
        'observation_log': observation_log
    }
    serializer=[]
    for item in data:
        try:
            itemJson=CCEESerializerProfileFindBasic(item.id_ccee, many=False, context=serializer_context).data
            profile_ccee=ProfileSerializerFindBasic(item, many=False, context=serializer_context).data
            agents_detail=AgentsSerializerFindBasic(item.id_agents, many=False, context=serializer_context).data
            itemJson['profile_ccee']=profile_ccee
            itemJson['profile_ccee']['agents_detail']=agents_detail
        except:
            itemJson = CCEESerializerProfile(data.id_ccee, many=False, context=serializer_context).data

        serializer.append(itemJson)

    return serializer