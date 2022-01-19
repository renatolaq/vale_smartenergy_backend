import collections
import json

from django.core.serializers.json import DjangoJSONEncoder
from django.forms import model_to_dict
from rest_framework import status, serializers
from rest_framework.decorators import api_view
from rest_framework.response import Response

from asset_items.models import AssetItems
from asset_items.serializers import AssetItemsSerializer
from usage_contract.models import UsageContract
from assets.models import Submarket, Assets, AssetsComposition, SeasonalityProinfa
from assets.serializers import CCEESerializerAssetsSIGA, CCEESerializerAssetsPROINFA, AssetsSerializer, \
    AssetsCompositionSerializerAssets, SeasonalityProinfaSerializerAssets, \
    SeasonalitySerializerAssets
from assets.serializersViews import CompanyAssetsSerializerView, ProfileAssetsSerializerView, \
    EnergyCompositionAssetsSerializerView, submarketAssetsSerializerView, AssetsCompositionSerializerView, \
    SeasonalityProinfaSerializerView, \
    UsageContractAssetsSerializerView, AssetsSerializerShowView, AssetsSerializerWithItems
from company.models import Company
from core.attachment_utility import generic_pdf, generic_csv, generic_data_csv_list, generic_xls
from core.models import Seasonality, CceeDescription 
from core.views import generic_log_search, generic_queryset_filter, generic_paginator, \
    generic_detail_log, alter_number, generic_log_search_basic, validates_data_used_file
from energy_composition.models import EnergyComposition
from profiles.models import Profile
from locales.translates_function import translate_language_header, translate_language, translate_language_error
from django.db import connection
from SmartEnergy.auth import check_module
import SmartEnergy.auth.permissions as permissions
import SmartEnergy.auth.modules as modules

from profiles.serializers import CCEESerializerProfileFindBasic, ProfileSerializerFindBasic, AgentsSerializerFindBasic
from agents.serializers import CompanySerializerViewFind
# list all assest status = S
@api_view(['GET'])
@check_module(modules.asset, [permissions.VIEW, permissions.EDITN1])
def show_assets(request, format=None):
    observation_log = ""
    if 'observation_log' in request.data:
        observation_log = request.data['observation_log']

    serializer_context = {
        'request': request,
        'observation_log': observation_log
    }

    try:

        kwargs = {'company_name': 'id_company__company_name__contains',
                  'code_ccee': 'id_ccee_siga__code_ccee__contains',
                  'status': 'status__contains'}

        ids = generic_queryset_filter(request, Assets, 'id_assets', **kwargs)
        assets = Assets.objects.filter(id_assets__in=ids, status='S').order_by('id_company__company_name')
        serializer = AssetsSerializerShowView(assets, many=True, context=serializer_context)

        return Response(serializer.data)

    except Assets.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)


# alterar show_company

# Bring data to popular lists: company, profile, EnergyComposition, submarket
@api_view(['GET'])
@check_module(modules.asset, [permissions.VIEW, permissions.EDITN1])
def show_company(request, format=None):
    observation_log = ""
    if 'observation_log' in request.data:
        observation_log = request.data['observation_log']  # pragma: no cover

    serializer_context = {
        'request': request,
        'observation_log': observation_log
    }
    company = (Company.objects.filter(type="F",status="S") | Company.objects.filter(type="R",status="S")).order_by('company_name')
    serializer = CompanyAssetsSerializerView(company, many=True, context=serializer_context)
    return Response(serializer.data)


@api_view(['GET'])
@check_module(modules.asset, [permissions.VIEW, permissions.EDITN1])
def show_profile(request, format=None):
    observation_log = ""
    if 'observation_log' in request.data:
        observation_log = request.data['observation_log']  # pragma: no cover

    serializer_context = {
        'request': request,
        'observation_log': observation_log
    }
    profile = Profile.objects\
        .select_related('id_agents').select_related('id_agents__id_company')\
        .filter(status="S").order_by('name_profile')
    
    try:
        serializer=[]
        for item in profile:
            itemJson=ProfileSerializerFindBasic(item, many=False, context=serializer_context).data
            agents_detail=AgentsSerializerFindBasic(item.id_agents, many=False, context=serializer_context).data
            company_detail=CompanySerializerViewFind(item.id_agents.id_company, many=False, context=serializer_context).data if hasattr(item.id_agents, 'id_company') else ""
            itemJson['agents_detail']=agents_detail
            itemJson['agents_detail']['company_detail']=company_detail
            serializer.append(itemJson)
    except :
        serializer = ProfileAssetsSerializerView(profile, many=True, context=serializer_context).data
    return Response(serializer)


@api_view(['GET'])
@check_module(modules.asset, [permissions.VIEW, permissions.EDITN1])
def show_energyComposition(request, pk, format=None):
    observation_log = ""
    if 'observation_log' in request.data:
        observation_log = request.data['observation_log']  # pragma: no cover

    serializer_context = {
        'request': request,
        'observation_log': observation_log
    }
    energyComposition = EnergyComposition.objects.filter(
        id_company=pk, status="S").order_by('composition_name')
    serializer = EnergyCompositionAssetsSerializerView(
        energyComposition, many=True, context=serializer_context)
    return Response(serializer.data)


@api_view(['GET'])
@check_module(modules.asset, [permissions.VIEW, permissions.EDITN1])
def show_contractUse(request, pk, format=None):
    observation_log = ""
    if 'observation_log' in request.data:
        observation_log = request.data['observation_log']  # pragma: no cover

    serializer_context = {
        'request': request,
        'observation_log': observation_log
    }
    contractUse = UsageContract.objects.filter(id_company=pk).order_by('contract_number')
    serializer = UsageContractAssetsSerializerView(contractUse, many=True, context=serializer_context)
    return Response(serializer.data)


