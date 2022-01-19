import collections
import json

from django.core.serializers.json import DjangoJSONEncoder
from django.forms import model_to_dict
from rest_framework import status, serializers
from rest_framework.decorators import api_view
from rest_framework.response import Response

from asset_items.models import AssetItems, SeasonalityAssetItemCost, SeasonalityAssetItem, \
    SeazonalityAssetItemDepreciation
from asset_items.serializers import AssetItemsSerializer, CompanySerializer, EnergyCompositionSerializer, \
    SeasonalityAssetItemSerializer, SazonalityAssetItemCostSerializer, \
    SeasonalitySerializerAssetItems, SeazonalityAssetItemDepreciationSerializer, \
    AssetItemsSerializerFindBasic, CompanySerializerFindBasic, EnergyCompositionSerializerFindBasic, AssetsSerializerFindBasic, CCEEDescriptionSerializerFindBasic
from assets.models import Assets
from company.models import Company
from core.attachment_utility import generic_pdf, generic_csv, generic_data_csv_list, generic_xls
from core.models import Seasonality, CceeDescription
from core.views import generic_log_search, generic_move_itens_log, alter_number, \
        generic_queryset_filter, generic_paginator, generic_detail_log, generic_log_search_basic, validates_data_used_file
from energy_composition.models import EnergyComposition
from profiles.models import Profile
from itertools import chain
from locales.translates_function import translate_language_header, translate_language, translate_language_error
from SmartEnergy.auth import check_module
import SmartEnergy.auth.permissions as permissions
import SmartEnergy.auth.modules as modules

@api_view(['GET'])
@check_module(modules.asset_item, [permissions.VIEW, permissions.EDITN1])
def show_company(request, format=None):
    companies = (Company.objects.filter(type__in=['R', 'F'], assetitems_company__isnull= True, status='S') | \
                 Company.objects.filter(pk= request.query_params.get('id_company') if request.query_params.get('id_company') else 0 ) ) \
        .order_by('company_name')\
        .values('id_company', 'company_name', 'type', 'characteristics')
    if companies:
        companies = list(
            map(
                lambda x:
                {
                'id_company': x['id_company'],
                'company_name': x['company_name'],
                'type': x['type'],
                'characteristics': x['characteristics']
                },
                companies
            )
        )
    else:
        companies={"Error": "Without company"}
    return Response(companies)

@api_view(['GET'])
@check_module(modules.asset_item, [permissions.VIEW, permissions.EDITN1])
def show_assets_basic(request, format=None):
    observation_log = ""
    if 'observation_log' in request.data:
        observation_log = request.data['observation_log']

    serializer_context = {
        'request': request,
        'observation_log': observation_log
    }
    kwargs = {'company_name': 'id_company__company_name__contains',
        'code_ccee': 'id_ccee_siga__code_ccee__contains',
        'status': 'status__contains'}

    ids = generic_queryset_filter(request, Assets, 'id_assets', **kwargs)
    assets = Assets.objects \
        .select_related('id_company').select_related('id_ccee_siga')\
        .filter(id_assets__in=ids, status='S').order_by('id_company__company_name')
    try:
        serializer=[]
        for item in assets:
            itemJson=AssetsSerializerFindBasic(item, many=False, context=serializer_context).data
            id_ccee_siga=CCEEDescriptionSerializerFindBasic(item.id_ccee_siga, many=False, context=serializer_context).data
            id_company=CompanySerializerFindBasic(item.id_company, many=False, context=serializer_context).data

            itemJson['id_ccee_siga']=id_ccee_siga
            itemJson['id_company']=id_company
            serializer.append(itemJson)
    except :
        serializer = AssetsSerializerShowView(assets, many=True, context=serializer_context).data

    return Response(serializer)


@api_view(['GET'])
@check_module(modules.asset_item, [permissions.VIEW, permissions.EDITN1])
def show_energyComposition(request, pk, format=None):
    observation_log = ""
    if 'observation_log' in request.data:
        observation_log = request.data['observation_log']

    serializer_context = {
        'request': request,
        'observation_log': observation_log
    }

    try:
        energyComposition = EnergyComposition.objects.filter(id_company=pk, status="S").order_by('composition_name')
        serializer = EnergyCompositionSerializer(energyComposition, many=True, context=serializer_context)
        return Response(serializer.data)

    except EnergyComposition.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)


