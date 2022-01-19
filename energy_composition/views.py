import json
from organization.models import ProductionPhase
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.forms import model_to_dict
from django.core.serializers.json import DjangoJSONEncoder
from core.attachment_utility import generic_data_csv_list, generic_csv, generic_pdf, generic_xls
from energy_composition.models import EnergyComposition, DirectorBoard, Business, Segment, Product, AccountantArea, \
    ApportiomentComposition, PointComposition
from gauge_point.models import GaugePoint
from gauge_point.serializers import GaugePointSerializerFindBasic, SourcePmeSerializer
from energy_composition.serializers import EnergyCompositionSerializer, PointCompositionSerializerViewBasic, ApportiomentCompositionSerializerViewBasic, EnergyCompositionSerializerViewBasic
from core.views import generic_paginator, generic_queryset_filter, generic_log_search, \
    generic_detail_log, generic_log_search_basic, validates_data_used_file
import collections
from company.models import Company
from core.serializers import log
from locales.translates_function import translate_language_header, translate_language, translate_language_error
from SmartEnergy.auth import check_module
import SmartEnergy.auth.permissions as permissions
import SmartEnergy.auth.modules as modules

# Create your views here.
@api_view(['GET'])
@check_module(modules.energy_composition, [permissions.VIEW, permissions.EDITN1])
def session_energy_composition_get(request, format=None):
    """
        List all composition
    """
    observation_log = ""
    if 'observation_log' in request.data:
        observation_log = request.data['observation_log']

    serializer_context = {
        'request': request,
        'observation_log': observation_log
    }

    if request.method == 'GET':
        energy_composition=function_find_generic(request)
        data, page_count, page_next, page_previous = generic_paginator(request, energy_composition)
        serializer = EnergyCompositionSerializer(data, many=True, context=serializer_context)
        response = collections.OrderedDict([
            ('count', page_count),
            ('next', page_next),
            ('previous', page_previous),
            ('results', serializer.data)
        ])
        return Response(response)

@api_view(['GET'])
@check_module(modules.energy_composition, [permissions.VIEW, permissions.EDITN1])
def session_energy_composition_get_basic_find(request, format=None):
    """
        List all composition
    """
    if request.method == 'GET':
        energy_composition = function_find_generic(request)
        data, page_count, page_next, page_previous = generic_paginator(request, energy_composition)
        serializer = function_format_result_for_find(request, data)
        response = collections.OrderedDict([
            ('count', page_count),
            ('next', page_next),
            ('previous', page_previous),
            ('results', serializer)
        ])
        return Response(response)

@api_view(['POST'])
@check_module(modules.energy_composition, [permissions.EDITN1])
def session_energy_composition_post(request, format=None):
    """
        create a new energy composition.
    """
    observation_log = ""
    if 'observation_log' in request.data:
        observation_log = request.data['observation_log']

    serializer_context = {
        'request': request,
        'observation_log': observation_log
    }
    if request.method == 'POST':
        serializer = EnergyCompositionSerializer(data=request.data, context=serializer_context)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT'])
@check_module(modules.energy_composition, [permissions.EDITN1])
def session_energy_composition_put(request, pk, format=None):
    """
        Retrieve, update or delete a specific energy composition.
    """
    observation_log = ""
    if 'observation_log' in request.data:
        observation_log = request.data['observation_log']

    serializer_context = {
        'request': request,
        'observation_log': observation_log
    }
    try:
        energy_composition = EnergyComposition.objects.get(pk=pk)
    except EnergyComposition.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'PUT':
        data = request.data
        if data:
            id_energy_composition = data['id_energy_composition']
            try:
                data['apport_energy_composition'] = list(
                    filter(lambda x: len(x) > 0 and x['id_company'] != '', data['apport_energy_composition']))
                apportitems = ApportiomentComposition.objects.filter(id_energy_composition=id_energy_composition, status='S')
                apport_ids = list(map(lambda x: x.get('id_apport'), data['apport_energy_composition']))
                for apport in apportitems:
                    # if record was deleted
                    if apport.id_apport not in apport_ids:
                        # logical exclusion
                        sel_apport = json.loads(json.dumps(model_to_dict(apport), cls=DjangoJSONEncoder))
                        sel_apport['status'] = 'N'
                        data['apport_energy_composition'].append(sel_apport)

                points_composition = PointComposition.objects.filter(id_energy_composition=id_energy_composition)
                point_ids = list(map(lambda x: x.get('id_point_composition'), data['point_energy_composition']))
                for point in points_composition:
                    # if record was deleted
                    if point.id_point_composition not in point_ids:
                        # Fisical exclusion
                        log(PointComposition, point.id_point_composition, {}, point, request.user,
                            observation_log, action="DELETE")
                        point.delete()

            except KeyError as e:
                kwargs = {'contacts:': e}
                return Response(collections.OrderedDict(kwargs), status=status.HTTP_400_BAD_REQUEST)               

        serializer = EnergyCompositionSerializer(energy_composition, data=data, context=serializer_context)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@check_module(modules.energy_composition, [permissions.VIEW, permissions.EDITN1])