@api_view(['GET'])
@check_module(modules.asset, [permissions.VIEW, permissions.EDITN1])
def show_submarket(request, format=None):
    observation_log = ""
    if 'observation_log' in request.data:
        observation_log = request.data['observation_log']  # pragma: no cover

    serializer_context = {
        'request': request,
        'observation_log': observation_log
    }
    submarket = Submarket.objects.filter(status='S').order_by('description')
    serializer = submarketAssetsSerializerView(
        submarket, many=True, context=serializer_context)
    return Response(serializer.data)


# validate years duplicate
def validate_year(data, action, id_ccee_data):
    for kwargs in range(len(data)):                
        for kwargsIntern in range(len(data)):
            if action=='PUT' and kwargs==0:
                if str(Seasonality.objects.get(pk=data[kwargsIntern]['id_seasonality']).year) != data[kwargsIntern]['year']:
                    if len( SeasonalityProinfa.objects.filter(id_ccee= id_ccee_data, id_seasonality__year=data[kwargsIntern]['year']) )>0:
                        return True

            elif action=='POST' and kwargs==0:
                if len( SeasonalityProinfa.objects.filter(id_ccee= id_ccee_data, id_seasonality__year=data[kwargsIntern]['year']) )>0:
                    return True
            
            if data[kwargs]['year']==data[kwargsIntern]['year'] and kwargs!=kwargsIntern :
                return True
    return False

def get_data_asset(pk):  # Get Detailed Return
    """
        List data about company
    """
    try:
        asset = Assets.objects.get(pk=pk)
        kwargs = json.loads(json.dumps(
            model_to_dict(asset), cls=DjangoJSONEncoder))
    except Assets.DoesNotExist:  # pragma: no cover
        return Response(status=status.HTTP_404_NOT_FOUND)
        # submarket
    try:
        submarket = Submarket.objects.get(pk=asset.id_submarket_id)
        kwargs['id_submarket'] = json.loads(json.dumps(
            model_to_dict(submarket), cls=DjangoJSONEncoder))
    except Submarket.DoesNotExist:  # pragma: no cover
        kwargs['id_submarket'] = {}
        # company
    try:
        company = Company.objects.get(pk=asset.id_company_id)
        kwargs['id_company'] = json.loads(json.dumps(
            model_to_dict(company), cls=DjangoJSONEncoder))

    except Company.DoesNotExist:  # pragma: no cover
        kwargs['id_company'] = {}
        # profile
    try:
        profile = Profile.objects.get(pk=asset.id_profile_id)
        kwargs['id_profile'] = json.loads(json.dumps(
            model_to_dict(profile), cls=DjangoJSONEncoder))
    except Profile.DoesNotExist:  # pragma: no cover
        kwargs['id_profile'] = {}
        # ccee_SIGA
    try:
        cceeSiga = CceeDescription.objects.get(pk=asset.id_ccee_siga_id)
        kwargs['id_ccee_siga'] = json.loads(json.dumps(
            model_to_dict(cceeSiga), cls=DjangoJSONEncoder))
    except CceeDescription.DoesNotExist:  # pragma: no cover
        kwargs['id_ccee_siga'] = {}
        # ccee_PROINFA
    try:
        cceeProinfa = CceeDescription.objects.get(pk=asset.id_ccee_proinfa_id)
        kwargs['id_ccee_proinfa'] = json.loads(json.dumps(
            model_to_dict(cceeProinfa), cls=DjangoJSONEncoder))
    except CceeDescription.DoesNotExist:  # pragma: no cover
        kwargs['id_ccee_proinfa'] = {}
        # AssetsComposition
    try:
        assetsComposition = AssetsComposition.objects.get(
            id_assets_id=pk, status="S")
        kwargs['Assets_Composition'] = json.loads(json.dumps(
            model_to_dict(assetsComposition), cls=DjangoJSONEncoder))
    except AssetsComposition.DoesNotExist:  # pragma: no cover
        kwargs['Assets_Composition'] = {}
        # asset_Items
    array_assetItems = []
    # for assetItems in AssetItems.objects.filter(id_assets=asset.id_assets):
    for assets_items_detail in AssetItems.objects.values(
            'id_asset_items',
            'id_assets',
            'id_company',
            'id_company__company_name',
            'id_company__characteristics',
            'id_energy_composition',
            'id_energy_composition__composition_name',
            'id_energy_composition__cost_center').filter(id_assets=asset.id_assets):
        
        assets_items_detail['id_company__characteristics_traduct']=assets_items_detail['id_company__characteristics']
        array_assetItems.append(assets_items_detail)
    kwargs['AssetItems'] = array_assetItems

    array_SeasonalityProinfa = []
    for seasonality_proinfa in SeasonalityProinfa.objects.filter(id_ccee=asset.id_ccee_proinfa):
        seasonality = Seasonality.objects.get(pk=int(seasonality_proinfa.id_seasonality_id))
        seasonalityJson = json.loads(json.dumps(model_to_dict(seasonality), cls=DjangoJSONEncoder))
        array_SeasonalityProinfa.append(seasonalityJson)

    kwargs['Seasonality_proinfa'] = {'Seasonality': array_SeasonalityProinfa}
    return kwargs

