import json
from core.attachment_utility import generic_data_csv_list, generic_csv, generic_pdf, generic_xls
from core.models import CceeDescription
from gauge_point.serializers import GaugePointSerializer, UpstreamMeterSerializer, CCEESerializer, GaugeCompanyView, \
    SourcePmeSerializer, GaugePointSerializerViewDetail, \
    CompanySerializerDealershipView, GaugePointSerializerFindBasic, GaugeEnergyDealershipSerializerFindBasic, \
    GaugeTypeSerializer, MeterTypeSerializer, UpstreamMeterSerializerFindBasic, CCEESerializerFindBasic
from rest_framework import viewsets, status, serializers
from rest_framework.decorators import api_view
from rest_framework.response import Response
from gauge_point.models import GaugePoint, UpstreamMeter, SourcePme, GaugeEnergyDealership, Company, \
    GaugeType, MeterType
from energy_composition.models import PointComposition
import collections
from core.views import generic_log_search, generic_paginator, generic_queryset_filter, generic_detail_log, \
    generic_log_search_basic, validates_data_used_file
from django.db.models import FilteredRelation, Q, Prefetch
from itertools import chain
from django.db import connection
from django.db.models import Prefetch
from locales.translates_function import translate_language_header, translate_language, translate_language_error, translate_language_log
from core.serializers import generic_validation_changed
from organization.serializersViews import OrganizationAgrupationEletrictSerializerView
from organization.models import ElectricalGrouping

from SmartEnergy.auth import check_module
import SmartEnergy.auth.permissions as permissions
import SmartEnergy.auth.modules as modules

@api_view(['GET'])
@check_module(modules.gauge_point, [permissions.VIEW, permissions.EDITN1])
def validated_using(request, pk, format=None):
    kwargs = {UpstreamMeter: 'id_gauge', PointComposition: 'id_gauge', UpstreamMeter:'id_upstream_meter'}
    status_message=generic_validation_changed(pk, GaugePoint, kwargs, request)
    if status_message != 'S':
        return Response(status_message, status=status.HTTP_400_BAD_REQUEST)
    return Response(status_message, status=status.HTTP_200_OK)

class GaugePointViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Gauge Point monipulation
    """
    queryset = GaugePoint.objects.all()
    serializer_class = GaugePointSerializerViewDetail


# get source pme
@api_view(['GET'])
@check_module(modules.gauge_point, [permissions.VIEW, permissions.EDITN1])
def get_data_source_pme(request, format=None):
    """
        List all source pme
    """
    serializer_context = {
        'request': request,

    }
    try:
        if request.method == 'GET':
            kwargs = {
                'source': 'display_name__contains', 
                'description': 'description__contains',
                'id_meter_type': 'id_meter_type',
            }
            ids = generic_queryset_filter(request, SourcePme, 'id_source', **kwargs)
            
            source_filtered = SourcePme.objects.filter(id_source__in=ids, gauge_source__isnull= True).order_by('display_name')
            if request.query_params.get('id_gauge'):
                gauge = GaugePoint.objects.get(pk = request.query_params.get('id_gauge'))
                source_related_gauge = SourcePme.objects.get(id_source = gauge.id_source_id)
                source = list(chain([source_related_gauge], source_filtered))
            else:
                source = source_filtered
            
            serializer = SourcePmeSerializer(source, many=True, context=serializer_context)
            return Response(serializer.data)

    except SourcePme.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)


# company related gauge
@api_view(['GET'])
@check_module(modules.gauge_point, [permissions.VIEW, permissions.EDITN1])
def session_gauge_company(request, format=None):
    """
        List all gauge/company or create a new gauge point
    """
    observation_log = ""
    if 'observation_log' in request.data:
        observation_log = request.data['observation_log']
    try:
        if request.method == 'GET':
            kwargs = {'gauge_type': 'gauge_type__contains',
                      'id_gauge_type': 'id_gauge_type', 
                      'id_meter_type': 'id_source__id_meter_type', 
                      'tag': 'id_source__display_name__contains',
                      'company_name': 'id_company__company_name__contains',
                      'status': 'status__contains', 'CCEE': 'id_ccee__name_ccee__contains',
                      'dealership': 'gauge_dealership__id_dealership__company_name__contains'}

            ids = generic_queryset_filter(request, GaugePoint, 'id_gauge', **kwargs)
            id_gauge = request.query_params.get('id_gauge')

            # not gauge company related himself
            if id_gauge and id_gauge in (ids):
                ids.pop(ids.index(id_gauge))

            gauge = GaugePoint.objects.values('id_company_id', 'id_company__company_name')\
                .filter(id_gauge__in=ids, id_gauge_type__isnull=False, status='S').order_by(
                'id_company__company_name').distinct()

            return Response(gauge)

    except GaugePoint.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@check_module(modules.gauge_point, [permissions.VIEW, permissions.EDITN1])
def session_gauge_point_find_basic(request, format=None):
    """
        List all gauge or create a new gauge point
    """
    if request.method == 'GET':
        gauge = kwargs_and_kwargs_order_format_for_find(request)
        
        data, page_count, page_next, page_previous = generic_paginator(request, gauge)
        serializer = function_find_format_return(request, data)
        response = collections.OrderedDict([
            ('count', page_count),
            ('next', page_next),
            ('previous', page_previous),
            ('results', serializer)
        ])
        return Response(response, status=status.HTTP_200_OK)


@api_view(['GET'])
@check_module(modules.gauge_point, [permissions.VIEW, permissions.EDITN1])
def session_gauge_point_get(request, format=None):
    """
        List all gauge or create a new gauge point
    """
    if request.method == 'GET':
        observation_log = ""
        if 'observation_log' in request.data:
            observation_log = request.data['observation_log']
        serializer_context = {
            'request': request,
            'observation_log': observation_log
        }

        gauge = kwargs_and_kwargs_order_format_for_find(request)
        data, page_count, page_next, page_previous = generic_paginator(request, gauge)
        serializer = GaugePointSerializerViewDetail(data, many=True, context=serializer_context)
        response = collections.OrderedDict([
            ('count', page_count),
            ('next', page_next),
            ('previous', page_previous),
            ('results', serializer.data)
        ])
        return Response(response)

@api_view(['POST'])
@check_module(modules.gauge_point, [permissions.EDITN1])
def session_gauge_point_post(request, format=None):
    """
        List all gauge or create a new gauge point
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
        try:
            meter_type_source = SourcePme.objects.get(id_source=data['id_source']).id_meter_type_id
        except SourcePme.DoesNotExist:
            return Response("id_source invalid",status=status.HTTP_400_BAD_REQUEST)

        if (data['ccee_gauge'].get("code_ccee") != "" and data['ccee_gauge'].get("code_ccee") != None) and (data['id_gauge_type']!=1 or meter_type_source!=1):
            return Response(translate_language_error('error_disable_gauge_ccee', request), status=status.HTTP_400_BAD_REQUEST)
        else:
            serializer_ccee = CCEESerializer(data=data['ccee_gauge'], context=serializer_context)
            if serializer_ccee.is_valid():
                serializer_ccee.save()
                data['id_ccee'] = serializer_ccee.data['id_ccee']
            else:
                return Response(serializer_ccee.errors, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = GaugePointSerializer(data=data, context=serializer_context)
        if serializer.is_valid():
            serializer.save()
            ids_upstream = []
            pk = serializer.data['id_gauge']
            gauge = GaugePoint.objects.get(pk=pk)
            if 'upstream' in data:
                upstream = data['upstream']
                response_error = {}
                for data_upstream in upstream:
                    data_upstream['id_gauge'] = pk
                    data_serializer = UpstreamMeterSerializer(data=data_upstream, context=serializer_context)
                    if data_serializer.is_valid():
                        data_serializer.save()
                        ids_upstream.append(data_serializer.data['id_upstream'])
                    else:
                        response_error = data_serializer.errors

                    if response_error:
                        for upstream in UpstreamMeter.objects.filter(id_upstream__in=ids_upstream):
                            upstream.delete()
                        GaugeEnergyDealership.objects.get(id_gauge_point=pk).delete()
                        gauge.delete()
                        if data['ccee_gauge'].get("code_ccee") != "" and data['id_gauge_type']==1 and meter_type_source==1:
                            serializer_ccee.instance.delete()
                        return Response(response_error, status=status.HTTP_400_BAD_REQUEST)
                serializer = GaugePointSerializerViewDetail(gauge, context=serializer_context)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            if data['ccee_gauge'].get("code_ccee") != "" and data['id_gauge_type']==1 and meter_type_source==1:
                serializer_ccee.instance.delete() 
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT'])
@check_module(modules.gauge_point, [permissions.EDITN1])
def session_gauge_point_put(request, pk, format=None):
    """
        Retrieve, update or delete a specific gauge point.
    """
    observation_log = ""
    if 'observation_log' in request.data:
        observation_log = request.data['observation_log']

    serializer_context = {
        'request': request,
        'observation_log': observation_log
    }
    try:
        #gauge = GaugePoint.objects.get(pk=pk)
        gauge = GaugePoint.objects.prefetch_related(Prefetch(
            'gauge_chield',
            queryset=UpstreamMeter.objects.filter(status='S')
        )).get(pk=pk)
        
    except GaugePoint.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'PUT':
        data = request.data
        meter_type_source = SourcePme.objects.get(id_source=data['id_source']).id_meter_type_id

        if (data['ccee_gauge'] and 'code_ccee' in data['ccee_gauge']) and (data['ccee_gauge']['code_ccee']!="" and data['ccee_gauge']['code_ccee'] !=None) and (data['id_gauge_type']!=1 or meter_type_source!=1):
            return Response(translate_language_error('error_disable_gauge_ccee', request), status=status.HTTP_400_BAD_REQUEST)
        
        # Update
        if GaugePoint.objects.get(pk=pk).id_ccee:
            data['ccee_gauge']={
                'id_ccee':GaugePoint.objects.get(pk=pk).id_ccee_id,
                'code_ccee': (data['ccee_gauge']['code_ccee']) if 'code_ccee' in data['ccee_gauge'] else ("")
            }
            ccee = CceeDescription.objects.get(pk=data['ccee_gauge']['id_ccee'])
            serializer_ccee = CCEESerializer(ccee, data=data['ccee_gauge'], context=serializer_context)            
            if serializer_ccee.is_valid():
                serializer_ccee.save()
            else:
                return Response(serializer_ccee.errors, status=status.HTTP_400_BAD_REQUEST)
        # insert
        else: # pragma: no cover
            data['ccee_gauge']={'code_ccee': data['ccee_gauge']['code_ccee']}if data['ccee_gauge'] and 'code_ccee' in data['ccee_gauge'] else {'code_ccee': ""}
            serializer_ccee = CCEESerializer(data=data['ccee_gauge'], context=serializer_context)
            if serializer_ccee.is_valid():
                serializer_ccee.save()
                data['id_ccee']=serializer_ccee.instance.pk
            else:
                return Response(serializer_ccee.errors, status=status.HTTP_400_BAD_REQUEST)


        serializer = GaugePointSerializer(gauge, data=data, context=serializer_context)
        if serializer.is_valid():
            serializer.save()
            def disable_upstreams(ups_meter_for_disable):
                for ups_meter in ups_meter_for_disable:
                    dict_ups = {
                        'id_upstream_meter': ups_meter.id_upstream_meter_id,
                        'id_gauge': ups_meter.id_gauge_id,
                        'status': 'N'
                    }
                    ups_serializer = UpstreamMeterSerializer(ups_meter, data=dict_ups, context=serializer_context)
                    if ups_serializer.is_valid():
                        ups_serializer.save()
                    else:
                        raise serializers.ValidationError(ups_serializer.errors)

            if 'upstream' in data:
                ids_upstreams = []
                for data in data['upstream']:
                    upstream = None
                    if 'id_upstream' in data:
                        upstream = UpstreamMeter.objects.get(id_upstream=data['id_upstream'])
                    else:
                        try:
                            upstream = UpstreamMeter.objects.get(id_upstream_meter=data['id_upstream_meter'],
                                                                 id_gauge=serializer.data['id_gauge'], status='S')
                        except UpstreamMeter.DoesNotExist:
                            upstream = None
                    data['id_gauge'] = serializer.data['id_gauge']
                    if upstream:
                        # Update
                        data_serializer = UpstreamMeterSerializer(upstream, data=data, context=serializer_context)
                    else:
                        # Insert
                        data_serializer = UpstreamMeterSerializer(data=data, context=serializer_context)
                    if data_serializer.is_valid():
                        data_serializer.save()
                    else:
                        return Response(data_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                    ids_upstreams.append(data_serializer.data['id_upstream'])
                disable_upstreams(UpstreamMeter.objects.filter(id_gauge=serializer.data['id_gauge'],
                                                               status='S').exclude(id_upstream__in=ids_upstreams))
            else:
                # Disable all relations
                if data['status']!=GaugePoint.objects.get(pk=data['id_gauge']).status:
                    disable_upstreams(UpstreamMeter.objects.filter(id_gauge=serializer.data['id_gauge'], status='S'))

            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@check_module(modules.gauge_point, [permissions.VIEW, permissions.EDITN1])
def session_gauge_point_get_detail(request, pk, format=None):
    """
        Retrieve, update or delete a specific gauge point.
    """
    observation_log = ""
    if 'observation_log' in request.data:
        observation_log = request.data['observation_log']

    serializer_context = {
        'request': request,
        'observation_log': observation_log
    }
    try:
        #gauge = GaugePoint.objects.get(pk=pk)
        gauge = GaugePoint.objects.prefetch_related(Prefetch(
            'gauge_chield',
            queryset=UpstreamMeter.objects.filter(status='S')
        )).get(pk=pk)
        
    except GaugePoint.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = GaugePointSerializerViewDetail(gauge, context=serializer_context)
        return Response(serializer.data)


@api_view(['GET'])
@check_module(modules.gauge_point, [permissions.VIEW, permissions.EDITN1])
def session_gauge_point_file(request):
    if not (request.query_params.get('format_file', None) is None):
        format_file = request.query_params.get('format_file', None)
    else:
        return Response({'error': translate_language_error('error_format_file_csv_or_pdf', request) }, status=status.HTTP_400_BAD_REQUEST)

    gauge = kwargs_and_kwargs_order_format_for_find(request)
    serializer = function_find_format_return(request, gauge)

    payload = serializer
    payload = json.dumps(payload, indent=10, default=str).encode('utf-8')
    rest = json.loads(payload)
    # let empty to use de mapping (original) names: header = {}
    # must be in the same order of mapping
    header = {
        'meter_type': 'field_meter_type',
        'gauge_type': 'field_gauge_type',
        'display_name': 'field_display_meter',
        'company_name': 'field_company_name',
        'electrical_grouping': 'field_electrical_grouping',
        'connection_point': 'field_connection_point',
        'company_name_dealership': 'field_dealership',
        'id_ccee': 'ccee_code',
        'participation_sepp': 'field_participation_sepp',
        'status': 'field_gauge_status',
        'display_name_upstream': 'field_upstream_measuring_points',
    }
    header = translate_language_header(header, request)
    mapping = [
        'meter_type',
        'gauge_type',
        'display_name',
        'company_name',
        'electrical_grouping',
        'connection_point',
        'company_name_dealership',
        'id_ccee',
        'participation_sepp',
        'status',
        'display_name_upstream'
    ]
    rest = generic_data_csv_list(rest, ['upstream'])
    rest_data = []
    for index in range(len(rest)):
        kwargs = rest[index]
        new = {
            'meter_type': validates_data_used_file(kwargs, ['source_detail', 'meter_type_detail', 'description'], 0),
            'gauge_type': validates_data_used_file(kwargs, ['gauge_type_detail', 'description'], 0),
            'display_name': validates_data_used_file(kwargs, ['source_detail', 'display_name'], 0),

            'company_name': validates_data_used_file(kwargs, ['company_detail', 'company_name'], 0),
            'connection_point': validates_data_used_file(kwargs, ['connection_point'], 0),

            'company_name_dealership': validates_data_used_file(kwargs, ['gauge_dealership', 'company_dealership', 'company_name'], 0),
            'id_ccee': validates_data_used_file(kwargs, ['ccee_gauge', 'code_ccee'], 0),
            'electrical_grouping': validates_data_used_file(kwargs, ['electrical_grouping_detail', 'description'], 0) ,
            
            'participation_sepp': translate_language("field_response_"+validates_data_used_file(kwargs, ['participation_sepp'], 0), request),
            'status': translate_language("field_status_"+validates_data_used_file(kwargs, ['status'], 0), request),

            'display_name_upstream': validates_data_used_file(kwargs, ['upstream', 'source_detail.display_name'], 0)
        }
            
        rest_data.append(new)

    try:
        if format_file == 'csv':
            return generic_csv(mapping, header, rest_data, translate_language("label_gaugePoint_download", request) )
        elif format_file == 'xlsx':
            styles=[]
            return generic_xls(mapping, header, rest_data, translate_language("label_gaugePoint_download", request), styles)
        elif format_file == 'pdf':
            return generic_pdf(mapping, header, rest_data, translate_language("label_gaugePoint_download", request) )
        else:
            return Response({'error': translate_language_error('error_unknown_format_file', request) }, status=status.HTTP_400_BAD_REQUEST)
    except:  # pragma: no cover
        # just to protect endpoint
        return Response({'error': translate_language_error('error_undefined', request) }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@check_module(modules.gauge_point, [permissions.VIEW, permissions.EDITN1])
def session_log_basic_gauge_point(request, pk, format=None):
    """
        List all logs about gauge_point
    """

    kwargs = {'core': GaugePoint, 'core_pk': 'id_gauge',
              'core+': [{CceeDescription: 'id_ccee'}, {GaugeEnergyDealership: 'id_gauge_point'}],
              'child': []}
    log = generic_log_search(pk, **kwargs)

    kwargs = {'core': UpstreamMeter, 'core_pk': 'id_upstream',
              'core+': [],
              'child': []}
    array = []
    for a in UpstreamMeter.objects.filter(id_gauge=pk):
        array.append(generic_log_search(a.id_upstream, **kwargs))
    kwargs = log.copy()
    new_upstream = []
    for index in range(len(array)):
        for indexIntern in range(len(array[index]['UPSTREAM_METER'])):
            new_upstream.append(array[index]['UPSTREAM_METER'][indexIntern])
    kwargs['upstream'] = new_upstream

    kwargsAux = generic_log_search_basic(kwargs)
    kwargs = {'logs': kwargsAux}

    ids_arrays = []
    # company
    company_Array = []
    for items in kwargsAux:
        try:  # to be improoved
            if items['gauge_point']['new_value']['id_company']:
                a = items['gauge_point']['new_value']['id_company']
                if 'value' in a:
                    id_num = a['value']
                else:
                    id_num = a

                if id_num not in ids_arrays:
                    ids_arrays.append(id_num)
                    company_Array.append(
                        {'id_company': id_num, 'company_name': Company.objects.get(pk=id_num).company_name})
        except:
            pass

        try:  # to be improoved
            if items['GAUGE_ENERGY_DEALERSHIP']['new_value']['id_dealership']:
                a = items['GAUGE_ENERGY_DEALERSHIP']['new_value']['id_dealership']
                if 'value' in a:
                    id_num = a['value']
                else:
                    id_num = a

                if id_num not in ids_arrays:
                    ids_arrays.append(id_num)
                    company_Array.append(
                        {'id_company': id_num, 'company_name': Company.objects.get(pk=id_num).company_name})
        except:
            pass
    # SourcePME
    source_Array = []
    ids_arrays.clear()
    for items in kwargsAux:
        try:
            if items['gauge_point']['new_value']['id_source']:
                a = items['gauge_point']['new_value']['id_source']
                if 'value' in a:
                    id_num = a['value']
                else:
                    id_num = a

                if id_num not in ids_arrays:
                    ids_arrays.append(id_num)
                    obj_source =SourcePme.objects.filter(pk=id_num).select_related('id_meter_type').first()
                    source_Array.append({
                        'id_source': id_num, 
                        'source_name': obj_source.display_name, 
                        'meter_type': translate_language(obj_source.id_meter_type.description, request),
                        'id_meter_type': obj_source.id_meter_type_id
                    })
        except:
            pass
    # upstream_name
    upstream_array = []
    ids_arrays.clear()
    for items in kwargsAux:
        try:
            if type(items['upstream']) == dict:
                if items['upstream']['new_value']['id_upstream_meter']:
                    a = items['upstream']['new_value']['id_upstream_meter']
                    if a not in ids_arrays:
                        ids_arrays.append(a)
                        upstream_array.append(
                            {'id_upstream': a, 'upstream_name': (GaugePoint.objects.get(pk=a).id_source).display_name})

            else:
                for itemIntern in items['upstream']:
                    if itemIntern['new_value']['id_upstream_meter']:
                        a = itemIntern['new_value']['id_upstream_meter']
                        if a not in ids_arrays:
                            ids_arrays.append(a)
                            upstream_array.append({'id_upstream': a, 'upstream_name': (
                                GaugePoint.objects.get(pk=a).id_source).display_name})
        except:
            pass
    # electrical_grouping
    ids_arrays.clear()
    electrical_grouping_Array = []
    for items in kwargsAux:
        try:  # to be improoved
            if items['gauge_point']['new_value']['id_electrical_grouping']:
                a = items['gauge_point']['new_value']['id_electrical_grouping']
                if 'value' in a:
                    id_num = a['value']
                else:
                    id_num = a

                if id_num not in ids_arrays:
                    ids_arrays.append(id_num)
                    electrical_grouping_Array.append(
                        {'id_electrical_grouping': id_num, 'description': ElectricalGrouping.objects.get(pk=id_num).description})
        except:
            pass

    #Traduction
    for items in kwargs['logs']:
        if 'gauge_point' in items and items['gauge_point']:
            if items['gauge_point']['old_value']:
                items['gauge_point']['old_value']['gauge_type']= translate_language_log(items['gauge_point']['old_value']['gauge_type'], request)
            if items['gauge_point']['new_value']:
                if type(items['gauge_point']['new_value']['gauge_type'])==dict:
                    value=items['gauge_point']['new_value']['gauge_type']['value']
                    items['gauge_point']['new_value']['gauge_type']['value']= translate_language_log(value, request)
                else:
                    items['gauge_point']['new_value']['gauge_type']= translate_language_log(items['gauge_point']['new_value']['gauge_type'], request)

    serializerGaugeType = GaugeTypeSerializer(GaugeType.objects.all(), many=True, context=request).data
    kwargs['statics_relateds'] = {'Company': company_Array, 'source': source_Array, 'upstream': upstream_array, 
        'gauge_type': serializerGaugeType, 'electrical_grouping':electrical_grouping_Array}
    return Response(kwargs)

@api_view(['GET'])
@check_module(modules.gauge_point, [permissions.VIEW, permissions.EDITN1])
def session_show_gauge_type(request, format=None):
    serializerGaugeType = GaugeTypeSerializer (GaugeType.objects.all(), many=True, context=request).data
    return Response(serializerGaugeType, status=status.HTTP_200_OK)

@api_view(['GET'])
@check_module(modules.gauge_point, [permissions.VIEW, permissions.EDITN1])
def session_show_meter_type(request, format=None):
    serializerMeterType=MeterTypeSerializer(MeterType.objects.all(), many=True, context=request).data
    return Response(serializerMeterType, status=status.HTTP_200_OK)

####functions responsible for searches
def kwargs_and_kwargs_order_format_for_find(request):
    kwargs = {
        'gauge_type': 'gauge_type',
        'id_gauge_type': 'id_gauge_type',
        'id_meter_type': 'id_source__id_meter_type',
        'connection_point': 'connection_point__contains',
        'id_electrical_grouping': 'id_electrical_grouping__description__contains',
        'display_name': 'id_source__display_name__contains',
        'company_name': 'id_company__company_name__contains',
        'code_ccee': 'id_ccee__code_ccee',
        'gauge_dealership': 'gauge_dealership__id_dealership__company_name__contains',
        'status': 'status__contains',
        'id_company': 'id_company_id',
    }

    kwargs_order = {
        'gauge_type': 'gauge_type',
        'id_gauge_type': 'id_gauge_type__description',
        'id_meter_type': 'id_source__id_meter_type__description',
        'connection_point': 'connection_point',
        'id_electrical_grouping': 'id_electrical_grouping__description',
        'display_name': 'id_source__display_name',
        'company_name': 'id_company__company_name',
        'code_ccee': 'id_ccee__code_ccee',
        'gauge_dealership': 'gauge_dealership__id_dealership__company_name',
        'status': 'status',

        'gauge_type': 'gauge_type',
        '-id_gauge_type': '-id_gauge_type__description',
        '-id_meter_type': '-id_source__id_meter_type__description',
        '-connection_point': '-connection_point',
        '-id_electrical_grouping': '-id_electrical_grouping__description',
        '-display_name': '-id_source__display_name',
        '-company_name': '-id_company__company_name',
        '-code_ccee': '-id_ccee__code_ccee',
        '-gauge_dealership': '-gauge_dealership__id_dealership__company_name',
        '-status': '-status',
    }
    if request.query_params.get('ordering') in kwargs_order:
        order_by = kwargs_order[request.query_params.get('ordering')]
    else:
        order_by = kwargs_order['gauge_type']
    
    ids = generic_queryset_filter(request, GaugePoint, 'id_gauge', **kwargs)
    gauge = GaugePoint.objects \
        .select_related('id_company').select_related('id_source').select_related('id_ccee') \
        .select_related('id_gauge_type').select_related('id_source__id_meter_type').select_related('id_electrical_grouping') \
        .prefetch_related('gauge_dealership').prefetch_related('gauge_dealership__id_dealership')\
        .prefetch_related('gauge_chield').prefetch_related('gauge_chield__id_upstream_meter')\
        .prefetch_related('gauge_chield__id_upstream_meter__id_source')\
        .filter(id_gauge__in=ids).order_by(order_by)
    return gauge

def function_find_format_return(request, gauge):
    serializer_context = request
    try:
        serializer=[]
        for item in gauge:
            itemJson = GaugePointSerializerFindBasic(item, many=False, context=serializer_context).data
            itemJson['gauge_dealership']=None
            if hasattr(item, 'gauge_dealership'):
                itemJson['gauge_dealership']=GaugeEnergyDealershipSerializerFindBasic(item.gauge_dealership, many=False, context=serializer_context).data
                itemJson['gauge_dealership']['company_dealership'] = CompanySerializerDealershipView(item.gauge_dealership.id_dealership, many=False, context=serializer_context).data if hasattr(item.gauge_dealership, 'id_dealership') else None
            itemJson['gauge_type_detail'] = GaugeTypeSerializer(item.id_gauge_type, many=False, context=serializer_context).data
            itemJson['electrical_grouping_detail'] = OrganizationAgrupationEletrictSerializerView(item.id_electrical_grouping, many=False, context=serializer_context).data
            itemJson['upstream']=[]     
            if hasattr(item, 'gauge_chield'):
                for item_upstream in item._prefetched_objects_cache['gauge_chield']:
                    if item_upstream.status=='S':
                        item_json_upstrem=UpstreamMeterSerializerFindBasic(item_upstream, many=False ,context=serializer_context).data
                        item_json_upstrem['source_detail']= SourcePmeSerializer(item_upstream.id_upstream_meter.id_source, many=False, context=serializer_context).data
                        itemJson['upstream'].append(item_json_upstrem)

            itemJson['company_detail']=CompanySerializerDealershipView(item.id_company, many=False, context=serializer_context).data
            itemJson['source_detail']=SourcePmeSerializer(item.id_source, many=False, context=serializer_context).data
            itemJson['source_detail']['meter_type_detail'] = MeterTypeSerializer(item.id_source.id_meter_type, many=False, context=serializer_context).data if item.id_source else ""
            itemJson['ccee_gauge']=CCEESerializerFindBasic(item.id_ccee, many=False, context=serializer_context).data
            
            serializer.append(itemJson)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    return serializer