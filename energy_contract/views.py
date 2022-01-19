import collections
import json
import math
from datetime import datetime, timedelta, timezone
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db import transaction

from cliq_contract.views import get_pv
from cliq_contract.serializers import CliqContractSerializerView
from core.views import delete_file, generic_paginator, generic_log_search, generic_queryset_filter, generic_log_search_basic, \
    save_file, validates_data_used_file, alter_number
from core.attachment_utility import generic_data_csv_list, generic_csv, generic_pdf, generic_xls
from energy_contract.models import EnergyContract, Precification, Flexibilization, FlexibilizationType, Modulation, Seasonal, Guarantee, \
    ContractAttachment, EnergyProduct, Variable
from energy_contract.serializers import EnergyContractSerializer, ContractAttachmentSerializer, \
    EnergyProductSerializerView, EnergyContractSerializerView, ModulationSerializer, PrecificationSerializer, \
    GuaranteeSerializer, FlexibilizationSerializer, FlexibilizationTypeSerializer, SeasonalSerializer, VariableSerializerView, \
    EnergyContractSerializerBasicView, AgentsSerializerView, ProfileSerializerView
from agents.models import Agents
from profiles.models import Profile
from core.models import CceeDescription
from transfer_contract_priority.models import TransferContractPriority
from core.serializers import log, LogSerializer
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.translation import gettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend
from django.forms.models import model_to_dict
from locales.translates_function import translate_language_header, translate_language, translate_language_error, translate_language_log
from cliq_contract.models import CliqContract, SeasonalityCliq
from django.db.models import Q

from SmartEnergy.auth import check_module
import SmartEnergy.auth.permissions as permissions
import SmartEnergy.auth.modules as modules

from django.db import connection
from energy_contract.serializers import function_valid_contract_name

from assets.models import Assets
from assets.serializersViews import ProfileAssetsSerializerView
from asset_items.models import AssetItems
from global_variables.models import GlobalVariable