def session_energy_composition_get_detail(request, pk, format=None):
    """
        specific energy composition.
    """
    observation_log = ""
    if 'observation_log' in request.data:
        observation_log = request.data['observation_log']

    serializer_context = {
        'request': request,
        'observation_log': observation_log
    }
    try:
        energy_composition = EnergyComposition.objects.get(pk=pk)
    except EnergyComposition.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = EnergyCompositionSerializer(energy_composition, context=serializer_context)
        return Response(serializer.data)

@api_view(['GET'])
@check_module(modules.energy_composition, [permissions.VIEW, permissions.EDITN1])
def session_energy_composition_file(request):
    if not (request.query_params.get('format_file', None) is None):
        format_file = request.query_params.get('format_file', None)
    else:
        return Response({'error': translate_language_error('error_format_file_csv_or_pdf', request) }, status=status.HTTP_400_BAD_REQUEST)

    energy_composition = function_find_generic(request)
    serializer = function_format_result_for_find(request, energy_composition)

    payload = json.dumps(serializer, indent=4, default=str).encode('utf-8')
    rest = json.loads(payload)

    header = {
                'composition_name': 'field_name' ,
                'cost_center': 'field_cost_center',
                'company_name': 'field_company_name',
                'business': 'field_business',
                'director': 'field_directorBoard',
                'segment': 'field_segment',
                'accountantarea': 'field_accountantArea',
                'profit_center': 'field_profitCenter', 
                'composition_loss': 'field_composition_loss',
                'description': 'field_description',
                'status': 'field_status_energy',
                'company_name_apport': 'field_company_name_apportionment',
                'volume_code': 'field_volume_code',
                'cost_code': 'field_cost_code', 
                'status_apport': 'field_status_apportionment',
                'display_name': 'field_display_meter',
                'kpi_formulae': 'field_formula',
                'gauge_point_destination': 'field_gauge_point_destination',
                "id_production_phase": "field_production_phase",
                "data_source": "field_data_source",
        }
    header = translate_language_header(header, request)
    mapping = [
        'composition_name', 
        'cost_center',
        'company_name',
        'business',
        'director',
        'segment',
        'accountantarea', 
        'profit_center',
        'composition_loss', 
        'description', 
        'status', 
        'company_name_apport', 
        'volume_code', 
        'cost_code', 
        'status_apport', 
        'display_name',
        'kpi_formulae',
        'gauge_point_destination',
        'id_production_phase',
        'data_source',
    ]
    rest = generic_data_csv_list(rest, ['apport_energy_composition', 'point_energy_composition'])
    rest_data = []

    gauges_formule=GaugePoint.objects.filter(point_gauge__isnull=False).select_related('id_source')

    type_format_number=0 if format_file=='pdf' else 1
    for index in range(len(rest)):
        kwargs = rest[index]
        new = {
            'composition_name': validates_data_used_file(kwargs, ['composition_name'], 0),
            'kpi_formulae': formattedFomuleKpi(validates_data_used_file(kwargs, ['kpi_formulae'], 0), gauges_formule),
            'status': translate_language("field_status_"+( validates_data_used_file(kwargs, ['status'], 0) ), request),
            'description': validates_data_used_file(kwargs, ['description'], 0),
            'company_name': validates_data_used_file(kwargs, ['energy_detail', 'company_name'], 0),
            'accountantarea': validates_data_used_file(kwargs, ['energy_detail', 'accountantarea'], 0),
            'director': validates_data_used_file(kwargs, ['energy_detail', 'director'], 0),
            'segment': validates_data_used_file(kwargs, ['energy_detail', 'segment'], 0),
            'business': validates_data_used_file(kwargs, ['energy_detail', 'business'], 0),

            'cost_center': validates_data_used_file(kwargs, ['cost_center'], 0) ,

            'profit_center': validates_data_used_file(kwargs, ['profit_center'], 0) ,
            'composition_loss': validates_data_used_file(kwargs, ['composition_loss'], type_format_number), #number

            'company_name_apport': validates_data_used_file(kwargs, ['apport_energy_composition', 'company_name'], 0),
            'volume_code': validates_data_used_file(kwargs, ['apport_energy_composition', 'volume_code'], 0),
            'cost_code': validates_data_used_file(kwargs, ['apport_energy_composition', 'cost_code'], 0),
            'status_apport': translate_language("field_status_"+( validates_data_used_file(kwargs, ['apport_energy_composition', 'status'], 0) ), request),

            'display_name': validates_data_used_file(kwargs, ['point_energy_composition', 'display_name'], 0),
            'gauge_point_destination': validates_data_used_file(kwargs, ['gauge_point_destination', 'display_name'], 0),
            'id_production_phase': validates_data_used_file(kwargs, ['id_production_phase', 'description'], 0),
            'data_source': validates_data_used_file(kwargs, ['data_source'], 0),
        }
        rest_data.append(new)
    
    try:
        if format_file == 'csv':
            return generic_csv(mapping, header, rest_data, translate_language("label_energyComposition_download", request) )
        elif format_file == 'xlsx':
            styles=[
                {
                    'fields': [
                        "composition_loss"
                    ], 
                    'number_format': '#,##0.00\\%'
                }
            ]
            return generic_xls(mapping, header, rest_data, translate_language("label_energyComposition_download", request), styles)
        elif format_file == 'pdf':
            return generic_pdf(mapping, header, rest_data, translate_language("label_energyComposition_download", request) )
        else:
            return Response({'error': translate_language_error('error_unknown_format_file', request) }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as ex:  # pragma: no cover
        # just to protect endpoint
        return Response({'error': translate_language_error('error_undefined', request) }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@check_module(modules.energy_composition, [permissions.VIEW, permissions.EDITN1])
def session_log_basic_energy_composition(request, pk, format=None):
    """
        List all logs about energy composition
    """

    kwargs = {'core': EnergyComposition, 'core_pk': 'id_energy_composition', 'core+': [],
              'child': [ApportiomentComposition,PointComposition]}
    kwargsAux = generic_log_search_basic(generic_log_search(pk, **kwargs))
    
    #format fomule
    for energy in kwargsAux:
        if energy['ENERGY_COMPOSITION']:
            if energy['ENERGY_COMPOSITION']['old_value']:
                energy['ENERGY_COMPOSITION']['old_value']['kpi_formulae']=formattedFomuleKpi(energy['ENERGY_COMPOSITION']['old_value']['kpi_formulae'], [])
            if 'value' in energy['ENERGY_COMPOSITION']['new_value']['kpi_formulae']:
                energy['ENERGY_COMPOSITION']['new_value']['kpi_formulae']['value']=formattedFomuleKpi(energy['ENERGY_COMPOSITION']['new_value']['kpi_formulae']['value'], [])
            else:
                energy['ENERGY_COMPOSITION']['new_value']['kpi_formulae']=formattedFomuleKpi(energy['ENERGY_COMPOSITION']['new_value']['kpi_formulae'], [])

    log={'logs':kwargsAux}

    id_array=[]

    #company
    company_Array=[]
    for items in kwargsAux:
        if items['ENERGY_COMPOSITION']['new_value']['id_company']:
            a=items['ENERGY_COMPOSITION']['new_value']['id_company']
            if 'value' in a:
                id_num=a['value']
            else:
                id_num=a
            if id_num not in id_array:
                id_array.append(id_num)
                company_Array.append({'id_company':id_num,'company_name':Company.objects.get(pk=id_num).company_name})
        
        if type(items['APPORTIOMENT_COMPOSITION'])==list:
            for item in items['APPORTIOMENT_COMPOSITION']:
                if item['new_value']['id_company']:
                    a=item['new_value']['id_company']
                    if 'value' in a:
                        id_num=a['value']
                    else:
                        id_num=a
                    if id_num not in id_array:
                        id_array.append(id_num)
                        company_Array.append({'id_company':id_num,'company_name':Company.objects.get(pk=id_num).company_name})
        else:
            if items['APPORTIOMENT_COMPOSITION']:
                if items['APPORTIOMENT_COMPOSITION']['new_value']['id_company']:
                    a=items['APPORTIOMENT_COMPOSITION']['new_value']['id_company']
                    if 'value' in a:
                        id_num=a['value']
                    else:
                        id_num=a
                    if id_num not in id_array:
                        id_array.append(id_num)
                        company_Array.append({'id_company':id_num,'company_name':Company.objects.get(pk=id_num).company_name})

    #Segment
    segment_array=[]
    id_array.clear()
    for items in kwargsAux:
        if items['ENERGY_COMPOSITION']['new_value']['id_segment']:
            a=items['ENERGY_COMPOSITION']['new_value']['id_segment']
            if 'value' in a:
                id_num=a['value']
            else:
                id_num=a
            if id_num not in id_array:
                id_array.append(id_num)
                segment_array.append({'id_segment':id_num,'description':Segment.objects.get(pk=id_num).description})

    #Business
    business_array=[]
    id_array.clear()
    for items in kwargsAux:
        if items['ENERGY_COMPOSITION']['new_value']['id_business']:
            a=items['ENERGY_COMPOSITION']['new_value']['id_business']
            if 'value' in a:
                id_num=a['value']
            else:
                id_num=a
            if id_num not in id_array:
                id_array.append(id_num)
                business_array.append({'id_business':id_num,'description':Business.objects.get(pk=id_num).description})

    #DirectorBoard
    director_array=[]
    id_array.clear()
    for items in kwargsAux:
        if items['ENERGY_COMPOSITION']['new_value']['id_director']:
            a=items['ENERGY_COMPOSITION']['new_value']['id_director']
            if 'value' in a:
                id_num=a['value']
            else:
                id_num=a
            if id_num not in id_array:
                id_array.append(id_num)
                director_array.append({'id_director':id_num,'description':DirectorBoard.objects.get(pk=id_num).description})
                
    #AccountantArea
    accountant_array=[]
    id_array.clear()
    for items in kwargsAux:
        if items['ENERGY_COMPOSITION']['new_value']['id_accountant']:
            a=items['ENERGY_COMPOSITION']['new_value']['id_accountant']
            if 'value' in a:
                id_num=a['value']
            else:
                id_num=a
            if id_num not in id_array:
                id_array.append(id_num)
                accountant_array.append({'id_accountant':id_num,'description':AccountantArea.objects.get(pk=id_num).description})

    #ProductionPhase
    production_phase_array=[]
    id_array.clear()
    for items in kwargsAux:
        if items['ENERGY_COMPOSITION']['new_value'].get('id_production_phase', None):
            a=items['ENERGY_COMPOSITION']['new_value']['id_production_phase']
            if 'value' in a:
                id_num=a['value']
            else:
                id_num=a
            if id_num not in id_array:
                id_array.append(id_num)
                production_phase_array.append({'id_production_phase':id_num,'description':ProductionPhase.objects.get(pk=id_num).description})
                
    #POINT_COMPOSITION
    point_array=[]
    id_array.clear()
    for items in kwargsAux:
        if type(items['POINT_COMPOSITION'])==list:
            for item in items['POINT_COMPOSITION']:
                if item['new_value']['id_gauge']:
                    a=item['new_value']['id_gauge']
                    if 'value' in a:
                        id_num=a['value']
                    else:
                        id_num=a
                    if id_num not in id_array:
                        id_array.append(id_num)
                        point_array.append( {'id_point':id_num, 'display_name': (GaugePoint.objects.get(pk=id_num).id_source).display_name} )
        else:
            if items['POINT_COMPOSITION']:
                if items['POINT_COMPOSITION']['new_value']['id_gauge']:
                    a=items['POINT_COMPOSITION']['new_value']['id_gauge']
                    if 'value' in a:
                        id_num=a['value']
                    else:
                        id_num=a
                    if id_num not in id_array:
                        id_array.append(id_num)
                        point_array.append( {'id_point':id_num, 'display_name': (GaugePoint.objects.get(pk=id_num).id_source).display_name} )

    #Gauge_point_destination
    gauge_array=[]
    id_array.clear()
    for items in kwargsAux:
        if items['ENERGY_COMPOSITION']['new_value'].get('id_gauge_point_destination'):
            a=items['ENERGY_COMPOSITION']['new_value']['id_gauge_point_destination']
            if 'value' in a:
                id_num=a['value']
            else:
                id_num=a
        if id_num not in id_array:
                id_array.append(id_num)
    for obj_gauge in GaugePoint.objects.filter(pk__in=id_array).select_related('id_source'):
        gauge_array.append({'id_gauge':obj_gauge.pk, 'display_name':obj_gauge.id_source.display_name })



    log['statics_relateds']={'Company':company_Array, 'Segment':segment_array, 'Business':business_array, \
            'DirectorBoard':director_array, 'AccountantArea':accountant_array, 'ProductionPhase': production_phase_array , 'Point_Composition':point_array, \
            'Gauge_point_destination':gauge_array }
    return Response( log )

def formattedFomuleKpi(formule, gauges):
    #formule: pass the formula as a parameter
    #gauges: lisList of gauge_point related to a formulat 
    try:
        fomule_original=formule

        formatted_Formule=""
        string_Position=0
        validates_is_object=0 #1=True, 0=False
        
        ###({'id':'86','key':'A'}+{'id':'66','key':'B'})*{'id':'64','key':'C'} Example of the fomula that is passed
        for item in fomule_original:
            if item=="{":#check if it is the beginning of the object
                counter_Id=string_Position+7#advance to the beginning of the value I need
                idGauge=""#save the id that was passed in the formula
                while(True): #It continues to run until the numeric id value runs out
                    if fomule_original[counter_Id] == "'": break
                    idGauge= idGauge+(fomule_original[counter_Id])
                    counter_Id+=1
                
                valueDisplay=""
                for item in gauges:
                    if item.id_gauge==int(idGauge):
                        valueDisplay=item.id_source.display_name
                if not valueDisplay:
                    valueDisplay=GaugePoint.objects.get(pk=int(idGauge)).id_source.display_name#retrieve gauge_point for id retrieved above
                
                formatted_Formule=formatted_Formule+valueDisplay+" " #enter display_name of recovered gauge point
                validates_is_object=1

            if validates_is_object==0:#check if value is not inside object
                formatted_Formule=formatted_Formule+item+" "

            if item=="}": #validates if it has reached the end of the object
                validates_is_object=0

            string_Position+=1
    except:
        formatted_Formule=formule

    return formatted_Formule
    
def function_find_generic(request):
    kwargs = {
        'composition_name': 'composition_name__contains', 
        'cost_center': 'cost_center__contains',
        'company_name': 'id_company__company_name__contains',
        'business': 'id_business__description__contains',
        'director':'id_director__description__contains',
        'segment':'id_segment__description__contains',
        'accountantarea':'id_accountant__description__contains',
        'status':'status__contains',
        'production_phase': 'id_production_phase__description__contains',
        'data_source': 'data_source',
    }

    kwargs_order = {
        'composition_name': 'composition_name', 
        'cost_center': 'cost_center',
        'company_name': 'id_company__company_name',
        'business':'id_business__description',
        'director':'id_director__description',
        'segment':'id_segment__description',
        'accountantarea': 'id_accountant__description',
        'status':'status',
        'production_phase': 'id_production_phase__description',
        'data_source': 'data_source',

        '-composition_name':'-composition_name',
        '-cost_center': '-cost_center',
        '-company_name': '-id_company__company_name',
        '-business':'-id_business__description',
        '-director':'-id_director__description',
        '-segment':'-id_segment__description',
        '-accountantarea': '-id_accountant__description',
        '-status':'-status',
        '-production_phase': 'id_production_phase__description',
        '-data_source': 'data_source',
    }

    ids = generic_queryset_filter(request, EnergyComposition, 'id_energy_composition', **kwargs)
    if request.query_params.get('ordering') in kwargs_order:
        order_by = kwargs_order[request.query_params.get('ordering')]
    else:
        order_by = kwargs_order['composition_name']

    energy_composition = EnergyComposition.objects.filter(id_energy_composition__in=ids).order_by(order_by)\
            .select_related('id_company').select_related('id_accountant')\
            .select_related('id_director') .select_related('id_segment')\
            .select_related('id_gauge_point_destination').select_related('id_gauge_point_destination__id_source')\
            .select_related('id_business').prefetch_related('point_energy_composition__id_gauge__id_source')\
            .prefetch_related('apport_energy_composition__id_company')
            
    return energy_composition

def function_format_result_for_find(request, data):
    observation_log = ""
    if 'observation_log' in request.data:
        observation_log = request.data['observation_log']

    serializer_context = {
        'request': request,
        'observation_log': observation_log
    }
    serializer=[]
    try:
        for item in data:
            item_json=EnergyCompositionSerializerViewBasic(item, many=False, context=serializer_context).data
            energy_detail= {
                "id_company": item.id_company_id,
                "company_name": item.id_company.company_name if item.id_company else "",
                "id_accountant": item.id_accountant_id if item.id_accountant else "",
                "accountantarea": item.id_accountant.description if item.id_accountant else "",
                "id_director": item.id_director_id if item.id_director else "",
                "director": item.id_director.description if item.id_director else "",
                "id_segment": item.id_segment_id if item.id_segment else "",
                "segment": item.id_segment.description if item.id_segment else "",
                "id_business": item.id_business_id if item.id_business else "",
                "business": item.id_business.description if item.id_business else ""
            }
            item_json['energy_detail']=energy_detail
            
            if hasattr(item, 'apport_energy_composition'):
                item_json['apport_energy_composition']=[]
                for item_apport in item._prefetched_objects_cache['apport_energy_composition']:
                    apport_json=ApportiomentCompositionSerializerViewBasic(item_apport, many=False, context=serializer_context).data  
                    if item_apport.id_company:
                        apport_json['company_name']=item_apport.id_company.company_name
                    else:
                        apport_json['company_name']=""
                    item_json['apport_energy_composition'].append(apport_json)
            
            if hasattr(item, 'point_energy_composition'):
                item_json['point_energy_composition']=[]
                for item_pointComp in item._prefetched_objects_cache['point_energy_composition']:
                    point_composition=PointCompositionSerializerViewBasic(item_pointComp, many=False, context=serializer_context).data
                    if item_pointComp.id_gauge:
                        point_composition['display_name']=item_pointComp.id_gauge.id_source.display_name
                    else:
                        point_composition['display_name']=""
                    item_json['point_energy_composition'].append(point_composition)
           
            item_json['gauge_point_destination']={}
            if item.id_gauge_point_destination:
                item_json['gauge_point_destination']=GaugePointSerializerFindBasic(item.id_gauge_point_destination, many=False, context=serializer_context).data  
                item_json['gauge_point_destination']['source_details']=SourcePmeSerializer(item.id_gauge_point_destination.id_source, many=False, context=serializer_context).data
                item_json['gauge_point_destination']['display_name']=item.id_gauge_point_destination.id_source.display_name
            
            serializer.append(item_json)
    except:
        serializer = EnergyCompositionSerializer(data, many=True, context=serializer_context).data
    return serializer