def get_data_asset_items(pk):  # Get Detailed Return
    """
        List data about asset items
    """
    try:
        asset_item = AssetItems.objects.get(pk=pk)
        kwargs = json.loads(json.dumps(
            model_to_dict(asset_item), cls=DjangoJSONEncoder))
    except AssetItems.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
        # energycomposition
    try:
        energycomposition = EnergyComposition.objects.get(pk=asset_item.id_energy_composition_id)
        kwargs['energy_composition'] = json.loads(json.dumps(
            model_to_dict(energycomposition), cls=DjangoJSONEncoder))
    except EnergyComposition.DoesNotExist:
        kwargs['energy_composition'] = {}
        # company
    try:
        company = Company.objects.get(pk=asset_item.id_company_id)
        kwargs['company'] = json.loads(json.dumps(
            model_to_dict(company), cls=DjangoJSONEncoder))

    except Company.DoesNotExist:
        kwargs['company'] = {}
        # assets
    try:
        asset = Assets.objects.get(pk=asset_item.id_assets_id)
        kwargs['assets'] = json.loads(json.dumps(
            model_to_dict(asset), cls=DjangoJSONEncoder))
    except Assets.DoesNotExist:
        kwargs['assets'] = {}

    try:
        cceedescription = CceeDescription.objects.get(pk=asset_item.id_assets.id_ccee_siga_id)
        kwargs['assets']['cceedescription'] = json.loads(json.dumps(
            model_to_dict(cceedescription), cls=DjangoJSONEncoder))
    except Assets.DoesNotExist:
        kwargs['assets']['cceedescription'] = {}

    try:
        company = Company.objects.values('id_company', 'company_name').get(pk=asset_item.id_assets.id_company_id)
        kwargs['assets']['company'] = company

    except Assets.DoesNotExist:
        kwargs['assets']['company'] = {}

    array_SeasonalityAssetItem = []
    for seasonality_assetitem in SeasonalityAssetItem.objects.filter(id_asset_items=asset_item.id_asset_items):
        SeasonalityAssetItemJson = json.loads(json.dumps(
            model_to_dict(seasonality_assetitem), cls=DjangoJSONEncoder))
        seasonality = Seasonality.objects.get(
            pk=int(seasonality_assetitem.id_seasonality_id))
        seasonalityJson = json.loads(json.dumps(
            model_to_dict(seasonality), cls=DjangoJSONEncoder))
        SeasonalityAssetItemJson['Seasonality'] = seasonalityJson

        array_SeasonalityAssetItem.append(SeasonalityAssetItemJson)
    kwargs['Seasonality_asset_item'] = array_SeasonalityAssetItem

    array_SeasonalityAssetItemCost = []
    for seasonality_itemCost in SeasonalityAssetItemCost.objects.filter(id_asset_items=asset_item.id_asset_items):
        SeasonalityAssetItemCostJson = json.loads(json.dumps(
            model_to_dict(seasonality_itemCost), cls=DjangoJSONEncoder))
        seasonality = Seasonality.objects.get(
            pk=int(seasonality_itemCost.id_seazonality_asset_id))
        seasonalityJson = json.loads(json.dumps(
            model_to_dict(seasonality), cls=DjangoJSONEncoder))
        SeasonalityAssetItemCostJson['Seasonality'] = seasonalityJson

        array_SeasonalityAssetItemCost.append(SeasonalityAssetItemCostJson)
    kwargs['Seasonality_asset_item_cost'] = array_SeasonalityAssetItemCost

    array_SeazonalityAssetItemDepreciation = []
    for seasonality_assetItemDepreciation in SeazonalityAssetItemDepreciation.objects.filter(
            id_asset_items=asset_item.id_asset_items):
        SeazonalityAssetItemDepreciationJson = json.loads(json.dumps(
            model_to_dict(seasonality_assetItemDepreciation), cls=DjangoJSONEncoder))
        seasonality = Seasonality.objects.get(
            pk=int(seasonality_assetItemDepreciation.id_seasonality_id))
        seasonalityJson = json.loads(json.dumps(
            model_to_dict(seasonality), cls=DjangoJSONEncoder))
        SeazonalityAssetItemDepreciationJson['Seasonality'] = seasonalityJson

        array_SeazonalityAssetItemDepreciation.append(SeazonalityAssetItemDepreciationJson)
    kwargs['Seazonality_asset_depreciation'] = array_SeazonalityAssetItemDepreciation

    return kwargs

@api_view(['GET'])
@check_module(modules.asset_item, [permissions.VIEW, permissions.EDITN1])
def session_asset_items_get(request, format=None):
    """
        List all companies 
    """
    observation_log = ""
    if 'observation_log' in request.data:
        observation_log = request.data['observation_log']

    serializer_context = {
        'request': request,
        'observation_log': observation_log
    }
    if request.method == 'GET':
        kwargs = {'company_name': 'id_company__company_name__contains',
                  'cost_center': 'id_energy_composition__cost_center__contains',
                  'name_ccee': 'id_assets__id_ccee_siga__name_ccee__contains',
                  'composition_name': 'id_energy_composition__composition_name__contains', 
                  'company_name_assets': 'id_assets__id_company__company_name__contains',
                  'status': 'status__contains' }
        kwargs_order = {'company_name': 'id_company__company_name',
                        'cost_center': 'id_energy_composition__cost_center',
                        'name_ccee': 'id_assets__id_ccee_siga__name_ccee',
                        'composition_name': 'id_energy_composition__composition_name',
                        'company_name_assets': 'id_assets__id_company__company_name',
                        'status': 'status',

                        '-company_name': '-id_company__company_name',
                        '-cost_center': '-id_energy_composition__cost_center',
                        '-name_ccee': '-id_assets__id_ccee_siga__name_ccee',
                        '-composition_name': '-id_energy_composition__composition_name',
                        '-company_name_assets': '-id_assets__id_company__company_name',
                        '-status': '-status'
                        }
        ids = generic_queryset_filter(request, AssetItems, 'id_asset_items', **kwargs)
        if request.query_params.get('ordering') in kwargs_order:
            order_by = kwargs_order[request.query_params.get('ordering')]
        else:
            order_by = kwargs_order['company_name']
        asset_item = AssetItems.objects.filter(id_asset_items__in=ids).order_by(order_by)
        data, page_count, page_next, page_previous = generic_paginator(request, asset_item)
        serializer = AssetItemsSerializer(data, many=True, context=serializer_context)
        response = collections.OrderedDict([
            ('count', page_count),
            ('next', page_next),
            ('previous', page_previous),
            ('results', serializer.data)
        ])
        return Response(response)


@api_view(['POST'])
@check_module(modules.asset_item, [permissions.EDITN1])
def session_asset_items_post(request, format=None):
    """
        create a asset items
    """
    observation_log = ""
    if 'observation_log' in request.data:
        observation_log = request.data['observation_log']

    serializer_context = {
        'request': request,
        'observation_log': observation_log
    }

    if request.method == 'POST':
        serializer = AssetItemsSerializer(data=request.data, context=serializer_context)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT'])
@check_module(modules.asset_item, [permissions.EDITN1])
def session_asset_items_put(request, pk, format=None):
    """
        Retrieve, update or delete a specific asset items.
    """
    observation_log = ""
    if 'observation_log' in request.data:
        observation_log = request.data['observation_log']

    serializer_context = {
        'request': request,
        'observation_log': observation_log
    }
 
    try:
        asset_item = AssetItems.objects.get(pk=pk)
    except AssetItems.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'PUT':
        serializer = AssetItemsSerializer(asset_item, data=request.data, context=serializer_context)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@check_module(modules.asset_item, [permissions.VIEW, permissions.EDITN1])
def session_asset_items_get_detail(request, pk, format=None):
    """
        specific asset items.
    """
    observation_log = ""
    if 'observation_log' in request.data:
        observation_log = request.data['observation_log']

    serializer_context = {
        'request': request,
        'observation_log': observation_log
    }
 
    try:
        asset_item = AssetItems.objects.get(pk=pk)
    except AssetItems.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)


    if request.method == 'GET':
        serializer = collections.OrderedDict(get_data_asset_items(pk))
        return Response(serializer)