# validates if the contract already exists (if it exists returns which last id)
@api_view(['GET'])
@check_module(modules.energy_contract, [permissions.VIEW, permissions.EDITN1])
def valid_contract_name(request, name):  # if no id returns 0
    if request.query_params.get('id_contract'): #Checks whether the existing contract has been changed
        try:
            if EnergyContract.objects.get( pk=request.query_params.get('id_contract') ).contract_name == name:
                return Response({'validate': "False"}, status=status.HTTP_200_OK)
        except EnergyContract.DoesNotExist:
            pass
    valid_name, message_function = function_valid_contract_name(request, name)
    if valid_name:
        return Response(message_function, status=status.HTTP_200_OK)
    else:
        return Response(message_function, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@check_module(modules.energy_contract, [permissions.VIEW, permissions.EDITN1])
def show_variable(request):
    variable = Variable.objects.filter(type_id_variable=1).order_by('name')
    teste = VariableSerializerView(variable, many=True, context=request)
    return Response(teste.data)


# lists all energy_products
@api_view(['GET'])
@check_module(modules.energy_contract, [permissions.VIEW, permissions.EDITN1])
def get_energy_product(request):
    """
        get list energy_product
    """

    observation_log = ""
    if 'observation_log' in request.data:
        observation_log = request.data['observation_log']

    serializer_context = {
        'request': request,
        'observation_log': observation_log
    }
    try:
        energy_products = EnergyProduct.objects.all().order_by('description')
        serializer = EnergyProductSerializerView(energy_products, many=True, context=serializer_context)
        return Response(serializer.data)
    except EnergyProduct.DoesNotExist:  # pragma: no cover
        # Insert security exception
        return Response(status=status.HTTP_404_NOT_FOUND)

def _is_valid_signing_data(contract):
    # signing_data is locked for transfer except agent company is represented
    
    if (contract.get('id_buyer_profile') and contract.get('id_seller_profile')):
        if Profile.objects.get(pk=contract.get('id_buyer_profile')).id_agents.id_company.type == 'R' and\
            Profile.objects.get(pk=contract.get('id_seller_profile')).id_agents.id_company.type == 'R':        
            return contract.get('signing_data')
    
    
    if contract.get('modality').upper() == 'TRANSFERENCIA':
        return None    

    if contract.get('contract_status') == 'AS':
        return contract.get('signing_data')

    return None
    

@api_view(['GET'])
@check_module(modules.energy_contract, [permissions.VIEW, permissions.EDITN1])
def session_energy_contract_get(request):
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
        kwargs = {'modality': 'modality__contains',
                  'sap_contract': 'sap_contract__contains',
                  'type': 'type__contains',
                  'contract_name': 'contract_name__contains',
                  'buyer_profile': 'id_buyer_profile__name_profile__contains',
                  'seller_profile': 'id_seller_profile__name_profile__contains',
                  'buyer_agents': 'id_buyer_agents__vale_name_agent__contains',
                  'seller_agents': 'id_seller_agents__vale_name_agent__contains', 'status': 'status__contains'
                  }

        kwargs_order = {'modality': 'modality',
                        'sap_contract': 'sap_contract',
                        'type': 'type',
                        'contract_name': 'contract_name',
                        'buyer_profile': 'id_buyer_profile__name_profile',
                        'seller_profile': 'id_seller_profile__name_profile',
                        'buyer_agents': 'id_buyer_agents__vale_name_agent',
                        'seller_agents': 'id_seller_agents__vale_name_agent',
                        'status': 'status',

                        '-modality': '-modality',
                        '-sap_contract': '-sap_contract',
                        '-type': '-type',
                        '-contract_name': '-contract_name',
                        '-buyer_profile': '-id_buyer_profile__name_profile',
                        '-seller_profile': '-id_seller_profile__name_profile',
                        '-buyer_agents': '-id_buyer_agents__vale_name_agent',
                        '-seller_agents': '-id_seller_agents__vale_name_agent', '-status': '-status'
                        }

        ids = generic_queryset_filter(request, EnergyContract, 'id_contract', **kwargs)
        if request.query_params.get('ordering') in kwargs_order:
            order_by = kwargs_order[request.query_params.get('ordering')]
        else:
            order_by = kwargs_order['modality']
        energy = EnergyContract.objects.exclude(status='T').filter(id_contract__in=ids).order_by(order_by)
        data, page_count, page_next, page_previous = generic_paginator(request, energy)
        serializer = EnergyContractSerializerView(data, many=True, context=serializer_context)
        response = collections.OrderedDict([
            ('count', page_count),
            ('next', page_next),
            ('previous', page_previous),
            ('results', serializer.data)
        ])
        return Response(response)

@api_view(['POST'])
@check_module(modules.energy_contract, [permissions.EDITN1])
def session_energy_contract_post(request):
    """
       create a new energy contract
    """
    observation_log = ""
    if 'observation_log' in request.data:
        observation_log = request.data['observation_log']

    serializer_context = {
        'request': request,
        'observation_log': observation_log
    }

    if request.method == 'POST':
        # valid signing_data
        if request.data['contract_status'] == "AS" and not request.data['signing_data']:
            return Response({'error': translate_language_error('error_signing_null', request) }, status=status.HTTP_400_BAD_REQUEST)
        else:
            request.data['signing_data'] = _is_valid_signing_data(request.data)

        try:
            precif_data = request.data.pop('precif_energy_contract')
            if not bool(precif_data):  # evaluates if dict is empty
                precif_data = None
        except KeyError:
            precif_data = None

        try:
            flexib_data = request.data.pop('flexib_energy_contract')
            if not bool(flexib_data):  # evaluates if dict is empty
                flexib_data = None
        except KeyError:
            flexib_data = None

        try:
            modul_data = request.data.pop('modulation_energy_contract')
            if not bool(modul_data):  # evaluates if dict is empty
                modul_data = None
        except KeyError:
            modul_data = None

        try:
            season_data = request.data.pop('season_energy_contract')
            if not bool(season_data):  # evaluates if dict is empty
                season_data = None
        except KeyError:
            season_data = None

        try:
            guaran_data = request.data.pop('guaran_energy_contract')
            if not bool(guaran_data):  # evaluates if dict is empty
                guaran_data = None
        except KeyError:
            guaran_data = None

        serializer = EnergyContractSerializer(data=request.data, context=serializer_context)
        if serializer.is_valid():
            energy = serializer.save()

            if precif_data:
                precif_data["id_contract"] = energy.pk
                precif_serializer = PrecificationSerializer(data=precif_data, context=serializer_context)
                if precif_serializer.is_valid():
                    precif_serializer.save()
                else:
                    return Response(precif_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            if flexib_data:
                flexib_data["id_contract"] = energy.pk
                flexib_serializer = FlexibilizationSerializer(data=flexib_data, context=serializer_context)
                if flexib_serializer.is_valid():
                    flexib_serializer.save()
                else:
                    return Response(flexib_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            if modul_data:
                modul_data["id_contract"] = energy.pk
                modul_serializer = ModulationSerializer(data=modul_data, context=serializer_context)
                if modul_serializer.is_valid():
                    modul_serializer.save()
                else:
                    return Response(modul_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            if season_data:
                season_data["id_contract"] = energy.pk
                season_serializer = SeasonalSerializer(data=season_data, context=serializer_context)
                if season_serializer.is_valid():
                    season_serializer.save()
                else:
                    return Response(season_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            if guaran_data:
                guaran_data["id_contract"] = energy.pk
                guaran_serializer = GuaranteeSerializer(data=guaran_data, context=serializer_context)
                if guaran_serializer.is_valid():
                    guaran_serializer.save()
                else:
                    return Response(guaran_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            serializerReturn = EnergyContractSerializerView(EnergyContract.objects.get(pk=energy.pk),
                                                            context=serializer_context)
            return Response(serializerReturn.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT'])
@check_module(modules.energy_contract, [permissions.EDITN1])
def session_energy_contract_put(request, pk):
    """
        Retrieve, update or delete a specific energy contract.
    """
    observation_log = ""
    if 'observation_log' in request.data:
        observation_log = request.data['observation_log']

    serializer_context = {
        'request': request,
        'observation_log': observation_log
    }

    try:
        energy = EnergyContract.objects.get(pk=pk)
    except EnergyContract.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'PUT':
        # valid signing_data
        if request.data['contract_status'] == "AS" and not request.data['signing_data']:
            return Response({'error': translate_language_error('error_signing_null', request) }, status=status.HTTP_400_BAD_REQUEST)
        else:
            request.data['signing_data'] = _is_valid_signing_data(request.data)

        try:
            precif_data = request.data.pop('precif_energy_contract')
            if not bool(precif_data):  # evaluates if dict is empty
                precif_data = None
        except KeyError:
            precif_data = None

        try:
            flexib_data = request.data.pop('flexib_energy_contract')
            if not bool(flexib_data):  # evaluates if dict is empty
                flexib_data = None
        except KeyError:
            flexib_data = None

        try:
            modul_data = request.data.pop('modulation_energy_contract')
            if not bool(modul_data):  # evaluates if dict is empty
                modul_data = None
        except KeyError:
            modul_data = None

        try:
            season_data = request.data.pop('season_energy_contract')
            if not bool(season_data):  # evaluates if dict is empty
                season_data = None
        except KeyError:
            season_data = None

        try:
            guaran_data = request.data.pop('guaran_energy_contract')
            if not bool(guaran_data):  # evaluates if dict is empty
                guaran_data = None
        except KeyError:
            guaran_data = None

        serializer = EnergyContractSerializer(energy, data=request.data, context=serializer_context)
        if serializer.is_valid():
            serializer.save()

            if precif_data:
                precif_data["id_contract"] = energy.pk
                try:
                    precif = Precification.objects.get(id_contract_id=energy.pk)
                    precif_serializer = PrecificationSerializer(precif, data=precif_data, context=serializer_context)
                except Precification.DoesNotExist:
                    precif_serializer = PrecificationSerializer(data=precif_data, context=serializer_context)
                finally:
                    if precif_serializer.is_valid():
                        precif_serializer.save()
                    else:
                        return Response(precif_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            else:
                try:
                    precif = Precification.objects.get(id_contract_id=energy.pk)
                    log(Precification, precif.id_contract, precif, {}, request.user, \
                        observation_log, action="DELETE")
                    precif.delete()
                except Precification.DoesNotExist:
                    pass

            if flexib_data:
                flexib_data["id_contract"] = energy.pk
                try:
                    flexib = Flexibilization.objects.get(id_contract_id=energy.pk)
                    flexib_serializer = FlexibilizationSerializer(flexib, data=flexib_data, context=serializer_context)
                except Flexibilization.DoesNotExist:
                    flexib_serializer = FlexibilizationSerializer(data=flexib_data, context=serializer_context)
                finally:
                    if flexib_serializer.is_valid():
                        flexib_serializer.save()
                    else:
                        return Response(flexib_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            else:
                try:
                    flexib = Flexibilization.objects.get(id_contract_id=energy.pk)
                    log(Flexibilization, flexib.id_contract, flexib, {}, request.user, \
                        observation_log, action="DELETE")
                    flexib.delete()
                except Flexibilization.DoesNotExist:
                    pass

            if modul_data:
                modul_data["id_contract"] = energy.pk
                try:
                    modul = Modulation.objects.get(id_contract_id=energy.pk)
                    modul_serializer = ModulationSerializer(modul, data=modul_data, context=serializer_context)
                except Modulation.DoesNotExist:
                    modul_serializer = ModulationSerializer(data=modul_data, context=serializer_context)
                finally:
                    if modul_serializer.is_valid():
                        modul_serializer.save()
                    else:
                        return Response(modul_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            else:
                try:
                    modul = Modulation.objects.get(id_contract_id=energy.pk)
                    log(Modulation, modul.id_contract, modul, {}, request.user, \
                        observation_log, action="DELETE")
                    modul.delete()
                except Modulation.DoesNotExist:
                    pass

            if season_data:
                season_data["id_contract"] = energy.pk
                try:
                    season = Seasonal.objects.get(id_contract_id=energy.pk)
                    season_serializer = SeasonalSerializer(season, data=season_data, context=serializer_context)
                except Seasonal.DoesNotExist:
                    season_serializer = SeasonalSerializer(data=season_data, context=serializer_context)
                finally:
                    if season_serializer.is_valid():
                        season_serializer.save()
                    else:
                        return Response(season_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            else:
                try:
                    season = Seasonal.objects.get(id_contract_id=energy.pk)
                    log(Seasonal, season.id_contract, season, {}, request.user, \
                        observation_log, action="DELETE")
                    season.delete()
                except Seasonal.DoesNotExist:
                    pass

            if guaran_data:
                guaran_data["id_contract"] = energy.pk
                try:
                    guaran = Guarantee.objects.get(id_contract_id=energy.pk)
                    guaran_serializer = GuaranteeSerializer(guaran, data=guaran_data, context=serializer_context)
                except Guarantee.DoesNotExist:
                    guaran_serializer = GuaranteeSerializer(data=guaran_data, context=serializer_context)
                finally:
                    if guaran_serializer.is_valid():
                        guaran_serializer.save()
                    else:
                        return Response(guaran_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            else:
                try:
                    guaran = Guarantee.objects.get(id_contract_id=energy.pk)
                    log(Guarantee, guaran.id_contract, guaran, {}, request.user, \
                        observation_log, action="DELETE")
                    guaran.delete()
                except Guarantee.DoesNotExist:
                    pass

            energy = EnergyContract.objects.get(pk=pk)
            serializer = EnergyContractSerializerView(energy, context=serializer_context)
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@check_module(modules.energy_contract, [permissions.VIEW, permissions.EDITN1])
def session_energy_contract_get_detail(request, pk):
    """
        specific energy contract.
    """
    observation_log = ""
    if 'observation_log' in request.data:
        observation_log = request.data['observation_log']

    serializer_context = {
        'request': request,
        'observation_log': observation_log
    }

    try:
        energy = EnergyContract.objects \
            .select_related('id_buyer_agents').select_related('id_seller_agents')\
            .select_related('id_buyer_profile').select_related('id_seller_profile')\
            .select_related('id_energy_product')\
            .prefetch_related('precif_energy_contract').prefetch_related('flexib_energy_contract')\
            .prefetch_related('modul_energy_contract').prefetch_related('season_energy_contract')\
            .prefetch_related('guaran_energy_contract')\
            .get(pk=pk)
    except EnergyContract.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        
        try:
            serializer=EnergyContractSerializerBasicView(energy, many=False, context=serializer_context).data

            buyer_agents_detail=AgentsSerializerView(energy.id_buyer_agents, many=False, context=serializer_context).data if energy.id_buyer_agents else ""
            seller_agents_detail=AgentsSerializerView(energy.id_seller_agents, many=False, context=serializer_context).data if energy.id_seller_agents else ""
            serializer['buyer_agents_detail']=buyer_agents_detail
            serializer['seller_agents_detail']=seller_agents_detail

            buyer_profile_detail=ProfileSerializerView(energy.id_buyer_profile, many=False, context=serializer_context).data if energy.id_buyer_profile else ""
            seller_profile_detail=ProfileSerializerView(energy.id_seller_profile, many=False, context=serializer_context).data if energy.id_seller_profile else ""
            serializer['buyer_profile_detail']=buyer_profile_detail
            serializer['seller_profile_detail']=seller_profile_detail

            precif_energy_contract=PrecificationSerializer(energy.precif_energy_contract, many=False, context=serializer_context).data if hasattr(energy, 'precif_energy_contract') else ""
            flexib_energy_contract=FlexibilizationSerializer(energy.flexib_energy_contract, many=False, context=serializer_context).data if hasattr(energy, 'flexib_energy_contract') else ""
            modulation_energy_contract=ModulationSerializer(energy.modul_energy_contract, many=False, context=serializer_context).data  if hasattr(energy, 'modul_energy_contract') else ""
            season_energy_contract=SeasonalSerializer(energy.season_energy_contract, many=False, context=serializer_context).data  if hasattr(energy, 'season_energy_contract') else ""
            guaran_energy_contract=GuaranteeSerializer(energy.guaran_energy_contract, many=False, context=serializer_context).data  if hasattr(energy, 'guaran_energy_contract') else ""
            product=EnergyProductSerializerView(energy.id_energy_product, many=False, context=serializer_context).data  if energy.id_energy_product else ""

            serializer['precif_energy_contract']=precif_energy_contract
            serializer['flexib_energy_contract']=flexib_energy_contract
            serializer['modulation_energy_contract']=modulation_energy_contract
            serializer['season_energy_contract']=season_energy_contract
            serializer['guaran_energy_contract']=guaran_energy_contract
            serializer['product']=product

        except :
            serializer = EnergyContractSerializerView(energy, context=serializer_context).data
        kwargs = {'id_contract': energy.id_contract}
        current_price = get_pv(kwargs)
        kwargs = serializer
        kwargs['current_price'] = current_price
        serializer = collections.OrderedDict(kwargs)
        return Response(serializer)



@api_view(['GET'])
@check_module(modules.energy_contract, [permissions.VIEW, permissions.EDITN1])
def session_energy_contract_attachment_get(request):
    """
       List all energy contract attachments 
    """
    observation_log = ""
    if 'observation_log' in request.data:
        observation_log = request.data['observation_log']

    serializer_context = {
        'request': request,
        'observation_log': observation_log
    }

    if request.method == 'GET':
        kwargs = {'contract_name': 'id_contract__contract_name__contains',
                  'id_contract': 'id_contract_id', 'name': 'name__contains',
                  'revision': 'revision__contains', 'comments': 'comments__contains',
                  'path': 'path__contains'}

        kwargs_order = {'contract_name': 'id_contract__contract_name',
                        'name': 'name', 'revision': 'revision',
                        'comments': 'comments', 'path': 'path',
                        '-contract_name': '-id_contract__contract_name',
                        '-name': '-name', '-revision': '-revision',
                        '-comments': '-comments', '-path': '-path'}

        ids = generic_queryset_filter(request, ContractAttachment, 'id_contract', **kwargs)
        if request.query_params.get('ordering') in kwargs_order:
            order_by = kwargs_order[request.query_params.get('ordering')]
        else:
            order_by = kwargs_order['-revision']

        attachments = ContractAttachment.objects.filter(id_contract__in=ids).order_by(order_by)
        data, page_count, page_next, page_previous = generic_paginator(request, attachments)
        serializer = ContractAttachmentSerializer(data, many=True, context=serializer_context)
        response = collections.OrderedDict([
            ('count', page_count),
            ('next', page_next),
            ('previous', page_previous),
            ('results', serializer.data)
        ])
        return Response(response)

@api_view(['POST'])
@check_module(modules.energy_contract, [permissions.EDITN1])
def session_energy_contract_attachment_post(request):
    """
       creates a new one
    """
    observation_log = ""
    if 'observation_log' in request.data:
        observation_log = request.data['observation_log']

    serializer_context = {
        'request': request,
        'observation_log': observation_log
    }

    if request.method == 'POST':
        if 'path' in request.FILES:
            try:
                file = request.FILES['path']
                request.data['path'] = save_file(file)
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        serializer = ContractAttachmentSerializer(data=request.data, context=serializer_context)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT'])
@check_module(modules.energy_contract, [permissions.EDITN1])
def session_energy_contract_attachment_put(request, pk):
    """
        Retrieve, update or delete a specific energy contract.
    """
    observation_log = ""
    if 'observation_log' in request.data:
        observation_log = request.data['observation_log']

    serializer_context = {
        'request': request,
        'observation_log': observation_log
    }

    try:
        attachments = ContractAttachment.objects.get(pk=pk)
    except ContractAttachment.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'PUT':
        if 'path' in request.FILES:
            try:
                file = request.FILES['path']
                attachment = ContractAttachment.objects.get(pk=request.data['id_attachment'])
                path = attachment.path
                delete_file(path)
                request.data['path'] = save_file(file)
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        serializer = ContractAttachmentSerializer(attachments, data=request.data, context=serializer_context)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_304_NOT_MODIFIED)

@api_view(['GET'])
@check_module(modules.energy_contract, [permissions.VIEW, permissions.EDITN1])
def session_energy_contract_attachment_get_detail(request, pk):
    """
        specific energy contract.
    """
    observation_log = ""
    if 'observation_log' in request.data:
        observation_log = request.data['observation_log']

    serializer_context = {
        'request': request,
        'observation_log': observation_log
    }

    try:
        attachments = ContractAttachment.objects.get(pk=pk)
    except ContractAttachment.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = ContractAttachmentSerializer(attachments, context=serializer_context)
        return Response(serializer.data)


@api_view(['GET'])
@check_module(modules.energy_contract, [permissions.VIEW, permissions.EDITN1])
def session_log_basic_energy_contract(request, pk):
    """
           List all logs about energy contract
    """
    kwargs = {'core': EnergyContract, 'core_pk': 'id_contract', 'core+': [],
              'child': [Precification, Flexibilization, Modulation, Seasonal, Guarantee]}
    kwargsAux = generic_log_search_basic(generic_log_search(pk, **kwargs))
    log = {'logs': kwargsAux}

    id_array = []
    # Agents
    agents_array = []
    for items in kwargsAux:
        if items['ENERGY_CONTRACT']:
            if items['ENERGY_CONTRACT']['new_value']:
                if items['ENERGY_CONTRACT']['new_value']['id_buyer_agents']:
                    a = items['ENERGY_CONTRACT']['new_value']['id_buyer_agents']
                    if 'value' in a:
                        id_num = a['value']
                    else:
                        id_num = a
                    if id_num not in id_array and id_num:
                        id_array.append(id_num)
                        agents_array.append(
                            {'id_agents': id_num, 'name_agent': Agents.objects.filter(pk=id_num)[0].vale_name_agent})

                if items['ENERGY_CONTRACT']['new_value']['id_seller_agents']:
                    a = items['ENERGY_CONTRACT']['new_value']['id_seller_agents']
                    if 'value' in a:
                        id_num = a['value']
                    else:
                        id_num = a
                    if id_num not in id_array and id_num:
                        id_array.append(id_num)
                        agents_array.append(
                            {'id_agents': id_num, 'name_agent': Agents.objects.filter(pk=id_num)[0].vale_name_agent})

    # Profile
    profile_array = []
    id_array.clear()
    for items in kwargsAux:
        if items['ENERGY_CONTRACT']:
            if items['ENERGY_CONTRACT']['new_value']:
                if items['ENERGY_CONTRACT']['new_value']['id_buyer_profile']:
                    a = items['ENERGY_CONTRACT']['new_value']['id_buyer_profile']
                    if 'value' in a:
                        id_num = a['value']
                    else:
                        id_num = a
                    if id_num not in id_array:
                        id_array.append(id_num)
                        profile_array.append(
                            {'id_profile': id_num, 'name_profile': Profile.objects.get(pk=id_num).name_profile})

                if items['ENERGY_CONTRACT']['new_value']['id_seller_profile']:
                    a = items['ENERGY_CONTRACT']['new_value']['id_seller_profile']
                    if 'value' in a:
                        id_num = a['value']
                    else:
                        id_num = a
                    if id_num not in id_array:
                        id_array.append(id_num)
                        profile_array.append(
                            {'id_profile': id_num, 'name_profile': Profile.objects.get(pk=id_num).name_profile})

    log['statics_relateds'] = {'agents': agents_array, 'profile': profile_array}

    #Traduction
    for items in log['logs']:
        if items['PRECIFICATION']:  # PRECIFICATION
            if items['PRECIFICATION']['new_value']:
                if items['PRECIFICATION']['new_value'].get('id_variable'):
                    a = items['PRECIFICATION']['new_value']['id_variable']
                    if 'value' in a:
                        if a['value'] == "1":
                            items['PRECIFICATION']['new_value']['id_variable']['value'] = "IGP-M"
                        elif a['value'] == "2":
                            items['PRECIFICATION']['new_value']['id_variable']['value'] = "IPCA"
                    else:
                        if a == "1":
                            items['PRECIFICATION']['new_value']['id_variable'] = "IGP-M"
                        elif a == "2":
                            items['PRECIFICATION']['new_value']['id_variable'] = "IPCA"

            if items['PRECIFICATION']['old_value']:
                if items['PRECIFICATION']['old_value'].get('id_variable'):
                    a=items['PRECIFICATION']['old_value']['id_variable']
                    if a=="1": items['PRECIFICATION']['old_value']['id_variable']= "IGP-M" 
                    elif a=="2": items['PRECIFICATION']['old_value']['id_variable']="IPCA"

    return Response(log)

@api_view(['GET'])
@check_module(modules.energy_contract, [permissions.VIEW, permissions.EDITN1])
def session_energy_contract_file(request):
    if not (request.query_params.get('format_file', None) is None):
        format_file = request.query_params.get('format_file', None)
    else:
        return Response({'error': translate_language_error('error_format_file_csv_or_pdf', request) }, status=status.HTTP_400_BAD_REQUEST)

    energy_contract = function_find_objects(request)
    serializer = function_find_format(energy_contract, request, True)
    
    for item_serializer in serializer:
        kwargs=item_serializer['cliq_contract']
        cliq_json_formated = generic_data_csv_list(kwargs, ['seasonality_cliq_details'])
        item_serializer['cliq_contract']=cliq_json_formated
        
    payload = serializer
    payload = json.dumps(payload, indent=4, default=str).encode('utf-8')
    rest = json.loads(payload)

    # let empty to use mapping (original) names: header = {}
    # must be in the same order of mapping
    header = {
        'modality': 'field_modality', 
        'sap_contract': 'field_sap', 
        'type': 'field_contract_type', 
        'seller_vale_name_agent': 'field_seller_agents', 
        'buyer_vale_name_agent': 'field_buyer_agents', 
        'seller_name_profile': 'field_seller_profile', 
        'buyer_name_profile': 'field_buyer_profile', 
        'start_supply': 'field_start_supply', 
        'end_supply': 'field_end_supply', 
        'volume_mwm': 'field_volume_mwm', 
        'volume_mwh': 'field_volume_mwh', 
        'product_description': 'field_energy_product', 
        'contract_name': 'field_contract_name', 
        'contract_status': 'field_contract_status', 
        'signing_data': 'field_signing_date',
        'market': 'field_contract_market',
        'base_price_mwh': 'field_base_mwh', 
        'base_price_date': 'field_base_date', 
        'base_contract_value': 'field_base_value', 
        'birthday_date': 'field_birthday_date', 
        'id_variable': 'field_price_index', 
        'active_price_mwh': 'field_active_mwh', 
        'retusd': 'field_retusd', 

        'flexibility_type': 'field_flexibility_type',
        'min_flexibility_pu': 'field_min_flexibility',
        'max_flexibility_pu': 'field_max_flexibility',
        'proinfa_flexibility': 'field_proinfa_flexibility',
        'modulation_type': 'field_modulation_type',
        'min_modulation_pu': 'field_min_modulation',
        'max_modulation_pu': 'field_max_modulation',
        'type_seasonality': 'field_seasonalization_type',
        'season_min_pu': 'field_min_seasonalization',
        'season_max_pu': 'field_max_seasonalization',
        'month_hour': 'field_months',
        'hours': 'field_hours',
        'guaranteed_value': 'field_guaranteed_value',
        'emission_date': 'field_issuance_date',
        'effective_date': 'field_effective_date',
        #cliq
        'cliq_contract': 'field_cliq_contract',
        'ccee_type_contract': 'field_ccee_type_contract',
        'transaction_type': 'field_transaction_type',
        'flexibility': 'field_flexibility_title',
        'id_vendor_profile__name_profile': 'field_seller_profile',
        'id_buyer_profile__name_profile': 'field_buyer_profile',
        'mwm_volume': 'field_mwm_volume_title',
        'contractual_loss': 'field_contractual_loss_title',
        'Buyer_Consumer': 'field_buyer_consumer',
        'id_submarket__description': 'field_submarket',
        'submarket': 'field_contract_submarket',
        'status': 'field_cliq_status',

        'year':'field_year',
        'measure_unity':'field_measureUnity',
        'january':'field_january',
        'february':'field_february',
        'march':'field_march',
        'april':'field_april',
        'may':'field_may',
        'june':'field_june',
        'july':'field_july',
        'august':'field_august',
        'september':'field_september',
        'october':'field_october',
        'november':'field_november',
        'december':'field_december',
    }
    header = translate_language_header(header, request)
    mapping = [
        'modality', 
        'sap_contract', 
        'type', 
        'seller_vale_name_agent', 
        'buyer_vale_name_agent',
        'seller_name_profile',
        'buyer_name_profile', 
        'start_supply', 
        'end_supply', 
        'volume_mwm', 
        'volume_mwh', 
        'product_description',
        'contract_name', 
        'contract_status', 
        'signing_data',
        'market',
        'base_price_mwh', 
        'base_price_date', 
        'base_contract_value', 
        'birthday_date', 'id_variable',
        'active_price_mwh', 
        'retusd',
        'flexibility_type', 
        'min_flexibility_pu', 
        'max_flexibility_pu', 
        'proinfa_flexibility',
        'modulation_type', 
        'min_modulation_pu', 
        'max_modulation_pu',
        'type_seasonality', 
        'season_min_pu', 
        'season_max_pu',
        'month_hour', 
        'hours', 
        'guaranteed_value', 
        'emission_date', 
        'effective_date',
        
        #Cliq
        'cliq_contract',
        'ccee_type_contract',
        'transaction_type',
        'flexibility',
        'id_vendor_profile__name_profile',
        'id_buyer_profile__name_profile',
        "mwm_volume",
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

    rest = generic_data_csv_list(rest, ['cliq_contract'])
    rest_data = []

    assets_obj = Assets.objects.filter(cliq_asset__isnull=False).select_related('id_ccee_siga').select_related('id_company')
    assetsItems_obj = AssetItems.objects.filter(cliq_items__isnull=False).select_related('id_company')

    type_format_number=2 if format_file=='pdf' else 1
    for index in range(len(rest)):
        kwargs = rest[index]
        kwargs_cliq = rest[index]['cliq_contract']
        date_start_supply = datetime.strptime(kwargs['start_supply'], '%d/%m/%Y').date()
        date_end_supply = datetime.strptime(kwargs['end_supply'], '%d/%m/%Y').date()
        try:
            value_volume_mwm = float(kwargs['volume_mwm'])
        except:
            value_volume_mwm = 0
        try:
            value_base_price_mwh = float(kwargs['precif_energy_contract']['base_price_mwh'])
        except:
            value_base_price_mwh = 0
        try:
            value_month_hour = int(kwargs['guaran_energy_contract']['month_hour'])
        except:
            value_month_hour = 0
        
        value_base_contract_value=((date_end_supply - date_start_supply).days + 1) * 24 * value_volume_mwm * value_base_price_mwh 
        if type_format_number==2: #If file type is pdf, exchange . for ,
            retorno = "%.4f" %value_base_contract_value
            value_base_contract_value=alter_number(retorno)
        
        new = {
            'modality': translate_language(kwargs['modality'], request) if kwargs['modality'] else "",
            'sap_contract': validates_data_used_file(kwargs, ['sap_contract'], type_format_number), #number
            'type': translate_language(("field_csv_"+kwargs['type']), request) if kwargs['type'] else "",
            'start_supply': validates_data_used_file(kwargs, ['start_supply'], 0),
            'end_supply': validates_data_used_file(kwargs, ['end_supply'], 0),
            'volume_mwm': validates_data_used_file(kwargs, ['volume_mwm'], type_format_number, 6), #number with 6 decimal places
            'volume_mwh': validates_data_used_file(kwargs, ['volume_mwh'], type_format_number), #number
            'product_description': translate_language("energy_product_"+validates_data_used_file(kwargs, ['product', 'id_energy_product'], 0), request),
            'contract_name': validates_data_used_file(kwargs, ['contract_name'], 0),
            'contract_status': translate_language(("field_csv_contract_"+validates_data_used_file(kwargs, ['contract_status'], 0)), request ),
            'signing_data': validates_data_used_file(kwargs, ['signing_data'], 0),                        
            'market': translate_language("field_contract_market_"+validates_data_used_file(kwargs, ['market'], 0), request),

            'seller_name_profile': validates_data_used_file(kwargs, ['seller_profile_detail', 'name_profile'], 0),
            'buyer_name_profile': validates_data_used_file(kwargs, ['buyer_profile_detail', 'name_profile'], 0),

            'seller_vale_name_agent': validates_data_used_file(kwargs, ['seller_agents_detail', 'vale_name_agent'], 0),
            'buyer_vale_name_agent': validates_data_used_file(kwargs, ['buyer_agents_detail', 'vale_name_agent'], 0),

            'base_price_date': validates_data_used_file(kwargs, ['precif_energy_contract', 'base_price_date'], 0),
            'birthday_date': validates_data_used_file(kwargs, ['precif_energy_contract', 'birthday_date'], 0),
            'base_price_mwh': validates_data_used_file(kwargs, ['precif_energy_contract', 'base_price_mwh'], type_format_number), #number
            'active_price_mwh': validates_data_used_file(kwargs, ['precif_energy_contract', 'active_price_mwh'], type_format_number), #number
            'id_variable': translate_language("price_index_"+( validates_data_used_file(kwargs, ['precif_energy_contract', 'id_variable'], 0) ), request),
            'retusd': validates_data_used_file(kwargs, ['precif_energy_contract', 'retusd'], type_format_number), #number
            'base_contract_value': value_base_contract_value,

            'flexibility_type': translate_language(validates_data_used_file(kwargs, ['flexib_energy_contract', 'flexibility_type'], 0), request),
            'proinfa_flexibility': translate_language("field_response_"+validates_data_used_file(kwargs, ['flexib_energy_contract', 'proinfa_flexibility'], 0), request),
            'min_flexibility_pu': validates_data_used_file(kwargs, ['flexib_energy_contract', 'min_flexibility_pu'], type_format_number), #number
            'max_flexibility_pu': validates_data_used_file(kwargs, ['flexib_energy_contract', 'max_flexibility_pu'], type_format_number), #number

            'modulation_type': translate_language(validates_data_used_file(kwargs, ['modulation_energy_contract', 'modulation_type'],0), request),
            'min_modulation_pu': validates_data_used_file(kwargs, ['modulation_energy_contract', 'min_modulation_pu'], type_format_number), #number
            'max_modulation_pu': validates_data_used_file(kwargs, ['modulation_energy_contract', 'max_modulation_pu'], type_format_number), #number

            'type_seasonality': translate_language(validates_data_used_file(kwargs, ['season_energy_contract', 'type_seasonality'], 0), request),
            'season_min_pu': validates_data_used_file(kwargs, ['season_energy_contract', 'season_min_pu'], type_format_number), #number
            'season_max_pu': validates_data_used_file(kwargs, ['season_energy_contract', 'season_max_pu'], type_format_number), #number

            'month_hour': validates_data_used_file(kwargs, ['guaran_energy_contract', 'month_hour'], type_format_number), #number
            'hours': (24 * 30 * value_month_hour),
            'guaranteed_value': validates_data_used_file(kwargs, ['guaran_energy_contract', 'guaranteed_value'], type_format_number), #number
            'emission_date': validates_data_used_file(kwargs, ['guaran_energy_contract', 'emission_date'], 0),
            'effective_date': validates_data_used_file(kwargs, ['guaran_energy_contract', 'effective_date'], 0),

            #CLIQ
            'Buyer_Consumer': "",
            'cliq_contract': validates_data_used_file(kwargs_cliq, ['cliq_contract'], 0),
            'ccee_type_contract': validates_data_used_file(kwargs_cliq, ['ccee_type_contract'], 0),
            'transaction_type': translate_language(validates_data_used_file(kwargs_cliq, ['transaction_type'], 0), request),
            'flexibility': translate_language(validates_data_used_file(kwargs_cliq, ['flexibility'], 0), request),
            'id_vendor_profile__name_profile': validates_data_used_file(kwargs_cliq, ['id_vendor_profile.name_profile'], 0),
            'id_buyer_profile__name_profile': validates_data_used_file(kwargs_cliq, ['id_buyer_profile.name_profile'], 0),
            'mwm_volume': validates_data_used_file(kwargs_cliq, ['mwm_volume'], type_format_number),
            'contractual_loss': validates_data_used_file(kwargs_cliq, ['contractual_loss'], type_format_number), #number
            'id_submarket__description': validates_data_used_file(kwargs_cliq, ['id_submarket.description'], 0),
            'submarket': "",
            'status': translate_language("field_status_"+( validates_data_used_file(kwargs_cliq, ['status'],0) ), request),

            'year': "",
            'measure_unity': "",
            'january': "",
            'february': "",
            'march': "",
            'april': "",
            'may': "",
            'june': "",
            'july': "",
            'august': "",
            'september': "",
            'october': "",
            'november': "",
            'december': "",
        }

        if kwargs_cliq:
            new['submarket'] = translate_language("field_contract_market_"+validates_data_used_file(kwargs_cliq, ['submarket'], 0), request)
            if not 'id_buyer_assets' in kwargs_cliq:
                for asset in assets_obj:
                    if str(kwargs_cliq['id_buyer_assets.id_assets'])==str(asset.pk):
                        new['Buyer_Consumer'] = translate_language('field_Assets', request)+": " + str(asset.id_ccee_siga.code_ccee) + " - " \
                                                + asset.id_company.company_name
                        break

            elif not 'id_buyer_asset_items' in kwargs_cliq:
                for asset_item in assetsItems_obj:
                    if str(kwargs_cliq['id_buyer_asset_items.id_asset_items'])==str(asset_item.pk):
                        new['Buyer_Consumer'] = translate_language('field_Asset_items', request)+": "  + str(asset_item.id_asset_items)  + " - " \
                                                + asset_item.id_company.company_name
                        break

            if ('seasonality_cliq_details.id_seasonality_cliq' in kwargs_cliq) and (not math.isnan(kwargs_cliq['seasonality_cliq_details.id_seasonality_cliq'])):
                new['year']= validates_data_used_file(kwargs_cliq, ['seasonality_cliq_details.seasonality_detail.year'], 0) #number
                new['measure_unity']= validates_data_used_file(kwargs_cliq, ['seasonality_cliq_details.seasonality_detail.measure_unity'], 0)
                new['january']= validates_data_used_file(kwargs_cliq, ['seasonality_cliq_details.seasonality_detail.january'], type_format_number) #number
                new['february']= validates_data_used_file(kwargs_cliq, ['seasonality_cliq_details.seasonality_detail.february'], type_format_number) #number
                new['march']= validates_data_used_file(kwargs_cliq, ['seasonality_cliq_details.seasonality_detail.march'], type_format_number) #number
                new['april']= validates_data_used_file(kwargs_cliq, ['seasonality_cliq_details.seasonality_detail.april'], type_format_number) #number
                new['may']= validates_data_used_file(kwargs_cliq, ['seasonality_cliq_details.seasonality_detail.may'], type_format_number) #number
                new['june']= validates_data_used_file(kwargs_cliq, ['seasonality_cliq_details.seasonality_detail.june'], type_format_number) #number
                new['july']= validates_data_used_file(kwargs_cliq, ['seasonality_cliq_details.seasonality_detail.july'], type_format_number) #number
                new['august']= validates_data_used_file(kwargs_cliq, ['seasonality_cliq_details.seasonality_detail.august'], type_format_number) #number
                new['september']= validates_data_used_file(kwargs_cliq, ['seasonality_cliq_details.seasonality_detail.september'], type_format_number) #number
                new['october']= validates_data_used_file(kwargs_cliq, ['seasonality_cliq_details.seasonality_detail.october'], type_format_number) #number
                new['november']= validates_data_used_file(kwargs_cliq, ['seasonality_cliq_details.seasonality_detail.november'], type_format_number) #number
                new['december']= validates_data_used_file(kwargs_cliq, ['seasonality_cliq_details.seasonality_detail.december'], type_format_number) #number

        rest_data.append(new)

    try:
        if format_file == 'csv':
            return generic_csv(mapping, header, rest_data, translate_language('label_energyContract_download', request) )
        elif format_file == 'xlsx':
            styles=[
                {
                    'fields': [
                        "sap_contract", "month_hour", 
                        "hours", "cliq_contract", "year"
                    ], 
                    'number_format': '0'
                },
                {
                    'fields': [
                        "volume_mwh", "volume_mwm", 
                        "min_flexibility_pu", "max_flexibility_pu",
                        "min_modulation_pu", "max_modulation_pu",
                        "season_min_pu", "season_max_pu",
                        "mwm_volume",
                        "january", "february", "march", 
                        "april", "may", "june", "july", 
                        "august", "september", "october", 
                        "november", "december"
                    ], 
                    'number_format': '#,##0.0000'
                },
                {
                    'fields': [
                        "base_price_mwh", "base_contract_value",
                        "active_price_mwh", "retusd", "guaranteed_value"
                    ], 
                    "number_format":'R$ #,##0.0000'
                },
                {
                    'fields': [
                        "contractual_loss"
                    ], 
                    'number_format': '#,##0.0000\\%'
                }
            ]
            return generic_xls(mapping, header, rest_data, translate_language('label_energyContract_download', request), styles)
        elif format_file == 'pdf':
            return generic_pdf(mapping, header, rest_data, translate_language('label_energyContract_download', request) )
        else:
            return Response({'error': translate_language_error('error_unknown_format_file', request) }, status=status.HTTP_400_BAD_REQUEST)
    except:  # pragma: no cover
        # just to protect endpoint
        return Response({'error': translate_language_error('error_undefined', request) }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@check_module(modules.energy_contract, [permissions.VIEW, permissions.EDITN1])
def session_energy_contract_get_find_basic(request):
    """
       List all companies 
    """
    if request.method == 'GET':
        energy = function_find_objects(request)
        data, page_count, page_next, page_previous = generic_paginator(request, energy)
        serializer=function_find_format(data, request, False)
             
        response = collections.OrderedDict([
            ('count', page_count),
            ('next', page_next),
            ('previous', page_previous),
            ('results', serializer)
        ])
        return Response(response)

@api_view(['GET'])
@check_module(modules.energy_contract, [permissions.VIEW, permissions.EDITN1])
def get_data_agents_basic(request, format=None):
    """
        List all agents
    """
    serializer_context = {
        'request': request,

    }
    if request.method == 'GET':
        kwargs = {'vale_name_agent': 'vale_name_agent__contains'}
        ids = generic_queryset_filter(request, Agents, 'id_agents', **kwargs)
        agents_object = Agents.objects \
        .select_related('id_company') \
        .filter(id_agents__in=ids, status='S').order_by('vale_name_agent')
        try:
            serializer=[]
            for item in agents_object:
                item_json={
                    "id_agents": item.pk,
                    "vale_name_agent": item.vale_name_agent,
                    "status": item.status,
                    "company_detail": {
                    "id_company": item.id_company_id,
                    "company_name": item.id_company.company_name,
                    "type": item.id_company.type,
                    "status": item.id_company.status,
                    }
                }
                serializer.append(item_json)
        except:
            serializer = AgentsSerializerView(agents_object, many=True, context=serializer_context).data
        return Response(serializer)

@api_view(['GET'])
@check_module(modules.energy_contract, [permissions.VIEW, permissions.EDITN1])
def get_data_profile_basic(request, format=None):
    observation_log = ""
    if 'observation_log' in request.data:
        observation_log = request.data['observation_log']  # pragma: no cover

    serializer_context = {
        'request': request,
        'observation_log': observation_log
    }
    object_profile = Profile.objects\
        .select_related('id_agents__id_company')\
        .filter(status="S").order_by('name_profile')
    try:
        serializer=[]
        for item in object_profile:
            itemJson={}
            itemJson={
                "id_profile": item.pk,
                "name_profile": item.name_profile,
                "status": item.status,
                "agents_detail": {
                    "id_agents": item.id_agents_id if item.id_agents else "",
                    "id_company": item.id_agents.id_company_id if item.id_agents else "",
                    "vale_name_agent": item.id_agents.vale_name_agent if item.id_agents else "",
                    "status": item.id_agents.status if item.id_agents else "",
                    "company_detail": {
                        "id_company": item.id_agents.id_company_id if item.id_agents else "",
                        "company_name": item.id_agents.id_company.company_name if item.id_agents else "",
                        "type": item.id_agents.id_company.type if item.id_agents else "",
                        "status": item.id_agents.id_company.status if item.id_agents else ""
                    }
                },  
            }
            serializer.append(itemJson)
    except:
        serializer = ProfileAssetsSerializerView(object_profile, many=True, context=serializer_context).data
    return Response(serializer)


@api_view(['GET'])
@check_module(modules.energy_contract, [permissions.VIEW, permissions.EDITN1])
def list_energy_contract_summary(request):
    now = datetime.now()

    contracts = list(filter(None, request.GET.get("contracts", "").split('|')))
    master_only = request.GET.get("masterOnly")

    cliq_contracts = CliqContract.objects \
        .select_related("id_contract") \
        .select_related("id_contract__id_buyer_agents") \
        .select_related("id_contract__id_buyer_agents__id_company") \
        .select_related("id_contract__id_seller_agents") \
        .select_related("id_contract__id_seller_agents__id_company") \
        .select_related("id_buyer_profile") \
        .select_related("id_vendor_profile") \
        .select_related("id_buyer_asset_items__id_company")        
    
    cliq_contracts = cliq_contracts.filter(Q(
        id_contract__status="S",
        id_contract__volume_mwm__gt=0,
        id_contract__modality__in=['Longo Prazo','Curto Prazo'],
        id_contract__start_supply__lte=now,
        id_contract__type="C",
        id_contract__end_supply__gte=now,
        status="S") | Q(id_contract_cliq__in=contracts)
    )

    if master_only:
        cliq_contracts = cliq_contracts.filter(id_contract__id_buyer_agents__id_company__id_sap="1001")

    return Response(map(lambda contract: {
        'id_contract_cliq': int(contract.id_contract_cliq),
        'id_contract': int(contract.id_contract.id_contract),
        'contract_name': contract.id_contract.contract_name,
        'contract_start_supply': contract.id_contract.start_supply,
        'contract_end_supply': contract.id_contract.end_supply,
        'contract_status': contract.id_contract.status,
        'contract_type': contract.id_contract.type,
        'buyer_company_id': int(contract.id_contract.id_buyer_agents.id_company.id_company),
        'seller_company_id': int(contract.id_contract.id_seller_agents.id_company.id_company),
        'buyer_agent_id': int(contract.id_contract.id_buyer_agents.id_agents),
        'buyer_agent_name': contract.id_contract.id_buyer_agents.vale_name_agent,
        'buyer_assert_items_company_id': int(contract.id_buyer_asset_items.id_company.id_company) if contract.id_buyer_asset_items else None,
        'buyer_assert_items_company_name': contract.id_buyer_asset_items.id_company.company_name if contract.id_buyer_asset_items else None,
        'seller_agent_id': int(contract.id_contract.id_seller_agents.id_agents),
        'seller_agent_name': contract.id_contract.id_seller_agents.vale_name_agent,
        'buyer_profile_id': int(contract.id_buyer_profile.id_profile) if contract.id_buyer_profile else None,
        'buyer_profile_name': contract.id_buyer_profile.name_profile if contract.id_buyer_profile else None,
        'vendor_profile_id': int(contract.id_vendor_profile.id_profile),
        'vendor_profile_name': contract.id_vendor_profile.name_profile,
    }, cliq_contracts))    


def function_find_objects(request):
    kwargs = {
        'modality': 'modality__contains',
        'sap_contract': 'sap_contract__contains',
        'type': 'type__contains',
        'contract_name': 'contract_name__contains',
        'buyer_profile': 'id_buyer_profile__name_profile__contains',
        'seller_profile': 'id_seller_profile__name_profile__contains',
        'buyer_agents': 'id_buyer_agents__vale_name_agent__contains',
        'seller_agents': 'id_seller_agents__vale_name_agent__contains', 'status': 'status__contains'
    }
    kwargs_order = {
        'modality': 'modality',
        'sap_contract': 'sap_contract',
        'type': 'type',
        'contract_name': 'contract_name',
        'buyer_profile': 'id_buyer_profile__name_profile',
        'seller_profile': 'id_seller_profile__name_profile',
        'buyer_agents': 'id_buyer_agents__vale_name_agent',
        'seller_agents': 'id_seller_agents__vale_name_agent',
        'status': 'status',

        '-modality': '-modality',
        '-sap_contract': '-sap_contract',
        '-type': '-type',
        '-contract_name': '-contract_name',
        '-buyer_profile': '-id_buyer_profile__name_profile',
        '-seller_profile': '-id_seller_profile__name_profile',
        '-buyer_agents': '-id_buyer_agents__vale_name_agent',
        '-seller_agents': '-id_seller_agents__vale_name_agent',
        '-status': '-status'
    }

    if request.query_params.get('ordering') in kwargs_order:
        order_by = kwargs_order[request.query_params.get('ordering')]
    else:
        order_by = kwargs_order['modality']
    ids = generic_queryset_filter(request, EnergyContract, 'id_contract', **kwargs)

    energy = EnergyContract.objects\
        .select_related('id_buyer_agents').select_related('id_seller_agents')\
        .select_related('id_buyer_profile').select_related('id_seller_profile')\
        .select_related('id_energy_product')\
        .prefetch_related('precif_energy_contract').prefetch_related('flexib_energy_contract')\
        .prefetch_related('modul_energy_contract').prefetch_related('season_energy_contract')\
        .prefetch_related('guaran_energy_contract')\
        .prefetch_related('cliq_contract__id_vendor_profile').prefetch_related('cliq_contract__id_buyer_profile')\
        .prefetch_related('cliq_contract__id_contract').prefetch_related('cliq_contract__id_ccee')\
        .prefetch_related('cliq_contract__id_buyer_assets').prefetch_related('cliq_contract__id_buyer_asset_items')\
        .prefetch_related('cliq_contract__id_submarket')\
        .prefetch_related('cliq_contract__seasonalityCliq_cliqContract')\
        .prefetch_related('cliq_contract__seasonalityCliq_cliqContract__id_seasonality')\
        .exclude(status='T').filter(id_contract__in=ids).order_by(order_by)
    return energy

def function_find_format(data, request, file):
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
            itemJson=EnergyContractSerializerBasicView(item, many=False, context=serializer_context).data

            buyer_agents_detail=AgentsSerializerView(item.id_buyer_agents, many=False, context=serializer_context).data if item.id_buyer_agents else ""
            seller_agents_detail=AgentsSerializerView(item.id_seller_agents, many=False, context=serializer_context).data if item.id_seller_agents else ""
            itemJson['buyer_agents_detail']=buyer_agents_detail
            itemJson['seller_agents_detail']=seller_agents_detail

            buyer_profile_detail=ProfileSerializerView(item.id_buyer_profile, many=False, context=serializer_context).data if item.id_buyer_profile else ""
            seller_profile_detail=ProfileSerializerView(item.id_seller_profile, many=False, context=serializer_context).data if item.id_seller_profile else ""
            itemJson['buyer_profile_detail']=buyer_profile_detail
            itemJson['seller_profile_detail']=seller_profile_detail

            precif_energy_contract=PrecificationSerializer(item.precif_energy_contract, many=False, context=serializer_context).data if hasattr(item, 'precif_energy_contract') else ""
            flexib_energy_contract=FlexibilizationSerializer(item.flexib_energy_contract, many=False, context=serializer_context).data if hasattr(item, 'flexib_energy_contract') else ""
            modulation_energy_contract=ModulationSerializer(item.modul_energy_contract, many=False, context=serializer_context).data  if hasattr(item, 'modul_energy_contract') else ""
            season_energy_contract=SeasonalSerializer(item.season_energy_contract, many=False, context=serializer_context).data  if hasattr(item, 'season_energy_contract') else ""
            guaran_energy_contract=GuaranteeSerializer(item.guaran_energy_contract, many=False, context=serializer_context).data  if hasattr(item, 'guaran_energy_contract') else ""
            product=EnergyProductSerializerView(item.id_energy_product, many=False, context=serializer_context).data  if item.id_energy_product else ""

            itemJson['precif_energy_contract']=precif_energy_contract
            itemJson['flexib_energy_contract']=flexib_energy_contract
            itemJson['modulation_energy_contract']=modulation_energy_contract
            itemJson['season_energy_contract']=season_energy_contract
            itemJson['guaran_energy_contract']=guaran_energy_contract
            itemJson['product']=product
        
        except:
            serializer = EnergyContractSerializerView(item, many=False, context=serializer_context).data
        
        array_cliq_contact=[]
        if file:
            for item_cliq in item._prefetched_objects_cache['cliq_contract']:
                array_cliq_contact.append(CliqContractSerializerView(item_cliq, many=False, context=serializer_context).data)
        
        itemJson['cliq_contract']=array_cliq_contact
        serializer.append(itemJson)
    
    return serializer

@api_view(['GET'])
@check_module(modules.energy_contract, [permissions.VIEW, permissions.EDITN1])
def update_current_price_energy_contract(request, format=None):
    observation_log = "Automatic update of the current price due to the anniversary date."
    if 'observation_log' in request.data:
        observation_log = request.data['observation_log']
    serializer_context = {
        'request': request,
        'observation_log': observation_log
    }

    date = request.query_params.get('date', None)
    if date != None:
        today = datetime.strptime(date, '%Y-%m-%d')
    else:
        today = datetime.today()    
    
    #date_ago = today - timedelta(days = 15) # Birthdays 15 days ago
    precif_birthdays_ago = list(\
        Precification.objects\
            .filter(\
                birthday_date__lte = today,\
                id_contract__status = 'S',\
                id_variable_id__gt = 0\
            ).order_by('birthday_date')\
    ) # Query Cached

    connection.queries

    if (len(precif_birthdays_ago) == 0):
        return Response({'updateds': [], 'not_updateds': []})

    # If 1st day use previous month
    def change_date_previos_month(date):
        return date - timedelta(days = 1) if date.day == 1 else date

    dates = [p.birthday_date for p in precif_birthdays_ago] + [p.base_price_date for p in precif_birthdays_ago]    
    dates = [change_date_previos_month(date) for date in dates]
    dates = sorted(dates)
    months = [date.month for date in dates]
    years = [date.year for date in dates]

    # Prepare indexes for loop. Avoid too many selects!
    indexes = list(GlobalVariable.objects.filter(\
        month__in = months,\
        year__in = years,\
        status = 1
    )) # Query Cached
    
    updateds = []
    not_updateds = []
    for p in precif_birthdays_ago:
        birthday_date = change_date_previos_month(p.birthday_date)
        base_price_date = change_date_previos_month(p.base_price_date)
        # if p.id_variable_id == None or p.id_variable_id <= 0:
        #     not_updateds.append({p._meta.pk.name: p.pk, 'reason': 'price_index_null'})
        #     continue
        birthday_price_index_number = next((i.value for i in indexes\
            if i.year == birthday_date.year\
            and i.month == birthday_date.month\
            and i.variable_id == int(p.id_variable_id)), None)
        base_price_index_number = next((i.value for i in indexes\
            if i.year == base_price_date.year\
            and i.month == base_price_date.month\
            and i.variable_id == int(p.id_variable_id)), None)
        if (birthday_price_index_number == None or base_price_index_number == None):
            not_updateds.append({p._meta.pk.name: p.pk, 'reason': 'indexes_do_not_exists'})
            continue        
        if (base_price_index_number == 0):
            not_updateds.append({p._meta.pk.name: p.pk, 'reason': 'division_by_zero_in_base_price_index_number'})
            continue

        p_dict = model_to_dict(p, fields=[field.name for field in p._meta.fields])

        if p.base_price_mwh is not None: 
            p_dict['base_price_mwh'] = round(p.base_price_mwh, 6)
        
        if p.retusd is not None:
            p_dict['retusd'] = round(p.retusd, 6)

        p_dict['active_price_mwh'] = round(p.base_price_mwh * birthday_price_index_number / base_price_index_number, 6)
        # Set next birthday
        p_dict['birthday_date'] = p.birthday_date.replace(year = p.birthday_date.year + 1)
        # Set last updated
        p_dict['last_updated_current_price'] = today
        
        
        precif_serializer = PrecificationSerializer(p, data=p_dict, context=serializer_context)
        if precif_serializer.is_valid():
            precif_serializer.save()
            updateds.append({p._meta.pk.name: p.pk})
        else:
            not_updateds.append({p._meta.pk.name: p.pk, 'reason': 'errors', 'errors': precif_serializer.errors})
    
    return Response({'updateds': updateds, 'not_updateds': not_updateds}, status=status.HTTP_200_OK)

@api_view(['GET'])
@check_module(modules.energy_contract, [permissions.VIEW, permissions.EDITN1])
def list_flexibilization_type(request):
    return Response(FlexibilizationTypeSerializer(FlexibilizationType.objects, many=True).data)


@api_view(['GET'])
@check_module(modules.energy_contract, [permissions.EDITN1])
def session_energy_contract_save_temporary(request, pk):
    energy_contract = EnergyContract.objects.get(pk=pk)
    cliqs = CliqContract.objects.filter(id_contract=pk).count()
    if energy_contract.status == 'T':
        if cliqs == 0:
            return Response({'erro': 'UNABLE_SAVE_NO_CLICKS_FOUND'}, status=status.HTTP_400_BAD_REQUEST)    
        energy_contract.status = 'S'
        energy_contract.save()
        return Response({}, status=status.HTTP_200_OK)
    else:
        return Response({'erro': 'INVALID_STATUS'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@check_module(modules.energy_contract, [permissions.EDITN1])
def session_energy_contract_cancel_temporary(request, pk):
    energy_contracts = list(EnergyContract.objects.filter(temporary_expire_time__lt=datetime.now(timezone.utc), status='T'))
    energy_contracts.append(EnergyContract.objects.get(pk=pk))
    
    for energy_contract in energy_contracts:
        if energy_contract.status == 'T':
            with transaction.atomic():
                trans_savepoint = transaction.savepoint()
                try:                    
                    Guarantee.objects.filter(id_contract=energy_contract).delete()
                    Modulation.objects.filter(id_contract=energy_contract).delete()
                    Precification.objects.filter(id_contract=energy_contract).delete()
                    Seasonal.objects.filter(id_contract=energy_contract).delete()
                    Flexibilization.objects.filter(id_contract=energy_contract).delete()
                    ContractAttachment.objects.filter(id_contract=energy_contract).delete()
                    cliqs = CliqContract.objects.filter(id_contract=energy_contract)
                    for cliq in cliqs:
                        SeasonalityCliq.objects.filter(id_contract_cliq=cliq.pk).delete()
                        TransferContractPriority.objects.filter(id_contract_cliq=cliq.pk).delete()
                        cliq.delete()
                        if cliq.id_ccee:
                            CceeDescription.objects.get(pk=cliq.id_ccee.pk).delete()
                    energy_contract.delete()
                    transaction.savepoint_commit(trans_savepoint)
                except Exception as ex:
                    transaction.savepoint_rollback(trans_savepoint)
    return Response({}, status=status.HTTP_200_OK)