@api_view(['GET'])
@check_module(modules.asset, [permissions.VIEW, permissions.EDITN1])
def session_assets_get_find_basic(request, format=None):
    """
        List all companies 
    """
    if request.method == 'GET':
        assets_object = function_generic_find(request)
        data, page_count, page_next, page_previous = generic_paginator(request, assets_object)
        serializer = function_format_response_find(request, data)

        response = collections.OrderedDict([
            ('count', page_count),
            ('next', page_next),
            ('previous', page_previous),
            ('results', serializer)
        ])
        #print(connection.queries)
        return Response(response)

@api_view(['GET'])
@check_module(modules.asset, [permissions.VIEW, permissions.EDITN1])
def session_assets_get(request, format=None):
    """
        List all companies 
    """
    observation_log = ""
    if 'observation_log' in request.data:
        observation_log = request.data['observation_log']  # pragma: no cover

    serializer_context = {
        'request': request,
        'observation_log': observation_log
    }

    if request.method == 'GET':
        kwargs = {'company_name': 'id_assets__id_company__company_name__contains',
                  'name_profile': 'id_assets__id_profile__name_profile__contains',
                  'code_ccee': 'id_assets__id_ccee_siga__code_ccee__contains',
                  'show_balance': 'id_assets__show_balance__contains',
                  'composition_name': 'id_energy_composition__composition_name__contains',
                  'status': 'id_assets__status__contains'}

        kwargs_order = {'company_name': 'id_assets__id_company__company_name',
                        'name_profile': 'id_assets__id_profile__name_profile',
                        'code_ccee': 'id_assets__id_ccee_siga__code_ccee',
                        'show_balance': '-id_assets__show_balance',
                        'composition_name': 'id_energy_composition__composition_name',
                        'status': 'id_assets__status',

                        '-company_name': '-id_assets__id_company__company_name',
                        '-name_profile': '-id_assets__id_profile__name_profile',
                        '-code_ccee': '-id_assets__id_ccee_siga__code_ccee',
                        '-show_balance': 'id_assets__show_balance',
                        '-composition_name': '-id_energy_composition__composition_name',
                        '-status': '-id_assets__status'
                        
                        }

        ids = generic_queryset_filter(request, AssetsComposition, 'id_assets', **kwargs)
        if request.query_params.get('ordering') in kwargs_order:
            order_by = kwargs_order[request.query_params.get('ordering')]
        else:
            order_by = kwargs_order['company_name']
        assets = AssetsComposition.objects.filter(id_assets__in=ids).order_by(order_by)
        data, page_count, page_next, page_previous = generic_paginator(request, assets)
        serializer = AssetsCompositionSerializerView(data, many=True, context=serializer_context)

        response = collections.OrderedDict([
            ('count', page_count),
            ('next', page_next),
            ('previous', page_previous),
            ('results', serializer.data)
        ])
        return Response(response)