@api_view(['GET'])
@check_module(modules.asset_item, [permissions.VIEW, permissions.EDITN1])
def session_asset_items_file(request):
    if not (request.query_params.get('format_file', None) is None):
        format_file = request.query_params.get('format_file', None)
    else:
        return Response({'error': translate_language_error('error_format_file_csv_or_pdf', request)}, status=status.HTTP_400_BAD_REQUEST)

    asset_item = function_generic_find(request)
    serializer = function_generic_format_return_find(request, asset_item)
    
    payload = json.dumps(serializer, indent=9, default=str).encode('utf-8')
    rest = json.loads(payload)
    
    header = {
        'company_name': 'field_company_name',
        'characteristics': 'field_characteristics',
        'composition_name': 'field_composition_name',
        'cost_center': 'field_cost_center',
        'Associated_Asset':'field_id_assets',
        'status':'Status',

        'year_asset_item': 'field_year_seasonality_generation',
        "measure_unity_asset_item": 'field_measureUnity',
        "january_asset_item": 'field_january_seasonality_generation',
        "february_asset_item": 'field_february_seasonality_generation',
        "march_asset_item": 'field_march_seasonality_generation',
        "april_asset_item": 'field_april_seasonality_generation',
        "may_asset_item": 'field_may_seasonality_generation',
        "june_asset_item": 'field_june_seasonality_generation',
        "july_asset_item": 'field_july_seasonality_generation',
        "august_asset_item": 'field_august_seasonality_generation',
        "september_asset_item": 'field_september_seasonality_generation',
        "october_asset_item": 'field_october_seasonality_generation',
        "november_asset_item": 'field_november_seasonality_generation',
        "december_asset_item": 'field_december_seasonality_generation',

        'year_asset_item_cost': 'field_year_seasonality_generation_cost',
        "measure_unity_asset_item_cost": 'field_measureUnity',
        "january_asset_item_cost": 'field_january_seasonality_generation_cost',
        "february_asset_item_cost": 'field_february_seasonality_generation_cost',
        "march_asset_item_cost": 'field_march_seasonality_generation_cost',
        "april_asset_item_cost": 'field_april_seasonality_generation_cost',
        "may_asset_item_cost": 'field_may_seasonality_generation_cost',
        "june_asset_item_cost": 'field_june_seasonality_generation_cost',
        "july_asset_item_cost": 'field_july_seasonality_generation_cost',
        "august_asset_item_cost": 'field_august_seasonality_generation_cost',
        "september_asset_item_cost": 'field_september_seasonality_generation_cost',
        "october_asset_item_cost": 'field_october_seasonality_generation_cost',
        "november_asset_item_cost": 'field_november_seasonality_generation_cost',
        "december_asset_item_cost": 'field_december_seasonality_generation_cost',

        'year_asset_depreciation': 'field_year_seasonality_depreciation',
        "measure_unity_asset_depreciation": 'field_measureUnity',
        "january_asset_depreciation": 'field_january_seasonality_depreciation',
        "february_asset_depreciation": 'field_february_seasonality_depreciation',
        "march_asset_depreciation": 'field_march_seasonality_depreciation',
        "april_asset_depreciation": 'field_april_seasonality_depreciation',
        "may_asset_depreciation": 'field_may_seasonality_depreciation',
        "june_asset_depreciation": 'field_june_seasonality_depreciation',
        "july_asset_depreciation": 'field_july_seasonality_depreciation',
        "august_asset_depreciation": 'field_august_seasonality_depreciation',
        "september_asset_depreciation": 'field_september_seasonality_depreciation',
        "october_asset_depreciation": 'field_october_seasonality_depreciation',
        "november_asset_depreciation": 'field_november_seasonality_depreciation',
        "december_asset_depreciation": 'field_december_seasonality_depreciation',
    }
    header=translate_language_header(header, request)
    mapping = [
        'company_name',
        'characteristics',
        'composition_name',
        'cost_center',
        'Associated_Asset',
        'status',

        'year_asset_item',
        "measure_unity_asset_item",
        "january_asset_item",
        "february_asset_item",
        "march_asset_item",
        "april_asset_item",
        "may_asset_item",
        "june_asset_item",
        "july_asset_item",
        "august_asset_item",
        "september_asset_item",
        "october_asset_item",
        "november_asset_item",
        "december_asset_item",

        'year_asset_item_cost',
        "measure_unity_asset_item_cost",
        "january_asset_item_cost",
        "february_asset_item_cost",
        "march_asset_item_cost",
        "april_asset_item_cost",
        "may_asset_item_cost",
        "june_asset_item_cost",
        "july_asset_item_cost",
        "august_asset_item_cost",
        "september_asset_item_cost",
        "october_asset_item_cost",
        "november_asset_item_cost",
        "december_asset_item_cost",

        'year_asset_depreciation',
        "measure_unity_asset_depreciation",
        "january_asset_depreciation",
        "february_asset_depreciation",
        "march_asset_depreciation",
        "april_asset_depreciation",
        "may_asset_depreciation",
        "june_asset_depreciation",
        "july_asset_depreciation",
        "august_asset_depreciation",
        "september_asset_depreciation",
        "october_asset_depreciation",
        "november_asset_depreciation",
        "december_asset_depreciation"
    ]

    rest = generic_data_csv_list(rest, ['Seasonality_asset_item', 'Seasonality_asset_item_cost',
                                            'Seazonality_asset_depreciation'])
    rest_data = []

    type_format_number=0 if format_file=='pdf' else 1
    for index in range(len(rest)):
        kwargs = rest[index]
        new = {
            'company_name': validates_data_used_file(kwargs, ['company_detail', 'company_name'], 0),
            'characteristics': translate_language(validates_data_used_file(kwargs, ['company_detail', 'characteristics'], 0), request),
            'composition_name': validates_data_used_file(kwargs, ['energycomposition_detail', 'composition_name'], 0),
            
            'cost_center': validates_data_used_file(kwargs, ['energycomposition_detail', 'cost_center'], 0),
            'Associated_Asset': validates_data_used_file(kwargs, ['assets_detail', 'company', 'company_name'], 0),
            
            #Seasonality_asset_item
            'year_asset_item': validates_data_used_file(kwargs, ['Seasonality_asset_item', 'id_seasonality_detail.year'], type_format_number),
            'measure_unity_asset_item': validates_data_used_file(kwargs, ['Seasonality_asset_item', 'id_seasonality_detail.measure_unity'], 0),
            'january_asset_item': validates_data_used_file(kwargs, ['Seasonality_asset_item', 'id_seasonality_detail.january'], type_format_number),
            'february_asset_item': validates_data_used_file(kwargs, ['Seasonality_asset_item', 'id_seasonality_detail.february'], type_format_number),
            'march_asset_item': validates_data_used_file(kwargs, ['Seasonality_asset_item', 'id_seasonality_detail.march'], type_format_number),
            'april_asset_item': validates_data_used_file(kwargs, ['Seasonality_asset_item', 'id_seasonality_detail.april'], type_format_number),
            'may_asset_item': validates_data_used_file(kwargs, ['Seasonality_asset_item', 'id_seasonality_detail.may'], type_format_number),
            'june_asset_item': validates_data_used_file(kwargs, ['Seasonality_asset_item', 'id_seasonality_detail.june'], type_format_number),
            'july_asset_item': validates_data_used_file(kwargs, ['Seasonality_asset_item', 'id_seasonality_detail.july'], type_format_number),
            'august_asset_item': validates_data_used_file(kwargs, ['Seasonality_asset_item', 'id_seasonality_detail.august'], type_format_number),
            'september_asset_item': validates_data_used_file(kwargs, ['Seasonality_asset_item', 'id_seasonality_detail.september'], type_format_number),
            'october_asset_item': validates_data_used_file(kwargs, ['Seasonality_asset_item', 'id_seasonality_detail.october'], type_format_number),
            'november_asset_item': validates_data_used_file(kwargs, ['Seasonality_asset_item', 'id_seasonality_detail.november'], type_format_number),
            'december_asset_item': validates_data_used_file(kwargs, ['Seasonality_asset_item', 'id_seasonality_detail.december'], type_format_number),

            #Seasonality_asset_item_cost
            'year_asset_item_cost': validates_data_used_file(kwargs, ['Seasonality_asset_item_cost', 'id_seasonality_detail.year'], type_format_number),
            'measure_unity_asset_item_cost': validates_data_used_file(kwargs, ['Seasonality_asset_item_cost', 'id_seasonality_detail.measure_unity'], 0),
            'january_asset_item_cost': validates_data_used_file(kwargs, ['Seasonality_asset_item_cost', 'id_seasonality_detail.january'], type_format_number),
            'february_asset_item_cost': validates_data_used_file(kwargs, ['Seasonality_asset_item_cost', 'id_seasonality_detail.february'], type_format_number),
            'march_asset_item_cost': validates_data_used_file(kwargs, ['Seasonality_asset_item_cost', 'id_seasonality_detail.march'], type_format_number),
            'april_asset_item_cost': validates_data_used_file(kwargs, ['Seasonality_asset_item_cost', 'id_seasonality_detail.april'], type_format_number),
            'may_asset_item_cost': validates_data_used_file(kwargs, ['Seasonality_asset_item_cost', 'id_seasonality_detail.may'], type_format_number),
            'june_asset_item_cost': validates_data_used_file(kwargs, ['Seasonality_asset_item_cost', 'id_seasonality_detail.june'], type_format_number),
            'july_asset_item_cost': validates_data_used_file(kwargs, ['Seasonality_asset_item_cost', 'id_seasonality_detail.july'], type_format_number),
            'august_asset_item_cost': validates_data_used_file(kwargs, ['Seasonality_asset_item_cost', 'id_seasonality_detail.august'], type_format_number),
            'september_asset_item_cost': validates_data_used_file(kwargs, ['Seasonality_asset_item_cost', 'id_seasonality_detail.september'], type_format_number),
            'october_asset_item_cost': validates_data_used_file(kwargs, ['Seasonality_asset_item_cost', 'id_seasonality_detail.october'], type_format_number),
            'november_asset_item_cost': validates_data_used_file(kwargs, ['Seasonality_asset_item_cost', 'id_seasonality_detail.november'], type_format_number),
            'december_asset_item_cost': validates_data_used_file(kwargs, ['Seasonality_asset_item_cost', 'id_seasonality_detail.december'], type_format_number),

            #Seazonality_asset_depreciation
            'year_asset_depreciation': validates_data_used_file(kwargs, ['Seazonality_asset_depreciation', 'id_seasonality_detail.year'], type_format_number),
            'measure_unity_asset_depreciation': validates_data_used_file(kwargs, ['Seazonality_asset_depreciation', 'id_seasonality_detail.measure_unity'], 0),
            'january_asset_depreciation': validates_data_used_file(kwargs, ['Seazonality_asset_depreciation', 'id_seasonality_detail.january'], type_format_number),
            'february_asset_depreciation': validates_data_used_file(kwargs, ['Seazonality_asset_depreciation', 'id_seasonality_detail.february'], type_format_number),
            'march_asset_depreciation': validates_data_used_file(kwargs, ['Seazonality_asset_depreciation', 'id_seasonality_detail.march'], type_format_number),
            'april_asset_depreciation': validates_data_used_file(kwargs, ['Seazonality_asset_depreciation', 'id_seasonality_detail.april'], type_format_number),
            'may_asset_depreciation': validates_data_used_file(kwargs, ['Seazonality_asset_depreciation', 'id_seasonality_detail.may'], type_format_number),
            'june_asset_depreciation': validates_data_used_file(kwargs, ['Seazonality_asset_depreciation', 'id_seasonality_detail.june'], type_format_number),
            'july_asset_depreciation': validates_data_used_file(kwargs, ['Seazonality_asset_depreciation', 'id_seasonality_detail.july'], type_format_number),
            'august_asset_depreciation': validates_data_used_file(kwargs, ['Seazonality_asset_depreciation', 'id_seasonality_detail.august'], type_format_number),
            'september_asset_depreciation': validates_data_used_file(kwargs, ['Seazonality_asset_depreciation', 'id_seasonality_detail.september'], type_format_number),
            'october_asset_depreciation': validates_data_used_file(kwargs, ['Seazonality_asset_depreciation', 'id_seasonality_detail.october'], type_format_number),
            'november_asset_depreciation': validates_data_used_file(kwargs, ['Seazonality_asset_depreciation', 'id_seasonality_detail.november'], type_format_number),
            'december_asset_depreciation': validates_data_used_file(kwargs, ['Seazonality_asset_depreciation', 'id_seasonality_detail.december'], type_format_number),

            'status': translate_language("field_status_"+(validates_data_used_file(kwargs, ['status'], 0) ), request),
        }

        rest_data.append(new)
    
    try:
        if format_file == 'csv':
            return generic_csv(mapping, header, rest_data, translate_language('label_assetItems_download', request) )
        elif format_file == 'xlsx':
            styles=[
                {
                    'fields':[
                        'year_asset_item',
                        'year_asset_item_cost', 
                        'year_asset_depreciation', 
                    ], 
                    'number_format': '0'
                },
                {
                    'fields':[
                        'january_asset_item', 'february_asset_item', 'march_asset_item',
                        'april_asset_item', 'may_asset_item', 'june_asset_item',
                        'july_asset_item', 'august_asset_item', 'september_asset_item',
                        'october_asset_item', 'november_asset_item', 'december_asset_item',

                        'january_asset_item_cost', 'february_asset_item_cost', 'march_asset_item_cost',
                        'april_asset_item_cost', 'may_asset_item_cost', 'june_asset_item_cost',
                        'july_asset_item_cost', 'august_asset_item_cost', 'september_asset_item_cost',
                        'october_asset_item_cost', 'november_asset_item_cost', 'december_asset_item_cost',

                        'january_asset_depreciation', 'february_asset_depreciation', 'march_asset_depreciation',
                        'april_asset_depreciation', 'may_asset_depreciation', 'june_asset_depreciation',
                        'july_asset_depreciation', 'august_asset_depreciation', 'september_asset_depreciation',
                        'october_asset_depreciation', 'november_asset_depreciation', 'december_asset_depreciation',

                    ], 
                    'number_format': '#,##0.0000'
                }
            ]
            return generic_xls(mapping, header, rest_data, translate_language('label_assetItems_download', request), styles)
        elif format_file == 'pdf':
            return generic_pdf(mapping, header, rest_data, translate_language('label_assetItems_download', request) )
        else:
            return Response({'error':  translate_language_error('error_unknown_format_file', request)}, status=status.HTTP_400_BAD_REQUEST)
    except:  # pragma: no cover
        # just to protect endpoint
        return Response({'error': translate_language_error('error_undefined', request) } , status=status.HTTP_400_BAD_REQUEST)

# validate years duplicate
def validate_year(data, action, typeName, pkAssets):
    if not typeName==SeasonalityAssetItemCost:
        for kwargs in range(len(data)):                
            for kwargsIntern in range(len(data)):
                if action=='PUT' and kwargs==0:
                    if str( Seasonality.objects.get(pk=data[kwargsIntern]['id_seasonality']).year ) != data[kwargsIntern]['Seasonality']['year']:
                        if len( typeName.objects.filter(id_asset_items=pkAssets ,id_seasonality__year=data[kwargsIntern]['Seasonality']['year']) )>0:
                            return True
                elif action=='POST' and kwargs==0:
                    if len( typeName.objects.filter(id_asset_items=pkAssets ,id_seasonality__year=data[kwargsIntern]['Seasonality']['year']) )>0:
                        return True
                if data[kwargs]['Seasonality']['year']==data[kwargsIntern]['Seasonality']['year'] and kwargs!=kwargsIntern :
                    return True
    else:
        for kwargs in range(len(data)):                
            for kwargsIntern in range(len(data)):
                if action=='PUT' and kwargs==0:
                    if str( Seasonality.objects.get(pk=data[kwargsIntern]['id_seazonality_asset']).year ) != data[kwargsIntern]['Seasonality']['year']:
                        if len( typeName.objects.filter(id_asset_items=pkAssets ,id_seazonality_asset__year=data[kwargsIntern]['Seasonality']['year']) )>0:
                            return True
                elif action=='POST' and kwargs==0:
                    if len( typeName.objects.filter(id_asset_items=pkAssets ,id_seazonality_asset__year=data[kwargsIntern]['Seasonality']['year']) )>0:
                        return True
                if data[kwargs]['Seasonality']['year']==data[kwargsIntern]['Seasonality']['year'] and kwargs!=kwargsIntern :
                    return True
    return False