@api_view(['POST'])
@check_module(modules.asset, [permissions.EDITN1])
def session_assets_post(request, format=None):
    """
        create a new company
    """
    observation_log = ""
    if 'observation_log' in request.data:
        observation_log = request.data['observation_log']  # pragma: no cover

    serializer_context = {
        'request': request,
        'observation_log': observation_log
    }

    if request.method == 'POST':
        data = request.data  # create data to save pks and use when registering assets
        response_error = {}
        # Insert code SIGA, then code PROINFA, check the id_submarket of the selected description and create an ASSETS, otherwise undo all insertion
        # SIGA
        serializerSiga = CCEESerializerAssetsSIGA(data=request.data['id_ccee_siga'], context=serializer_context)
        if serializerSiga.is_valid():
            # PROINFA

            #If json is passed in the field Id_ccee_proinfa it checks if the creation is valid (If not validate = 0 and generates the error in proinfa), otherwise it processes.
            validate=1 #1Passed null  0=erro  2=create
            
            if request.data['id_ccee_proinfa']['code_ccee'] is not None and request.data['id_ccee_proinfa']['code_ccee'] != "":
                serializerProinfa = CCEESerializerAssetsPROINFA(data=request.data['id_ccee_proinfa'],context=serializer_context)
                validate=0

                if serializerProinfa.is_valid():
                    validate = 2
            else:
                data['id_ccee_proinfa'] = None
            if validate != 0:
                # SUBMARKET
                submarket = Submarket.objects.filter(
                    id_submarket=data['id_submarket']['id_submarket'])  # check description id
                if submarket:
                    data['id_submarket'] = submarket[0].id_submarket  # returns data to id_submarket found

                    if validate == 2:  # save Proinfa
                        serializerProinfa.save()
                        pkProinfa = serializerProinfa.data['id_ccee']  # Save Pk from created code ROINFA
                        data['id_ccee_proinfa'] = pkProinfa  # returns data to pkPROINFA

                    serializerSiga.save()
                    pkSiga = serializerSiga.data['id_ccee']  # Save Pk from created code SIGA
                    data['id_ccee_siga'] = pkSiga  # returns data to pkSIGA

                    # ASSETS
                    if data['id_company'] and data['id_profile'] :
                        data['id_company'] = data['id_company']['id_company']
                        data['id_profile'] = data['id_profile']['id_profile']
                    else:
                        return Response({'error': translate_language_error('error_company_and_profile_null', request) }, status=status.HTTP_400_BAD_REQUEST)
                    assets = AssetsSerializer(data=data, context=serializer_context)
                    if assets.is_valid():
                        assets.save()
                        pkAssets = assets.data['id_assets']  # Save Pk from created code Assets
                        data['Assets_Composition'][
                            'id_assets'] = pkAssets  # Returns pk to register the energy composition
                        # AssetsComposition
                        assetsComposition = AssetsCompositionSerializerAssets(data=data['Assets_Composition'],
                                                                              context=serializer_context)
                        if assetsComposition.is_valid():
                            assetsComposition.save()
                        else:  # error inserting AssetsComposition

                            assets = Assets.objects.get(pk=pkAssets)
                            assets.delete()
                            cceeSiga = CceeDescription.objects.get(pk=pkSiga)
                            cceeSiga.delete()
                            if validate == 2:
                                cceeProinfa = CceeDescription.objects.get(pk=pkProinfa)
                                cceeProinfa.delete()
                            response_error = assetsComposition.errors

                    else:  # Error inserting assets
                        cceeSiga = CceeDescription.objects.get(pk=pkSiga)
                        cceeSiga.delete()
                        if validate == 2:
                            cceeProinfa = CceeDescription.objects.get(pk=pkProinfa)
                            cceeProinfa.delete()
                        response_error = assets.errors

                else:  # Error search submarket
                    response_error = {translate_language_error('error_submarket_invalid', request) }

            else:  # Error inserting CceeDescription PROINFA
                response_error = serializerProinfa.errors

        else:  # Error inserting CceeDescription SIGA
            response_error = serializerSiga.errors

        if response_error:
            return Response(response_error, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(assets.data, status=status.HTTP_201_CREATED)


@api_view(['PUT'])
@check_module(modules.asset, [permissions.EDITN1])
def session_assets_put(request, pk, format=None):
    """
        Retrieve, update or delete a specific company.
    """
    observation_log = ""
    if 'observation_log' in request.data:
        observation_log = request.data['observation_log']  # pragma: no cover

    serializer_context = {
        'request': request,
        'observation_log': observation_log
    }

    try:
        assets = Assets.objects.get(pk=pk)
    except Assets.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'PUT':
        data = request.data
        if 'id_ccee_siga' in data:
            siga_model = CceeDescription.objects.get(pk=assets.id_ccee_siga_id)
            cceeSiga = CCEESerializerAssetsSIGA(siga_model, data=data['id_ccee_siga'], context=serializer_context)
            if cceeSiga.is_valid():
                cceeSiga.save()
                data['id_ccee_siga'] = assets.id_ccee_siga_id
            else:
                return Response(cceeSiga.errors, status=status.HTTP_400_BAD_REQUEST)
        
        if request.data.get('id_ccee_proinfa') and request.data['id_ccee_proinfa'].get('code_ccee') and assets.id_ccee_proinfa:
            proinfa_model = CceeDescription.objects.get(pk=assets.id_ccee_proinfa_id)
            cceeProinfa = CCEESerializerAssetsPROINFA(proinfa_model, data=data['id_ccee_proinfa'],
                                                        context=serializer_context)
            if cceeProinfa.is_valid():
                cceeProinfa.save()
                data['id_ccee_proinfa'] = cceeProinfa.data['id_ccee']
            else:
                return Response(cceeProinfa.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            data['id_ccee_proinfa'] = None

        if 'Assets_Composition' in data:
            assetsCompositionOld = AssetsComposition.objects.filter(id_assets=pk).first()
            assetsComposition = AssetsCompositionSerializerAssets(assetsCompositionOld, data['Assets_Composition'],
                                                                  context=serializer_context)
            if assetsComposition.is_valid():
                assetsComposition.save()
            else:
                return Response(assetsComposition.errors, status=status.HTTP_400_BAD_REQUEST)

        submarket = Submarket.objects.filter(id_submarket=data['id_submarket']['id_submarket'])  # check description id

        if submarket:  # Saves changes made to:submarket,cceeSiga,cceeProinfa

            data['id_submarket'] = submarket[0].id_submarket  # returns data to id_submarket found

            assets_model = Assets.objects.get(pk=pk)
            if data['id_company'] and data['id_profile']:
                data['id_company'] = data['id_company']['id_company']
                data['id_profile'] = data['id_profile']['id_profile']
            else:
                return Response({'error': translate_language_error('error_company_and_profile_null', request) },
                                status=status.HTTP_400_BAD_REQUEST)
            assetsSerializer = AssetsSerializer(assets_model, data=data, context=serializer_context)
            if assetsSerializer.is_valid():
                assetsSerializer.save()
                serializer = collections.OrderedDict(get_data_asset(pk))
                return Response(serializer, status=status.HTTP_200_OK)
            else:
                return Response(assetsSerializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({translate_language_error('error_submarket_invalid', request)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@check_module(modules.asset, [permissions.VIEW, permissions.EDITN1])
def session_assets_get_detail(request, pk, format=None):
    """
        specific company.
    """

    if request.method == 'GET':
        serializer = collections.OrderedDict(get_data_asset(pk))
        return Response(serializer)

# Insert new Seasonality
@api_view(['POST'])
@check_module(modules.asset, [permissions.EDITN1])
def session_assets_post_Seasonality(request, pk, format=None):
    observation_log = ""
    if 'observation_log' in request.data:
        observation_log = request.data['observation_log']  # pragma: no cover

    serializer_context = {
        'request': request,
        'observation_log': observation_log
    }
    # SEASONALITY
    if request.method == 'POST':
        data = request.data['Seasonality_proinfa']
        try:
            assets = Assets.objects.get(pk=pk)
        except Assets.DoesNotExist:
            raise serializers.ValidationError(translate_language_error('error_asset_not_exist', request))

        if assets.id_ccee_proinfa_id:
            data_proinfa = {'id_ccee': assets.id_ccee_proinfa_id}
            array_proinfa = []
            errors = {}

            
            # validate years not duplicate
            if validate_year(data['Seasonality'], 'POST', assets.id_ccee_proinfa_id):
                raise serializers.ValidationError(translate_language_error('error_year_already_register', request) ) 
            # save sazonality    
            for kwargs in data['Seasonality']:
                serializerSeasonality = SeasonalitySerializerAssets(data=kwargs, context=serializer_context)
                if serializerSeasonality.is_valid():
                    serializerSeasonality.save()
                    pkSeasonality = serializerSeasonality.data[
                        'id_seasonality']  # Save Pk from created code Seasonality
                    data_proinfa['id_seasonality'] = pkSeasonality  # returns data to pkSeasonality
                    array_proinfa.append(pkSeasonality)
                    serializerSeasonalityProinfa = SeasonalityProinfaSerializerAssets(data=data_proinfa,
                                                                                      context=serializer_context)
                    if serializerSeasonalityProinfa.is_valid():
                        serializerSeasonalityProinfa.save()
                    else:
                        errors['erro'] = serializerSeasonalityProinfa.errors
                else:
                    errors['erro'] = serializerSeasonality.errors

            if not errors:
                serializer = collections.OrderedDict(get_data_asset(pk))
                return Response(serializer, status=status.HTTP_200_OK)
            else:
                ## deletar os itens 
                for instance in SeasonalityProinfa.objects.filter(id_seasonality__in=array_proinfa):
                    instance.delete()

                for instance in Seasonality.objects.filter(id_seasonality__in=array_proinfa):
                    instance.delete()
                return Response(errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            raise serializers.ValidationError(translate_language_error('error_code_proinfa_invalid', request) )


# Update Seasonality
@api_view(['PUT'])
@check_module(modules.asset, [permissions.EDITN1])
def session_assets_put_Seasonality(request, format=None):
    observation_log = ""
    if 'observation_log' in request.data:
        observation_log = request.data['observation_log']  # pragma: no cover

    serializer_context = {
        'request': request,
        'observation_log': observation_log
    }
    # SEASONALITY
    if request.method == 'PUT':
        data = request.data['Seasonality_proinfa']['Seasonality']
        errors = {}
        
        # validate years duplicate
        if validate_year(data, 'PUT', SeasonalityProinfa.objects.get(id_seasonality=data[0]['id_seasonality']).id_ccee_id):
            raise serializers.ValidationError(translate_language_error('error_year_already_register', request) ) 
                
        for index in range(len(data)):
            kwargs = data[index]
            seasonality_model = Seasonality.objects.get(pk=kwargs['id_seasonality'])

            serializerSeasonality = SeasonalitySerializerAssets(seasonality_model, data=kwargs,
                                                                context=serializer_context)
            if serializerSeasonality.is_valid():
                serializerSeasonality.save()
            else:
                errors['erro'] = serializerSeasonality.errors
        if not errors:
            return Response({}, status=status.HTTP_200_OK)
        else:
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@check_module(modules.asset, [permissions.VIEW, permissions.EDITN1])
def session_assets_file(request, format=None):
    if not (request.query_params.get('format_file', None) is None):
        format_file = request.query_params.get('format_file', None)
    else:
        return Response({'error': translate_language_error('error_format_file_csv_or_pdf', request) }, status=status.HTTP_400_BAD_REQUEST)

    assets_object = function_generic_find(request)
    serializer = function_format_response_find(request, assets_object)

    
    payload = json.dumps(serializer, indent=10, default=str).encode('utf-8')
    rest = json.loads(payload)

    header = {
        'company_name': 'field_company_name',
        'name_profile': 'field_profile_name',
        'code_ccee': 'ccee_code_siga',
        'show_balance': 'field_show_balance',
        'submarket': 'field_submarket',
        'composition_name': 'field_composition_name',
        'status': 'Status',

        'code_ccee_proinfa': 'field_ccee_code_proinfa',
        'year':'field_year',
        'measure_unity':'field_measureUnity',
        "january":'field_january',
        "february":'field_february',
        "march":'field_march',
        "april":'field_april',
        "may":'field_may',
        "june":'field_june',
        "july":'field_july',
        "august":'field_august',
        "september":'field_september',
        "october":'field_october',
        "november":'field_november',
        "december":'field_december',

        'company_name_item': 'field_company_name_item',
        'cost_center': 'field_cost_center',
        'composition_name_item': 'field_energyComposition_item',
        'status_item': 'Status - item'
    }
    header=translate_language_header(header, request)
    mapping = [
        'company_name',
        'name_profile',
        'code_ccee',
        'show_balance',
        'submarket',
        'composition_name',
        'status',

        'code_ccee_proinfa',
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
        "december",

        'company_name_item',
        'cost_center',
        'composition_name_item',
        'status_item',
    ]
    rest = generic_data_csv_list(rest, ['seasonality','asset_item'])
    rest_data = []

    type_format_number=0 if format_file=='pdf' else 1
    for index in range(len(rest)):
        kwargs = rest[index]
        new = {
            'company_name': validates_data_used_file(kwargs, ['id_assets', 'id_company', 'company_name'], 0),
            'name_profile': validates_data_used_file(kwargs, ['id_assets', 'id_profile', 'name_profile'], 0),
            'code_ccee': validates_data_used_file(kwargs, ['id_assets', 'id_ccee_siga', 'code_ccee'], type_format_number), #number

            'submarket': validates_data_used_file(kwargs, ['id_assets', 'id_submarket', 'description'], 0),
            #usage
            'show_balance': translate_language("field_"+( validates_data_used_file(kwargs, ['id_assets', 'show_balance'], 0)  ), request),

            'composition_name': validates_data_used_file(kwargs, ['id_energy_composition', 'composition_name'], 0),
            'status': translate_language("field_status_"+( validates_data_used_file(kwargs, ['id_assets', 'status'], 0)  ), request),

            'code_ccee_proinfa': validates_data_used_file(kwargs, ['id_assets', 'id_ccee_proinfa', 'code_ccee'], type_format_number), #number
            'year': validates_data_used_file(kwargs, ['seasonality', 'id_seasonality.year'], type_format_number), #number
            'measure_unity': validates_data_used_file(kwargs, ['seasonality', 'id_seasonality.measure_unity'], 0),
            'january': validates_data_used_file(kwargs, ['seasonality', 'id_seasonality.january'], type_format_number), #number
            'february': validates_data_used_file(kwargs, ['seasonality', 'id_seasonality.february'], type_format_number), #number
            'march': validates_data_used_file(kwargs, ['seasonality', 'id_seasonality.march'], type_format_number), #number
            'april': validates_data_used_file(kwargs, ['seasonality', 'id_seasonality.april'], type_format_number), #number
            'may': validates_data_used_file(kwargs, ['seasonality', 'id_seasonality.may'], type_format_number), #number
            'june': validates_data_used_file(kwargs, ['seasonality', 'id_seasonality.june'], type_format_number), #number
            'july': validates_data_used_file(kwargs, ['seasonality', 'id_seasonality.july'], type_format_number), #number
            'august': validates_data_used_file(kwargs, ['seasonality', 'id_seasonality.august'], type_format_number), #number
            'september': validates_data_used_file(kwargs, ['seasonality', 'id_seasonality.september'], type_format_number), #number
            'october': validates_data_used_file(kwargs, ['seasonality', 'id_seasonality.october'], type_format_number), #number
            'november': validates_data_used_file(kwargs, ['seasonality', 'id_seasonality.november'], type_format_number), #number
            'december': validates_data_used_file(kwargs, ['seasonality', 'id_seasonality.december'], type_format_number), #number
            
            'company_name_item': validates_data_used_file(kwargs, ['asset_item', 'company_detail.company_name'], 0),
            'cost_center': validates_data_used_file(kwargs, ['asset_item', 'energycomposition_detail.cost_center'], 0),
            'composition_name_item': validates_data_used_file(kwargs, ['asset_item', 'energycomposition_detail.composition_name'], 0),
            'status_item': translate_language("field_status_"+( validates_data_used_file(kwargs, ['asset_item', 'status'], 0) ), request),
        }
            
        rest_data.append(new)

    try:
        if format_file == 'csv':
            return generic_csv(mapping, header, rest_data, translate_language('label_assets_download', request) )
        elif format_file == 'xlsx':
            styles=[
                {
                    'fields': [
                        "code_ccee", "code_ccee_proinfa", "year"
                    ], 
                    'number_format': '0'
                },
                {
                    'fields': [
                        "mwm_volume",
                        "january", "february", "march", 
                        "april", "may", "june", "july", 
                        "august", "september", "october", 
                        "november", "december"
                    ], 
                    'number_format': '#,##0.0000'
                }
            ]
            return generic_xls(mapping, header, rest_data, translate_language('label_assets_download', request), styles)
        elif format_file == 'pdf':
            return generic_pdf(mapping, header, rest_data, translate_language('label_assets_download', request) )
        else:
            return Response({'error': translate_language_error('error_unknown_format_file', request) }, status=status.HTTP_400_BAD_REQUEST)
    except:  # pragma: no cover
        # just to protect endpoint
        return Response({'error': translate_language_error('error_undefined', request) }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@check_module(modules.asset, [permissions.VIEW, permissions.EDITN1])
def session_assets_get_by_profile(request, pk, format=None):
    observation_log = ""
    if 'observation_log' in request.data:
        observation_log = request.data['observation_log']  # pragma: no cover

    serializer_context = {
        'request': request,
        'observation_log': observation_log
    }

    assets = Assets.objects.filter(id_profile_id=pk, status='S')
    serializer = AssetsSerializerWithItems(assets, many=True, context=serializer_context)

    return Response(serializer.data)

@api_view(['GET'])
@check_module(modules.asset, [permissions.VIEW, permissions.EDITN1])
def session_assets_get_by_agent(request, pk, format=None):
    observation_log = ""
    if 'observation_log' in request.data:
        observation_log = request.data['observation_log']  # pragma: no cover

    serializer_context = {
        'request': request,
        'observation_log': observation_log
    }

    assets = Assets.objects.filter(id_profile__id_agents_id=pk, status='S')
    serializer = AssetsSerializerWithItems(assets, many=True, context=serializer_context)

    return Response(serializer.data)

@api_view(['GET'])
@check_module(modules.asset, [permissions.VIEW, permissions.EDITN1])
def session_log_basic_assets(request, pk, format=None):
    """
        List all logs about company
    """
    kwargs = {'core': Assets, 'core_pk': 'id_assets', 'core+': [{CceeDescription:'id_ccee_siga'}],
              'child': [AssetsComposition]}
    try:
        log = generic_log_search(pk, **kwargs)
    except Assets.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    asset = Assets.objects.get(pk=pk)

    #seasonality
    array = []
    kwargs = {'core': SeasonalityProinfa, 'core_pk': 'id_seasonality_proinfa',
              'core+': [{Seasonality: 'id_seasonality'}],
              'child': []}
    for a in SeasonalityProinfa.objects.filter(id_ccee=asset.id_ccee_proinfa):
        array.append(generic_log_search(a.id_seasonality_proinfa, **kwargs) )
    kwargsReturn = log.copy()
    new_seasonality = []
    new_proinfa = []
    for index in range(len(array)):
        if 'seasonality' in array[index]:
            for intern_index in range(len(array[index]['seasonality'])):
                new_seasonality.append(array[index]['seasonality'][intern_index])
    for index in range(len(array)):
        if 'SEASONALITY_PROINFA' in array[index]:
            for intern_index in range(len(array[index]['SEASONALITY_PROINFA'])):
                new_proinfa.append(array[index]['SEASONALITY_PROINFA'][intern_index])
    kwargsReturn['SEASONALITY_PROINFA'] = new_proinfa
    kwargsReturn['SEASONALITY'] = new_seasonality

    if asset.id_ccee_proinfa_id:
        kwargs = {'core': CceeDescription, 'core_pk': 'id_ccee',
                'core+': [],
                'child': []}
        kwargsReturn['CCEE_DESCRIPTION_PROINFA']=(generic_log_search(asset.id_ccee_proinfa_id, **kwargs))
        kwargsReturn['CCEE_DESCRIPTION_PROINFA']=kwargsReturn['CCEE_DESCRIPTION_PROINFA']['CCEE_DESCRIPTION']

    #statics_relateds
    kwargsAux=generic_log_search_basic(kwargsReturn)
    log={'logs':kwargsAux}

    id_array=[]
    #submarket
    submarket_Array=[]
    for items in kwargsAux:
        if items['assets']:
            if items['assets']['new_value']:
                submarket_name= items['assets']['new_value']['id_submarket']
                if 'value' in submarket_name:
                        id_num=submarket_name['value']
                else:
                    id_num=submarket_name
                if id_num not in id_array and id_num:
                    id_array.append(id_num)
                    if Submarket.objects.filter(pk=id_num):
                        submarket_Array.append({'id_submarket':id_num,'description': Submarket.objects.filter(pk=id_num)[0].description })      
    
    #profile
    id_array.clear()
    profile_Array=[]
    for items in kwargsAux:
        if items['assets']: 
            if items['assets']['new_value']: 
                profile_name=items['assets']['new_value']['id_profile'] 
                if 'value' in profile_name:
                    id_num=profile_name['value']
                else:
                    id_num=profile_name
                if id_num not in id_array:
                    id_array.append(id_num)
                    profile_Array.append({'id_profile':id_num,'name_profile':Profile.objects.get(pk=id_num).name_profile})
    
    #company
    id_array.clear()
    company_Array=[]
    for items in kwargsAux:
        if items['assets']:
            if items['assets']['new_value']:
                name_company=items['assets']['new_value']['id_company']
                if 'value' in name_company:
                    id_num=name_company['value']
                else:
                    id_num=name_company
                if id_num not in id_array: 
                    id_array.append(id_num)
                    company_Array.append({'id_company':id_num,'company_name':Company.objects.get(pk=id_num).company_name})
    
    #Energy_Composition
    id_array.clear()
    composition_Array=[]
    for items in kwargsAux:
        if items['ASSETS_COMPOSITION']:
            if items['ASSETS_COMPOSITION']['new_value']:
                if items['ASSETS_COMPOSITION']['new_value']['id_energy_composition']:
                    name_composition=items['ASSETS_COMPOSITION']['new_value']['id_energy_composition']
                    if 'value' in name_composition:
                        id_num=name_composition['value']
                    else:
                        id_num=name_composition
                    if id_num not in id_array and id_num is not None and id_num != 'None': 
                        id_array.append(id_num)
                        composition_Array.append({'id_composition':id_num,'company_name':EnergyComposition.objects.get(pk=id_num).composition_name})
            

    
    log['statics_relateds']={'submarket':submarket_Array, 'profile':profile_Array, 'company':company_Array, 'energy_composition':composition_Array}
    return Response(log)

@api_view(['GET'])
@check_module(modules.asset, [permissions.VIEW, permissions.EDITN1])
def get_profiles_basic(request, format=None):
    profiles = Profile.objects.filter(status='S').order_by('name_profile').values('id_profile', 'name_profile')
    profiles = map(lambda p: {'id_profile': p['id_profile'], 'name_profile': p['name_profile']}, profiles)
    print(connection.queries)
    return Response(profiles)

@api_view(['GET'])
@check_module(modules.asset, [permissions.VIEW, permissions.EDITN1])
def get_generators_assets(request):
    asset_items = AssetItems.objects \
        .select_related("id_assets") \
        .select_related("id_assets__id_profile") \
        .select_related("id_company")
    
    asset_items = asset_items.filter(id_company__characteristics="geradora")

    return Response(map(lambda asset_item: {
        'id_asset_item': int(asset_item.id_asset_items),
        'id_asset': int(asset_item.id_assets.id_assets),
        'id_company': int(asset_item.id_company.id_company),
        'asset_profile_id': int(asset_item.id_assets.id_profile.id_profile),
        'asset_profile_name': asset_item.id_assets.id_profile.name_profile
    }, asset_items))

@api_view(['GET'])
@check_module(modules.asset, [permissions.VIEW, permissions.EDITN1])
def get_consumers_assets(request):
    assets = Assets.objects \
        .select_related("id_profile") \
        .select_related("id_company")

    asset_items = AssetItems.objects \
        .select_related("id_assets") \
        .select_related("id_assets__id_profile") \
        .select_related("id_company")
    
    asset_items = asset_items.filter(id_company__type='F', id_company__characteristics="consumidora", id_assets__show_balance="Asset items")    
    assets = assets.filter(id_company__type='F', id_company__characteristics="consumidora", show_balance="Assets")

    asset_items = list(map(lambda item: {
        'id_asset_item': int(item.id_asset_items),
        'id_asset': int(item.id_assets.id_assets),
        'id_company': int(item.id_company.id_company),
        'asset_profile_id': int(item.id_assets.id_profile.id_profile),
        'asset_profile_name': item.id_assets.id_profile.name_profile
    }, asset_items))

    assets = list(map(lambda item: {
        'id_asset_item': None,
        'id_asset': int(item.id_assets),
        'id_company': int(item.id_company.id_company),
        'asset_profile_id': int(item.id_profile.id_profile),
        'asset_profile_name': item.id_profile.name_profile
    }, assets))

    return Response(asset_items + assets)



def function_generic_find(request):
    kwargs = {
        'company_name': 'id_assets__id_company__company_name__contains',
        'name_profile': 'id_assets__id_profile__name_profile__contains',
        'code_ccee': 'id_assets__id_ccee_siga__code_ccee__contains',
        'show_balance': 'id_assets__show_balance__contains',
        'composition_name': 'id_energy_composition__composition_name__contains',
        'status': 'id_assets__status__contains'    
    }
    kwargs_order = {
        'company_name': 'id_company__company_name',
        'name_profile': 'id_profile__name_profile',
        'code_ccee': 'id_ccee_siga__code_ccee',
        'show_balance': '-show_balance',
        'composition_name': 'AssetsComposition_id_assets__id_energy_composition__composition_name',
        'status': 'status',

        '-company_name': '-id_company__company_name',
        '-name_profile': '-id_profile__name_profile',
        '-code_ccee': '-id_ccee_siga__code_ccee',
        '-show_balance': 'show_balance',
        '-composition_name': '-AssetsComposition_id_assets__id_energy_composition__composition_name',
        '-status': '-status'
    }

    ids = generic_queryset_filter(request, AssetsComposition, 'id_assets', **kwargs)
    if request.query_params.get('ordering') in kwargs_order:
        order_by = kwargs_order[request.query_params.get('ordering')]
    else:
        order_by = kwargs_order['company_name']
    assets_object = Assets.objects\
        .select_related('id_company').select_related('id_profile').select_related('id_submarket')\
        .select_related('id_ccee_siga').select_related('id_ccee_proinfa')\
          .prefetch_related('id_ccee_proinfa__id_ccee_SeasonalityProinfa').prefetch_related('id_ccee_proinfa__id_ccee_SeasonalityProinfa__id_seasonality')\
        .prefetch_related('AssetsComposition_id_assets').prefetch_related('AssetsComposition_id_assets__id_energy_composition')\
            .prefetch_related('assetitems_asset').prefetch_related('assetitems_asset__id_assets') \
        .prefetch_related('assetitems_asset__id_energy_composition').prefetch_related('assetitems_asset__id_company') \
        .filter(id_assets__in=ids).order_by(order_by)

    return assets_object

def function_format_response_find(request, data):
    observation_log = ""
    if 'observation_log' in request.data:
        observation_log = request.data['observation_log']  # pragma: no cover

    serializer_context = {
        'request': request,
        'observation_log': observation_log
    }
    serializer=[]

    for item in data:
        for item_Asse_Compo in item._prefetched_objects_cache['AssetsComposition_id_assets']:
            try:
                itemJson={
                    "id_assets_composition": item_Asse_Compo.id_assets_composition,
                    "id_assets": {
                        "id_assets": item.id_assets,
                        "id_company": {
                            "id_company": item.id_company_id if item.id_company else "",
                            "company_name": item.id_company.company_name if item.id_company else ""
                        },
                        "id_profile": {
                            "id_profile": item.id_profile_id if item.id_profile else "",
                            "name_profile": item.id_profile.name_profile if item.id_profile else "",
                            "status": item.id_profile.status if item.id_profile else ""
                        },
                        "id_submarket": {
                            'id_submarket': item.id_submarket_id if item.id_submarket else "", 
                            'description': item.id_submarket.description if item.id_submarket else "", 
                            'status': item.id_submarket.status if item.id_submarket else ""
                        },
                        "id_ccee_siga": {
                            "id_ccee": item.id_ccee_siga_id if item.id_ccee_siga else "",
                            "code_ccee": item.id_ccee_siga.code_ccee if item.id_ccee_siga else ""
                        },
                        "show_balance": item.show_balance,
                        "status": item.status
                    },
                    "id_energy_composition": {
                        "id_energy_composition": item_Asse_Compo.id_energy_composition_id if item_Asse_Compo.id_energy_composition else "", 
                        "composition_name": item_Asse_Compo.id_energy_composition.composition_name if item_Asse_Compo.id_energy_composition else ""
                    },
                    "status": item_Asse_Compo.status
                }
            except:
                itemJson = AssetsCompositionSerializerView(item_Asse_Compo, many=False, context=serializer_context).data
            
            proinfa_json=None
            array_seasonality=[]
            if item.id_ccee_proinfa:
                proinfa_json={
                    "id_ccee": item.id_ccee_proinfa_id,
                    "code_ccee": item.id_ccee_proinfa.code_ccee,
                    "type": item.id_ccee_proinfa.type,
                    "name_ccee": item.id_ccee_proinfa.name_ccee
                }
                for item_seaso in item.id_ccee_proinfa._prefetched_objects_cache['id_ccee_SeasonalityProinfa']:
                    array_seasonality.append(SeasonalityProinfaSerializerView(item_seaso, many=False, context=serializer_context).data)

            array_asset_items=[]
            for item_asset_items in item._prefetched_objects_cache['assetitems_asset']:
                array_asset_items.append(AssetItemsSerializer(item_asset_items, many=False, context=serializer_context).data)

            itemJson['id_assets']['id_ccee_proinfa']=proinfa_json
            itemJson['seasonality']=array_seasonality
            itemJson['asset_item']=array_asset_items
            serializer.append(itemJson)

    return serializer