# Seasonality Asset Item, insert new Seasonality 
@api_view(['POST'])
@check_module(modules.asset_item, [permissions.EDITN1])
def session_asset_items_post_Seasonality_Asset_Item(request, pk, format=None):
    observation_log = ""
    if 'observation_log' in request.data:
        observation_log = request.data['observation_log']

    serializer_context = {
        'request': request,
        'observation_log': observation_log
    }
    # SEASONALITY
    if request.method == 'POST':
        data = request.data['Seasonality_asset_item']
        try:
            assetitem = AssetItems.objects.get(pk=pk)
        except AssetItems.DoesNotExist:
            return Response({'error': translate_language_error('error_asset_item_not_exist', request) }, status=status.HTTP_400_BAD_REQUEST)
        errors = {}
        array_seasonality = []

        # validate years duplicate
        if validate_year(data, "POST", SeasonalityAssetItem, pk):
            return Response({'error': translate_language_error('error_year_already_register', request)}, status=status.HTTP_400_BAD_REQUEST)

        try:
            for index in range(len(data)):
                data[index]['id_asset_items'] = assetitem.id_asset_items
                kwargs = data[index]['Seasonality']
                serializerSeasonality = SeasonalitySerializerAssetItems(data=kwargs, context=serializer_context)
                if serializerSeasonality.is_valid():
                    serializerSeasonality.save()
                    pkSeasonality = serializerSeasonality.data[
                        'id_seasonality']  # Save Pk from created code Seasonality
                    data[index]['id_seasonality'] = pkSeasonality  # returns data to pkSeasonality

                    array_seasonality.append(pkSeasonality)
                    serializerSeasonalityAssetItem = SeasonalityAssetItemSerializer(data=data[index],
                                                                                    context=serializer_context)
                    if serializerSeasonalityAssetItem.is_valid():
                        serializerSeasonalityAssetItem.save()
                    else:
                        errors['erro'] = serializerSeasonalityAssetItem.errors
                else:
                    errors['erro'] = serializerSeasonality.errors

            if not errors:
                serializer = collections.OrderedDict(get_data_asset_items(pk))
                return Response(serializer, status=status.HTTP_200_OK)
            else:
                ## deletar os itens 
                for instance in SeasonalityAssetItem.objects.filter(id_seasonality__in=array_seasonality):
                    instance.delete()

                for instance in Seasonality.objects.filter(id_seasonality__in=array_seasonality):
                    instance.delete()
                return Response(errors, status=status.HTTP_400_BAD_REQUEST)
        except:
            return Response({'error': translate_language_error('error_save_sasonality_asset_item', request) }, status=status.HTTP_400_BAD_REQUEST)


# Seasonality Asset Item, Update Seasonality
@api_view(['PUT'])
@check_module(modules.asset_item, [permissions.EDITN1])
def session_asset_items_put_Seasonality_Asset_Item(request, format=None):
    observation_log = ""
    if 'observation_log' in request.data:
        observation_log = request.data['observation_log']

    serializer_context = {
        'request': request,
        'observation_log': observation_log
    }
    # SEASONALITY
    if request.method == 'PUT':
        data = request.data['Seasonality_asset_item']
        errors = {}

        # validate years duplicate
        if validate_year(data, "PUT", SeasonalityAssetItem, data[0]['id_asset_items']):
            return Response({'error': translate_language_error('error_year_already_register', request) }, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            for index in range(len(data)):
                kwargs = data[index]['Seasonality']
                seasonality_model = Seasonality.objects.get(pk=kwargs['id_seasonality'])

                serializerSeasonality = SeasonalitySerializerAssetItems(seasonality_model,
                                                                        data=kwargs, context=serializer_context)
                if serializerSeasonality.is_valid():
                    serializerSeasonality.save()
                else:
                    errors['erro'] = serializerSeasonality.errors

            if not errors:
                return Response({}, status=status.HTTP_200_OK)
            else:
                return Response(errors, status=status.HTTP_400_BAD_REQUEST)
        except:
            return Response({'error': translate_language_error('error_save_sasonality_asset_item', request) }, status=status.HTTP_400_BAD_REQUEST)


# Seasonality Asset Item Depreciation, insert new Seasonality
@api_view(['POST'])
@check_module(modules.asset_item, [permissions.EDITN1])
def session_asset_items_post_Seasonality_Depreciation(request, pk, format=None):
    observation_log = ""
    if 'observation_log' in request.data:
        observation_log = request.data['observation_log']

    serializer_context = {
        'request': request,
        'observation_log': observation_log
    }
    # SEASONALITY
    if request.method == 'POST':
        data = request.data['Seazonality_asset_depreciation']
        try:
            assetitem = AssetItems.objects.get(pk=pk)
        except AssetItems.DoesNotExist:
            return Response({'error': translate_language_error('error_asset_item_not_exist', request)}, status=status.HTTP_400_BAD_REQUEST)

        errors = {}
        array_seasonality = []

        # validate years duplicate
        if validate_year(data, "POST", SeazonalityAssetItemDepreciation, pk):
            return Response({'error': translate_language_error('error_year_already_register', request)}, status=status.HTTP_400_BAD_REQUEST)

        try:
            for index in range(len(data)):
                data[index]['id_asset_items'] = assetitem.id_asset_items
                kwargs = data[index]['Seasonality']
                serializerSeasonality = SeasonalitySerializerAssetItems(data=kwargs, context=serializer_context)
                if serializerSeasonality.is_valid():
                    serializerSeasonality.save()
                    pkSeasonality = serializerSeasonality.data['id_seasonality']  # Save Pk from created code Seasonality
                    data[index]['id_seasonality'] = pkSeasonality  # returns data to pkSeasonality

                    array_seasonality.append(pkSeasonality)
                    serializerSeazonalityAssetItemDepreciation = SeazonalityAssetItemDepreciationSerializer(data=data[index],context=serializer_context)
                    if serializerSeazonalityAssetItemDepreciation.is_valid():
                        serializerSeazonalityAssetItemDepreciation.save()
                    else:
                        errors['erro'] = serializerSeazonalityAssetItemDepreciation.errors

                else:
                    errors['erro'] = serializerSeasonality.errors

            if not errors:
                serializer = collections.OrderedDict(get_data_asset_items(pk))
                return Response(serializer, status=status.HTTP_200_OK)
            else:
                ## deletar os itens 
                for instance in SeazonalityAssetItemDepreciation.objects.filter(id_seasonality__in=array_seasonality):
                    instance.delete()

                for instance in Seasonality.objects.filter(id_seasonality__in=array_seasonality):
                    instance.delete()
                return Response(errors, status=status.HTTP_400_BAD_REQUEST)

        except:
            return Response({'error': translate_language_error('error_save_depreciation', request)}, status=status.HTTP_400_BAD_REQUEST)


# Seasonality Asset Item Depreciation, Update Seasonality
@api_view(['PUT'])
@check_module(modules.asset_item, [permissions.EDITN1])
def session_asset_items_put_Seasonality_Depreciation(request, format=None):
    observation_log = ""
    if 'observation_log' in request.data:
        observation_log = request.data['observation_log']

    serializer_context = {
        'request': request,
        'observation_log': observation_log
    }

    if request.method == 'PUT':
        data = request.data['Seazonality_asset_depreciation']
        errors = {}

        # validate years duplicate
        if validate_year(data, "PUT", SeazonalityAssetItemDepreciation, data[0]['id_asset_items']):
            return Response({'error':  translate_language_error('error_year_already_register', request) }, status=status.HTTP_400_BAD_REQUEST)

        try:
            for index in range(len(data)):
                kwargs = data[index]['Seasonality']
                seasonality_model = Seasonality.objects.get(pk=kwargs['id_seasonality'])

                serializerSeasonality = SeasonalitySerializerAssetItems(seasonality_model,
                                                                        data=kwargs, context=serializer_context)
                if serializerSeasonality.is_valid():
                    serializerSeasonality.save()
                else:
                    errors['erro'] = serializerSeasonality.errors

            if not errors:
                return Response({}, status=status.HTTP_200_OK)
            else:
                return Response(errors, status=status.HTTP_400_BAD_REQUEST)
        except:
            return Response({'error':  translate_language_error('error_save_depreciation', request)}, status=status.HTTP_400_BAD_REQUEST)


# Seasonality Item Cost, insert new Seasonality 
@api_view(['POST'])
@check_module(modules.asset_item, [permissions.EDITN1])
def session_asset_items_post_Seasonality_Item_Cost(request, pk, format=None):
    observation_log = ""
    if 'observation_log' in request.data:
        observation_log = request.data['observation_log']

    serializer_context = {
        'request': request,
        'observation_log': observation_log
    }

    if request.method == 'POST':
        data = request.data['Seasonality_asset_item_cost']
        try:
            assetitem = AssetItems.objects.get(pk=pk)
        except AssetItems.DoesNotExist:
            return Response({'error': translate_language_error('error_asset_item_not_exist', request) }, status=status.HTTP_400_BAD_REQUEST)

        errors = {}
        array_seasonality = []


        # validate years duplicate
        if validate_year(data, "POST", SeasonalityAssetItemCost, pk):
            return Response({'error': translate_language_error('error_year_already_register', request) }, status=status.HTTP_400_BAD_REQUEST)

        try:
            for index in range(len(data)):
                kwargs = data[index]['Seasonality']
                data[index]['id_asset_items'] = assetitem.id_asset_items
                serializerSeasonality = SeasonalitySerializerAssetItems(data=kwargs, context=serializer_context)
                if serializerSeasonality.is_valid():
                    serializerSeasonality.save()
                    pkSeasonality = serializerSeasonality.data[
                        'id_seasonality']  # Save Pk from created code Seasonality
                    data[index]['id_seazonality_asset'] = pkSeasonality  # returns data to pkSeasonality
                    array_seasonality.append(pkSeasonality)

                    serializerSeasonalityAssetItemCost = SazonalityAssetItemCostSerializer(data=data[index],
                                                                                           context=serializer_context)
                    if serializerSeasonalityAssetItemCost.is_valid():
                        serializerSeasonalityAssetItemCost.save()
                    else:
                        errors['erro'] = serializerSeasonalityAssetItemCost.errors
                else:
                    errors['erro'] = serializerSeasonality.errors

            if not errors:
                serializer = collections.OrderedDict(get_data_asset_items(pk))
                return Response(serializer, status=status.HTTP_200_OK)
            else:
                ## deletar os itens 
                for instance in SeasonalityAssetItemCost.objects.filter(id_seasonality__in=array_seasonality):
                    instance.delete()

                for instance in Seasonality.objects.filter(id_seasonality__in=array_seasonality):
                    instance.delete()
                return Response(errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({'error':  translate_language_error('error_save_generation_cost', request) }, status=status.HTTP_400_BAD_REQUEST)


# Seasonality Item Cost, Update Seasonality
@api_view(['PUT'])
@check_module(modules.asset_item, [permissions.EDITN1])
def session_asset_items_put_Seasonality_Item_Cost(request, format=None):
    observation_log = ""
    if 'observation_log' in request.data:
        observation_log = request.data['observation_log']

    serializer_context = {
        'request': request,
        'observation_log': observation_log
    }

    if request.method == 'PUT':
        data = request.data['Seasonality_asset_item_cost']
        errors = {}
        
        # validate years duplicate
        if validate_year(data, "PUT", SeasonalityAssetItemCost, data[0]['id_asset_items']):
            return Response({'error': translate_language_error('error_year_already_register', request) }, status=status.HTTP_400_BAD_REQUEST)

        try:
            for index in range(len(data)):
                kwargs = data[index]['Seasonality']
                seasonality_model = Seasonality.objects.filter(pk=kwargs['id_seasonality'])
                if seasonality_model:
                    serializerSeasonality = SeasonalitySerializerAssetItems(seasonality_model[0],
                                                                            data=kwargs, context=serializer_context)
                    if serializerSeasonality.is_valid():
                        serializerSeasonality.save()
                    else:
                        errors['erro'] = serializerSeasonality.errors
                else:
                    return Response(status=status.HTTP_404_NOT_FOUND)

            if not errors:
                return Response({}, status=status.HTTP_200_OK)
            else:
                return Response(errors, status=status.HTTP_400_BAD_REQUEST)
        except:
            return Response({'error':  translate_language_error('error_save_generation_cost', request) }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@check_module(modules.asset_item, [permissions.VIEW, permissions.EDITN1])
def session_log_basic_asset_items(request, pk, format=None):
    """
        List all logs about asset items
    """

    kwargs = {'core': AssetItems, 'core_pk': 'id_asset_items', 'core+': [],
              'child': []}
    try:
        log = generic_log_search(pk, **kwargs)
    except AssetItems.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    #Generate seasonality
    array = []
    kwargs = {'core': SeasonalityAssetItemCost, 'core_pk': 'id_seasonality_asset_item_cost',
              'core+': [{Seasonality: 'id_seazonality_asset'}],
              'child': []}
    for a in SeasonalityAssetItemCost.objects.filter(id_asset_items=pk):
        array.append(generic_log_search(a.id_seasonality_asset_item_cost, **kwargs))

    kwargs = {'core': SeasonalityAssetItem, 'core_pk': 'id_seasonality_asset_item',
              'core+': [{Seasonality: 'id_seasonality'}],
              'child': []}
    for a in SeasonalityAssetItem.objects.filter(id_asset_items=pk):
        array.append(generic_log_search(a.id_seasonality_asset_item, **kwargs))

    kwargs = {'core': SeazonalityAssetItemDepreciation, 'core_pk': 'seazonality_asset_depreciation',
              'core+': [{Seasonality: 'id_seasonality'}],
              'child': []}
    for a in SeazonalityAssetItemDepreciation.objects.filter(id_asset_items=pk):
        array.append(generic_log_search(a.seazonality_asset_depreciation, **kwargs))

    kwargs = log.copy()
    new_seasonality = []    
    for index in range(len(array)):
        if 'seasonality' in array[index]:
            for intern_index in range(len(array[index]['seasonality'])):
                new_seasonality.append(array[index]['seasonality'][intern_index])
    
    kwargs['SEASONALITY'] = new_seasonality
    
    kwargsAux=generic_log_search_basic(kwargs)
    log={'logs':kwargsAux}    

    id_array=[]
    #company
    company_array=[]
    for items in kwargsAux:
        if items['ASSET_ITEMS']:
            a=items['ASSET_ITEMS']['new_value']['id_company']
            if 'value' in a:
                id_num=a['value']
            else:
                id_num=a
            if id_num not in id_array:
                id_array.append(id_num)
                company_array.append({'id_company': id_num, 'company_name': Company.objects.get(pk=id_num).company_name })
    
    #energy_composition
    composition_array=[]
    id_array.clear()
    for items in kwargsAux:
        if items['ASSET_ITEMS']:
            if 'id_energy_composition' in items['ASSET_ITEMS']['new_value']:
                a=items['ASSET_ITEMS']['new_value']['id_energy_composition']
                if 'value' in a:
                    id_num=a['value']
                else:
                    id_num=a
                if id_num not in id_array:
                    id_array.append(id_num)
                    composition_array.append({'id_energy_composition': id_num, 'composition_name': EnergyComposition.objects.get(pk=id_num).composition_name })
    
    #assets
    id_array.clear()
    assets_array=[]
    for items in kwargsAux:
        if items['ASSET_ITEMS']:
            if items['ASSET_ITEMS']['new_value']:
                a=items['ASSET_ITEMS']['new_value']['id_assets']
                if 'value' in a:
                    id_num=a['value']
                else:
                    id_num=a
                if id_num not in id_array:
                    id_array.append(id_num)
                    assets_array.append({'id_assets': id_num, 'company_name_assets': (Assets.objects.get(pk=id_num).id_company).company_name, 'code_ccee':(Assets.objects.get(pk=id_num).id_ccee_siga).code_ccee })

    seasonality_ids = list(map(lambda x: x['field_pk'], new_seasonality))
    
    log['statics_relateds']={
        'company': company_array,
        'energy_composition':composition_array,
        'assets':assets_array,
        'seasonality_asset_item_cost': SeasonalityAssetItemCost.objects.filter(id_seazonality_asset__in=seasonality_ids).values(),
        'seasonality_asset_item': SeasonalityAssetItem.objects.filter(id_seasonality__in=seasonality_ids).values(),
        'seazonality_asset_item_depreciation': SeazonalityAssetItemDepreciation.objects.filter(id_seasonality__in=seasonality_ids).values()
    }
    return Response(log)

@api_view(['GET'])
@check_module(modules.asset_item, [permissions.VIEW, permissions.EDITN1])
def session_asset_items_get_find_basic(request, format=None):
    """
        List all companies 
    """
    if request.method == 'GET':
        asset_item = function_generic_find(request)
        data, page_count, page_next, page_previous = generic_paginator(request, asset_item)
        serializer = function_generic_format_return_find(request, data)

        response = collections.OrderedDict([
            ('count', page_count),
            ('next', page_next),
            ('previous', page_previous),
            ('results', serializer)
        ])
        return Response(response)



def function_generic_find(request):
    kwargs = {
        'company_name': 'id_company__company_name__contains',
        'cost_center': 'id_energy_composition__cost_center__contains',
        'name_ccee': 'id_assets__id_ccee_siga__name_ccee__contains',
        'composition_name': 'id_energy_composition__composition_name__contains', 
        'company_name_assets': 'id_assets__id_company__company_name__contains',
        'status': 'status__contains'
    }
    kwargs_order = {
        'company_name': 'id_company__company_name',
        'cost_center': 'id_energy_composition__cost_center',
        'name_ccee': 'id_assets__id_ccee_siga__name_ccee',
        'composition_name': 'id_energy_composition__composition_name',
        'company_name_assets': 'id_assets__id_company__company_name',
        'status': 'status',

        '-company_name': '-id_company__company_name',
        '-cost_center': '-id_energy_composition__cost_center',
        '-name_ccee': '-id_assets__id_ccee_siga__name_ccee',
        '-composition_name': '-id_energy_composition__composition_name',
        '-company_name_assets': '-id_assets__id_company__company_name',
        '-status': '-status'
    }
    ids = generic_queryset_filter(request, AssetItems, 'id_asset_items', **kwargs)
    if request.query_params.get('ordering') in kwargs_order:
        order_by = kwargs_order[request.query_params.get('ordering')]
    else:
        order_by = kwargs_order['company_name']
    
    asset_item = AssetItems.objects \
        .select_related('id_company').select_related('id_energy_composition') \
        .select_related('id_assets__id_ccee_siga').select_related('id_assets__id_company') \
        .prefetch_related('assetitem_seasonality__id_seasonality').prefetch_related('assetitem_cost__id_seazonality_asset')\
            .prefetch_related('assetitem_depreciation__id_seasonality')\
        .filter(id_asset_items__in=ids).order_by(order_by)
    return asset_item

def function_generic_format_return_find(request, data):
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
            itemJson=AssetItemsSerializerFindBasic(item, many=False, context=serializer_context).data
            company_detail=CompanySerializerFindBasic(item.id_company, many=False, context=serializer_context).data
            energycomposition_detail=EnergyCompositionSerializerFindBasic(item.id_energy_composition, many=False, context=serializer_context).data
            assets_detail=AssetsSerializerFindBasic(item.id_assets, many=False, context=serializer_context).data
            itemJson['company_detail']=company_detail
            itemJson['energycomposition_detail']=energycomposition_detail
            itemJson['assets_detail']=assets_detail

            cceedescription_detail=CCEEDescriptionSerializerFindBasic(item.id_assets.id_ccee_siga, many=False, context=serializer_context).data if hasattr(item.id_assets, 'id_ccee_siga') else ""
            company=CompanySerializerFindBasic(item.id_assets.id_company, many=False, context=serializer_context).data if hasattr(item.id_assets, 'id_company') else ""
            itemJson['assets_detail']['cceedescription_detail']=cceedescription_detail
            itemJson['assets_detail']['company']=company
        except:
            itemJson = AssetItemsSerializer(item, many=False, context=serializer_context).data


        valueseasonalityAssetItem = []
        valueseasonalityItemCost = []
        valueseasonalityAssetItemDepreciation = []

        for itemSeasonalityAssetItem in item._prefetched_objects_cache['assetitem_seasonality']:
            valueseasonalityAssetItem.append(SeasonalityAssetItemSerializer(itemSeasonalityAssetItem,context=serializer_context).data)
        for itemSeasonalityItemCost in item._prefetched_objects_cache['assetitem_cost']:
            valueseasonalityItemCost.append(SazonalityAssetItemCostSerializer(itemSeasonalityItemCost,context=serializer_context).data)
        for itemSeasonalityAssetItemDepreciation in item._prefetched_objects_cache['assetitem_depreciation']:
            valueseasonalityAssetItemDepreciation.append(SeazonalityAssetItemDepreciationSerializer(itemSeasonalityAssetItemDepreciation, context=serializer_context).data)

        
        itemJson['Seasonality_asset_item'] = valueseasonalityAssetItem
        itemJson['Seasonality_asset_item_cost'] = valueseasonalityItemCost
        itemJson['Seazonality_asset_depreciation'] = valueseasonalityAssetItemDepreciation

        serializer.append(itemJson)

    return serializer