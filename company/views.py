# coding: utf-8
from company.models import City, Address, CompanyContacts, BankAccount, Country, State, EletricUtilityCompany, Company, AccountType
from company.serializersViews import CompanySerializerView, CountrySerializerView, StateSerializerView, \
    CitySerializerVIew, CompanySerializerViewFindMany, CitySerializerSimpleView
from .serializers import AccountTypeSerializer
from core.models import Log
from core.attachment_utility import generic_data_csv_list, generic_csv, generic_pdf, generic_xls
from energy_composition.models import EnergyComposition
from company.serializers import CompanySerializer, AddressSerializer
from rest_framework import viewsets, status, generics, filters
from django.core.serializers.json import DjangoJSONEncoder
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import api_view
from rest_framework.response import Response
from core.views import generic_log_search, generic_detail_log, generic_log_search_basic, alter_number,\
    generic_subquery,generic_queryset_filter, validates_data_used_file
from django.forms import model_to_dict
from datetime import datetime, timedelta
from django.db.models import Q
import collections
import json
import csv
from django.http import HttpResponse
from SmartEnergy.auth import check_module
import SmartEnergy.auth.permissions as permissions
import SmartEnergy.auth.groups as groups
import SmartEnergy.auth.modules as modules

from io import StringIO, BytesIO
import pandas as pd
import pdfkit

from energy_composition.serializers import EnergyCompositionSerializer, PointCompositionSerializerViewBasic, ApportiomentCompositionSerializerViewBasic, EnergyCompositionSerializerViewBasic
from locales.translates_function import translate_language_header, translate_language, translate_language_error

from django.db import connection
from core.serializers import generic_validation_changed

from agents.models import Agents
from asset_items.models import AssetItems
from assets.models import Assets
from energy_composition.models import EnergyComposition
from gauge_point.models import GaugePoint, GaugeEnergyDealership

@api_view(['GET'])
@check_module(modules.company, [permissions.VIEW, permissions.EDITN1, permissions.APPROVALN1, permissions.APPROVALN2, permissions.APPROVALN3])
def validated_using(request, pk, format=None):
    kwargs = {EnergyComposition: 'id_company', Agents: 'id_company', AssetItems: 'id_company',\
                GaugePoint: 'id_company', Assets: 'id_company', GaugeEnergyDealership: 'id_dealership'}
    status_message=generic_validation_changed(pk, Company, kwargs, request)
    if status_message != 'S':
        return Response(status_message, status=status.HTTP_400_BAD_REQUEST)
    return Response(status_message, status=status.HTTP_200_OK)

@api_view(['GET'])
@check_module(modules.company, [permissions.VIEW, permissions.EDITN1, permissions.APPROVALN1, permissions.APPROVALN2, permissions.APPROVALN3])
def validated_code_sap(request, id_sap_resquest, format=None):
    if Company.objects.filter(id_sap=id_sap_resquest):
        return Response({'Id_sap '+ translate_language_error('error_code_sap', request) }, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response(status=status.HTTP_200_OK)


def get_data_company(pk):
    """
        List data about company
    """
    try:
        company = Company.objects.get(pk=pk)
    except Company.DoesNotExist:  # pragma: no cover
        # Insert security exception
        return Response(status=status.HTTP_404_NOT_FOUND)

    try:
        address = Address.objects.get(pk=company.id_address_id)
        kwargs = json.loads(json.dumps(model_to_dict(address), cls=DjangoJSONEncoder))
    except Address.DoesNotExist:  # pragma: no cover
        # The Address isn't required in database
        kwargs = {}

    kwargs['address_company'] = json.loads(json.dumps(model_to_dict(company), cls=DjangoJSONEncoder))
    try:
        city = City.objects.get(pk=address.id_city_id)
        kwargs['id_state'] = city.id_state_id
    except Exception:  # pragma: no cover
        # Insert id_state to front
        kwargs['id_state'] = "null"

    try:
        eletric_utility = EletricUtilityCompany.objects.get(id_company=pk)
        kwargs['address_company']['eletric_utility'] = json.loads(
            json.dumps(model_to_dict(eletric_utility), cls=DjangoJSONEncoder))
    except EletricUtilityCompany.DoesNotExist:  # pragma: no cover
        # The EletricUtilityCompany isn't required
        kwargs['address_company']['eletric_utility'] = {}

    array_bank = []
    array_contact = []
    for bank in BankAccount.objects.filter(id_company=pk,status='S'):
        array_bank.append(json.loads(json.dumps(model_to_dict(bank), cls=DjangoJSONEncoder)))

    for contact in CompanyContacts.objects.filter(id_company=pk,status='S'):
        array_contact.append(json.loads(json.dumps(model_to_dict(contact), cls=DjangoJSONEncoder)))
    kwargs['address_company']['company_contacts'] = array_contact
    kwargs['address_company']['bank_account'] = array_bank
    return kwargs


class CustomPaginationClass(PageNumberPagination):
    page_size_query_param = 'page_size'


class CompanyFindBasic(generics.ListAPIView):
    """
    API endpoint companies filtered
    """
    serializer_class = CompanySerializerViewFindMany
    pagination_class = CustomPaginationClass

    @check_module(modules.company, [permissions.VIEW, permissions.EDITN1, permissions.APPROVALN1, permissions.APPROVALN2, permissions.APPROVALN3])
    def get_queryset(self):
        """
        Filtering against query parameter in the URL.
        """
        try:
            queryset = function_find_companys(self.request)
            return queryset
        except Company.DoesNotExist:  # pragma: no cover
            # Insert security exception
            return Response(status=status.HTTP_404_NOT_FOUND)

class CompanyFind(generics.ListAPIView):
    """
    API endpoint companies filtered
    """
    serializer_class = CompanySerializerView
    pagination_class = CustomPaginationClass

    @check_module(modules.company, [permissions.VIEW, permissions.EDITN1, permissions.APPROVALN1, permissions.APPROVALN2, permissions.APPROVALN3])
    def get_queryset(self):
        """
        Filtering against query parameter in the URL.
        """
        try:
            filter_params = Q()
            queryset = Company.objects.all()
            company_name = self.request.query_params.get('company_name', None)
            sap = self.request.query_params.get('id_sap', None)
            registered_number = self.request.query_params.get('registered_number', None)
            type = self.request.query_params.get('type', None)
            state_number = self.request.query_params.get('state_number', None)
            status = self.request.query_params.get('status', None)
            city_name = self.request.query_params.get('city_name', None)
            state = self.request.query_params.get('state', None)
            country = self.request.query_params.get('country', None)
            date_creation_start = self.request.query_params.get('date_creation_start', None)
            date_creation_end = self.request.query_params.get('date_creation_end', None)
            ordering = self.request.query_params.get('ordering', None)

            if (date_creation_start and date_creation_end) is not None:
                date_creation_end = datetime.strptime(date_creation_end, '%Y-%m-%d')
                filter_params.add(Q(create_date__range=[date_creation_start, (date_creation_end + timedelta(days=1))]),
                                  Q.AND)

            if company_name is not None:
                filter_params.add(Q(company_name__contains=company_name), Q.AND)

            if registered_number is not None:
                filter_params.add(Q(registered_number__contains=registered_number), Q.AND)

            if type is not None:
                filter_params.add(Q(type=type), Q.AND)

            if state_number is not None:
                filter_params.add(Q(state_number__contains=state_number), Q.AND)

            if status is not None:
                filter_params.add(Q(status=status), Q.AND)

            if city_name is not None:
                filter_params.add(Q(id_address__id_city__city_name__contains=city_name), Q.AND)

            if state is not None:
                filter_params.add(Q(id_address__id_city__id_state__name__contains=state), Q.AND)

            if country is not None:
                filter_params.add(Q(id_address__id_city__id_state__id_country__name__contains=country), Q.AND)

            if sap is not None:
                filter_params.add(Q(id_sap__contains=sap), Q.AND)

            if ordering is None:
                ordering = ('company_name')

            queryset = queryset.filter(filter_params).order_by(ordering)

            return queryset
        except Company.DoesNotExist:  # pragma: no cover
            # Insert security exception
            return Response(status=status.HTTP_404_NOT_FOUND)


class AddressViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Address manipulation
    """
    queryset = Address.objects.all()
    serializer_class = AddressSerializer


class CountriesViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Countries manipulation
    """
    queryset = Country.objects.all()
    serializer_class = CountrySerializerView


@api_view(['GET'])
@check_module(modules.company, [permissions.VIEW, permissions.EDITN1, permissions.APPROVALN1, permissions.APPROVALN2, permissions.APPROVALN3])
def get_country(request):
    """
        get list country
    """

    serializer_context = {
        'request': request,
    }
    try:
        countries = Country.objects.all().order_by('name')
        serializer = CountrySerializerView(countries, many=True, context=serializer_context)
        return Response(serializer.data)
    except Country.DoesNotExist:  # pragma: no cover
        # Insert security exception
        return Response(status=status.HTTP_404_NOT_FOUND)



class CompanyViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Company manipulation
    """
    queryset = Company.objects.all()
    serializer_class = CompanySerializerView
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['type',
                       'company_name',
                       'registered_number',
                       'state_number',
                       'status',
                       'id_address__id_city__city_name',
                       'id_address__id_city__id_state__name',
                       'id_address__id_city__id_state__id_country__name']
    ordering = ['company_name']
    pagination_class = CustomPaginationClass


@api_view(['GET'])
@check_module(modules.company, [permissions.VIEW, permissions.EDITN1, permissions.APPROVALN1, permissions.APPROVALN2, permissions.APPROVALN3])
def get_energy_composition_company(request, pk):
    """
        get list energy composition by company
    """

    observation_log = ""
    if 'observation_log' in request.data:
        observation_log = request.data['observation_log']  # pragma: no cover


    serializer_context = {
        'request': request,
        'observation_log': observation_log
    }
    energy_composition = EnergyComposition.objects.select_related('id_company').select_related('id_accountant').select_related('id_director') \
            .select_related('id_segment').select_related('id_business') \
            .prefetch_related('point_energy_composition').prefetch_related('apport_energy_composition')\
            .filter(id_company=pk,status='S').order_by('composition_name')
    try:
        serializer=[]
        for item in energy_composition:
            item_json=EnergyCompositionSerializerViewBasic(item, many=False, context=serializer_context).data
            point_composition=PointCompositionSerializerViewBasic(item.point_energy_composition, many=True, context=serializer_context).data  if hasattr(item, 'point_energy_composition') else ""
            apport=ApportiomentCompositionSerializerViewBasic(item.apport_energy_composition, many=True, context=serializer_context).data  if hasattr(item, 'apport_energy_composition') else ""
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
            item_json['apport_energy_composition']= apport
            item_json['point_energy_composition']= point_composition

            serializer.append(item_json)
    except:
        serializer = EnergyCompositionSerializer(energy_composition, many=True, context=serializer_context).data
    return Response(serializer)

from django.db import connection

@api_view(['GET'])
@check_module(modules.company, [permissions.VIEW, permissions.EDITN1, permissions.APPROVALN1, permissions.APPROVALN2, permissions.APPROVALN3])
def get_state_by_country(request):
    """
        get list states by country
    """

    serializer_context = {
        'request': request,
    }
    try:
        country = request.query_params['id_country']
        states = State.objects.filter(id_country=country).order_by('name')
        serializer = StateSerializerView(states, many=True, context=serializer_context)
        return Response(serializer.data)
    except State.DoesNotExist:  # pragma: no cover
        # Insert security exception
        return Response(status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@check_module(modules.company, [permissions.VIEW, permissions.EDITN1, permissions.APPROVALN1, permissions.APPROVALN2, permissions.APPROVALN3])
def get_cities_by_state(request):
    """
        get cities by state
    """
    serializer_context = {
        'request': request,
    }
    try:
        id_state = request.query_params['id_state']
        cities = City.objects.filter(id_state=id_state).order_by('city_name')
        serializer = CitySerializerSimpleView(cities, many=True, context=serializer_context)
        citiesList = list(serializer.data)
        print(connection.queries)
        return Response(citiesList)
    except City.DoesNotExist:  # pragma: no cover
        # Insert security exception
        return Response(status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@check_module(modules.company, [permissions.VIEW, permissions.EDITN1, permissions.APPROVALN1, permissions.APPROVALN2, permissions.APPROVALN3])
def list_company_basic(request, format=None):
    kwargs = {
        'type': 'type__in'
    }       

    companies = Company.objects.filter(generic_subquery(request.query_params, kwargs))\
        .filter(status='S')\
        .order_by('company_name')\
        .values('id_company', 'company_name', 'type', 'characteristics')
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
    #print(connection.queries)
    return Response(companies)

@api_view(['GET'])
@check_module(modules.company, [permissions.VIEW, permissions.EDITN1, permissions.APPROVALN1, permissions.APPROVALN2, permissions.APPROVALN3])
def list_account_types(request):
     return Response(AccountTypeSerializer(AccountType.objects.all(), many=True).data)

@api_view(['POST'])
@check_module(modules.company, [permissions.EDITN1, permissions.APPROVALN1, permissions.APPROVALN2, permissions.APPROVALN3])
def session_company_post(request, format=None):
    """
        List all companies or create a new company
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
        new_company = {}

        for item in data['address_company']['company_contacts']:
            if item['cellphone']==" ": item['cellphone']=None #if the cellphone is passed by front null
        if data['number']==" " : data['number']=None #if the number is passed by front null 
         
        
        if 'address_company' in data:
            new_company = data['address_company']
            data.__delitem__('address_company')
        
        serializer = AddressSerializer(data=data, context=serializer_context)
        if serializer.is_valid():
            serializer.save()
            response_error = {}
            if new_company:
                pk = serializer.data['id_address']
                new_company['id_address'] = pk
                company = CompanySerializer(data=new_company, context=serializer_context)
                if company.is_valid():
                    company.save()
                else:
                    response_error = company.errors

                if response_error:
                    address = Address.objects.get(pk=pk)
                    address.delete()
                    return Response(response_error, status=status.HTTP_400_BAD_REQUEST)
                else:
                    serializer_data = collections.OrderedDict(get_data_company(company.data['id_company']))
                    return Response(serializer_data, status=status.HTTP_201_CREATED)
            return Response(serializer.data, status=status.HTTP_201_CREATED)  # pragma: no cover
        else:  # pragma: no cover
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@check_module(modules.company, [permissions.VIEW, permissions.EDITN1, permissions.APPROVALN1, permissions.APPROVALN2, permissions.APPROVALN3])
def session_company_get(request, format=None):
    """
        List all companies or create a new company
    """
    if request.method == 'GET':
        array = []
        # Todo: remover esse for que fica dando select no banco a cada iteração
        # Isso foi alterado no commit 183cd9c413cd211d48ff2490124cf3a956a0c74f
        for company in Company.objects.filter(status='S').order_by('company_name'):
            array.append(collections.OrderedDict(get_data_company(company.id_company)))
        return Response(array)

@api_view(['PUT'])
@check_module(modules.company, [permissions.EDITN1, permissions.APPROVALN1, permissions.APPROVALN2, permissions.APPROVALN3])
def session_company_put(request, pk, format=None):
    """
        Retrieve, update or delete a specific company.
    """
    observation_log = ""
    if 'observation_log' in request.data:
        observation_log = request.data['observation_log']

    serializer_context = {
        'request': request,
        'observation_log': observation_log
    }

    try:
        company = Company.objects.get(pk=pk)
        address = Address.objects.get(pk=company.id_address_id)
    except Company.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'PUT':
        data = request.data
        # logial exclusion of contacts and bank
        if data:
            id_company = data['address_company']['id_company']
            try:
                all_contacts = CompanyContacts.objects.filter(id_company=id_company)
                for contact in all_contacts:
                    sel_contact = json.loads(json.dumps(model_to_dict(contact), cls=DjangoJSONEncoder))
                    # if record was deleted
                    if len([sub["id_contacts"] for sub in data['address_company']['company_contacts'] if sub["id_contacts"] == sel_contact["id_contacts"]]) == 0:
                        #check if key exists
                        if not (data['address_company'].get('company_contacts',None)):
                            data['address_company']['company_contacts'] = []

                        #logical exclusion
                        sel_contact['status'] = 'N'

                        data['address_company']['company_contacts'].append(sel_contact)
            except KeyError as e:
                kwargs = {'contacts:': translate_language_error('error_key_error', request)+": "+ e }
                return Response(collections.OrderedDict(kwargs), status=status.HTTP_400_BAD_REQUEST)               

            try:
                all_banks = BankAccount.objects.filter(id_company=id_company)
                for bank in all_banks:
                    sel_bank = json.loads(json.dumps(model_to_dict(bank), cls=DjangoJSONEncoder))
                    # if record was deleted
                    if len([sub["id_bank"] for sub in data['address_company']['bank_account'] if sub["id_bank"] == sel_bank["id_bank"]]) == 0:
                        #check if key exists
                        if not (data['address_company'].get('bank_account',None)):
                            data['address_company']['bank_account'] = []

                        #logical exclusion
                        sel_bank['status'] = 'N'

                        data['address_company']['bank_account'].append(sel_bank)
            except KeyError as e:
                kwargs = {'contacts:': translate_language_error('error_key_error', request)}
                return Response(collections.OrderedDict(kwargs), status=status.HTTP_400_BAD_REQUEST)    


        data_company = {}
        for item in data['address_company']['company_contacts']:
            if item['cellphone']==" ":item['cellphone']=None #if the cellphone is passed by front null
        if data['number']==" " : data['number']=None #if the number is passed by front null 

        if 'address_company' in data:
            data_company = data['address_company']
            data.__delitem__('address_company')

        if data_company:
            try:
                company_model = Company.objects.get(pk=data_company['id_company'])
                company = CompanySerializer(company_model, data=data_company, context=serializer_context)
                if company.is_valid():
                    company.save()
                else:
                    return Response(company.errors, status=status.HTTP_400_BAD_REQUEST)
            except Company.DoesNotExist:
                return Response(status=status.HTTP_404_NOT_FOUND)
            except KeyError as e:
                kwargs = {'id_company:': translate_language_error('error_company_required', request)+": "+e }
                return Response(collections.OrderedDict(kwargs), status=status.HTTP_400_BAD_REQUEST)
        serializer = AddressSerializer(address, data=data, context=serializer_context)
        if serializer.is_valid():
            serializer.save()
            serializer_data = collections.OrderedDict(get_data_company(pk))
            return Response(serializer_data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)  # pragma: no cover

@api_view(['GET'])
@check_module(modules.company, [permissions.VIEW, permissions.EDITN1, permissions.APPROVALN1, permissions.APPROVALN2, permissions.APPROVALN3])
def session_company_get_detail(request, pk, format=None):
    """
        Retrieve, update or delete a specific company.
    """
    def convert_float(value):
        try:
            return float(value)
        except:
            return 0

    if request.method == 'GET':
        if not Company.objects.filter(pk=pk):
            return Response(status=status.HTTP_404_NOT_FOUND)
        # Todo: usar serializer
        #serializer = CompanySerializer(company, context=serializer_context)
        serializer = collections.OrderedDict(get_data_company(pk))
        serializer['address_company']['eletric_utility']['instaled_capacity'] = convert_float(serializer['address_company']['eletric_utility']['instaled_capacity'])
        serializer['address_company']['eletric_utility']['guaranteed_power'] = convert_float(serializer['address_company']['eletric_utility']['guaranteed_power'])
        serializer['address_company']['eletric_utility']['regulatory_act'] = serializer['address_company']['eletric_utility']['regulatory_act']
        serializer['address_company']['eletric_utility']['internal_loss'] = convert_float(serializer['address_company']['eletric_utility']['internal_loss'])
        serializer['address_company']['eletric_utility']['transmission_loss'] = convert_float(serializer['address_company']['eletric_utility']['transmission_loss'])
        return Response(serializer)

@api_view(['GET'])
@check_module(modules.company, [permissions.VIEW, permissions.EDITN1, permissions.APPROVALN1, permissions.APPROVALN2, permissions.APPROVALN3])
def session_company_file(request, format=None):
    """
    API endpoint companies filtered
    """
    serializer_context = {
        'request': request,
    }

    format_file = None

    if not(request.query_params.get('format_file',None) == None):
        format_file = request.query_params.get('format_file',None)
    else:
        return Response({'error': translate_language_error('error_format_file_csv_or_pdf', request) }, status=status.HTTP_400_BAD_REQUEST)

    # let empty to use de mapping (original) names: header = {}
    # must be in the same order of mapping
    queryset = function_find_companys(request)
    serializer = CompanySerializerView(queryset, many=True, context=serializer_context).data
    for item in serializer:
        if 'address' in item:
            del item['address']['number']    
        
    payload = serializer
    payload = json.dumps(payload, indent=10, default=str).encode('utf-8')
    rest = json.loads(payload)

    header = {
                'type_company' : 'field_company_type',
                'id_sap' : 'field_sap',
                'company_name' : 'field_name',
                'state_number' : 'field_state_number',
                'registered_number' : 'field_registered_number',
                'country_name' : 'field_country',
                'state_name' : 'field_state',
                'city_name' : 'field_city',
                'neighborhood' : 'field_neighborhood',
                'street' : 'field_street',
                'number' : 'field_number',
                'complement' : 'field_complement',
                'zip_code' : 'field_zipcode',
                'characteristics' : 'field_characteristics',
                'instaled_capacity' : 'field_instaled_capacity',
                'guaranteed_power': 'field_guaranteed_power',
                'regulatory_act': 'field_regulatory_act',
                'internal_loss': 'field_internal_loss',
                'transmission_loss': 'field_transmission_loss',
                'status_company' : 'Status',
                'create_date': 'field_create_date',
                'type_contact' : 'field_contacts_type',
                'responsible' : 'field_contacts_name',
                'email' : 'Email',
                'phone' : 'field_contact_number',
                'cellphone' : 'field_contact_mobile',
                'status_contact' : 'field_contact_status',
                'bank': 'field_bank',
                'bank_agency': 'field_agency',
                'account_number': 'field_accounts',
                'account_type': 'field_account_type',
                'other': 'field_other',
                'main_account': 'field_mainAccount',
                'status_bank': 'field_bank_status'
            }
    header = translate_language_header(header, request)
    mapping = [
        'type_company',
        'id_sap',
        'company_name',
        'state_number',
        'registered_number',
        'country_name',
        'state_name',
        'city_name',
        'neighborhood',
        'street',
        'number',
        'complement',
        'zip_code',
        'characteristics',
        'instaled_capacity',
        'guaranteed_power',
        'regulatory_act',
        'internal_loss',
        'transmission_loss',
        'status_company',
        'create_date',
        'type_contact',
        'responsible',
        'email',
        'phone',
        'cellphone',
        'status_contact',
        'bank',
        'bank_agency',
        'account_number',
        'account_type',
        'other',
        'main_account',
        'status_bank'
    ]

    rest = generic_data_csv_list(rest, ['bank_account', 'company_contacts'])
    rest_data = []

    type_format_number=0 if format_file=='pdf' else 1
    for index in range(len(rest)):
        kwargs = rest[index]
        statusBank = validates_data_used_file(kwargs, ['bank_account', 'status'], 0)
        statusContact = validates_data_used_file(kwargs, ['company_contacts', 'status'], 0)

        new = {
            'type_company': translate_language("field_type_company_"+validates_data_used_file(kwargs, ['type'], 0), request),
            'id_sap': validates_data_used_file(kwargs, ['id_sap'], type_format_number), #number Int
            'company_name': validates_data_used_file(kwargs, ['company_name'], 0),
            'state_number': validates_data_used_file(kwargs, ['state_number'], 0),
            'registered_number': validates_data_used_file(kwargs, ['registered_number'], type_format_number), #number Int
            
            'country_name': validates_data_used_file(kwargs, ['address', 'city', 'state', 'country', 'name'], 0),
            'state_name': validates_data_used_file(kwargs, ['address', 'city', 'state', 'name'], 0),
            'city_name': validates_data_used_file(kwargs, ['address', 'city', 'city_name'], 0),

            'neighborhood': validates_data_used_file(kwargs, ['address', 'neighborhood'], 0),
            'street': validates_data_used_file(kwargs, ['address', 'street'], 0),
            'number': validates_data_used_file(kwargs, ['address', 'number_address'], type_format_number), #number Int
            'complement': validates_data_used_file(kwargs, ['address', 'complement'], 0),
            'zip_code': validates_data_used_file(kwargs, ['address', 'zip_code'], 0),

            'characteristics': translate_language(validates_data_used_file(kwargs, ['characteristics'], 0), request),
            'instaled_capacity': validates_data_used_file(kwargs, ['eletric_utility', 'instaled_capacity'], type_format_number), #number
            'guaranteed_power': validates_data_used_file(kwargs, ['eletric_utility', 'guaranteed_power'], type_format_number), #number
            'regulatory_act': validates_data_used_file(kwargs, ['eletric_utility', 'regulatory_act'], 0),
            'internal_loss': validates_data_used_file(kwargs, ['eletric_utility', 'internal_loss'], type_format_number), #number
            'transmission_loss': validates_data_used_file(kwargs, ['eletric_utility', 'transmission_loss'], type_format_number), #number
            
            'status_company': translate_language("field_status_"+validates_data_used_file(kwargs, ['status'], 0), request),
            'create_date': datetime.strptime(kwargs['create_date'].split("T")[0], '%Y-%m-%d').strftime("%d/%m/%Y"),

            'responsible': "",
            'email': "",
            'phone': "",
            'cellphone': "",
            'type_contact': "",
            'status_contact': "",

            'bank': "",
            'bank_agency': "",
            'account_number': "",
            'account_type': "",
            'other': "",
            'main_account': "",
            'status_bank': ""
        }
        if statusContact and statusContact=='S':
            new['responsible']= validates_data_used_file(kwargs, ['company_contacts', 'responsible'], 0)
            new['email']= validates_data_used_file(kwargs, ['company_contacts', 'email'], 0)
            new['phone']= validates_data_used_file(kwargs, ['company_contacts', 'phone'], 0)
            new['cellphone']= validates_data_used_file(kwargs, ['company_contacts', 'cellphone'], 0)
            new['type_contact']= validates_data_used_file(kwargs, ['company_contacts', 'type'], 0)
            new['status_contact']= translate_language("field_status_"+statusContact, request)

        if statusBank and statusBank=='S':
            new['bank']=  validates_data_used_file(kwargs, ['bank_account', 'bank'], 0)
            new['bank_agency']=  validates_data_used_file(kwargs, ['bank_account', 'bank_agency'], 0)
            new['account_number']=  validates_data_used_file(kwargs, ['bank_account', 'account_number'], 0)
            new['account_type']=  validates_data_used_file(kwargs, ['bank_account', 'account_type'], 0)
            new['account_type']= AccountType.objects.get(id_account_type=new['account_type']).description
            new['other']=  validates_data_used_file(kwargs, ['bank_account', 'other'], 0)
            new['main_account']=  translate_language("field_response_"+validates_data_used_file(kwargs, ['bank_account', 'main_account'], 0), request)           
            new['status_bank']=  translate_language("field_status_"+statusBank, request)
        
        rest_data.append(new)
    try:
        if format_file == 'csv':
            return generic_csv(mapping, header, rest_data, translate_language("label_company_download", request) )
        elif format_file == 'xlsx':
            styles=[
                {
                    'fields': [
                        "id_sap", "registered_number", "number"
                    ], 
                    'number_format': '0'
                },
                {
                    'fields': [
                        "instaled_capacity", "guaranteed_power"
                    ], 
                    'number_format': '#,##0.0000'
                },
                {
                    'fields': [
                        "transmission_loss", "internal_loss"
                    ], 
                    'number_format': '#,##0.00\\%'
                }
            ]
            return generic_xls(mapping, header, rest_data, translate_language("label_company_download", request), styles)
        elif format_file == 'pdf':
            return generic_pdf(mapping, header, rest_data, translate_language("label_company_download", request), True)
        else:
            return Response({'error': translate_language_error('error_unknown_format_file', request) }, status=status.HTTP_400_BAD_REQUEST)
    except:  # pragma: no cover
        # just to protect endpoint
        return Response({'error': translate_language_error('error_undefined', request) }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@check_module(modules.company, [permissions.VIEW, permissions.EDITN1, permissions.APPROVALN1, permissions.APPROVALN2, permissions.APPROVALN3])
def session_basic_log(request, pk, format=None):
    kwargs = {'core': Company, 'core_pk': 'id_company', 'core+': [{Address: 'id_address'}],
              'child': [CompanyContacts, BankAccount, EletricUtilityCompany]}
    logs = generic_log_search_basic(generic_log_search(pk, **kwargs))

    ids_city=[]
    for item in logs:
        if 'new_value' in item['ADDRESS']:
            if item['ADDRESS']['new_value'] and 'id_city' in item['ADDRESS']['new_value']:
                if type(item['ADDRESS']['new_value']['id_city'])==dict:
                    ids_city.append(item['ADDRESS']['new_value']['id_city']['value'])
                else:
                    ids_city.append(item['ADDRESS']['new_value']['id_city'])

    related_cities = City.objects.filter(id_city__in=ids_city)

    serializer_related_cities = CitySerializerVIew(related_cities, many=True)

    return Response({
        'logs': logs,
        'statics_relateds': {
            'cities': serializer_related_cities.data
        }
    })


@api_view(['GET'])
@check_module(modules.company, [permissions.VIEW, permissions.EDITN1, permissions.APPROVALN1, permissions.APPROVALN2, permissions.APPROVALN3])
def get_energy_compositions_basic(request, company_id):
    compositions = EnergyComposition.objects.filter(status='S', id_company=company_id).order_by('composition_name').values('id_energy_composition', 'composition_name')
    compositions = map(lambda c: {'id_energy_composition': c['id_energy_composition'], 'composition_name': c['composition_name']}, compositions)
    #print(connection.queries)
    return Response(compositions)


def function_find_companys(request):
    kwargs = {
        'id_company': 'id_company',
        'company_name': 'company_name__contains',
        'id_sap': 'id_sap__contains',
        'registered_number': 'registered_number__contains',
        'type': 'type',
        'state_number': 'state_number__contains',
        'status': 'status__contains',
        'city_name': 'id_address__id_city__city_name__contains',
        'state': 'id_address__id_city__id_state__name__contains',
        'country': 'id_address__id_city__id_state__id_country__name__contains',
        'date_creation_start': 'create_date__gte',
        'date_creation_end': 'create_date__lte',
    }
    kwargs_order = {
        'id_company': 'id_company',
        'company_name': 'company_name',
        'id_sap': 'id_sap',
        'registered_number': 'registered_number',
        'type': 'type',
        'state_number': 'state_number',
        'status': 'status',
        'city_name': 'id_address__id_city__city_name',
        'state': 'id_address__id_city__id_state__name',
        'country': 'id_address__id_city__id_state__id_country',
        'create_date': 'create_date',

        '-id_company': '-id_company',
        '-company_name': '-company_name',
        '-id_sap': '-id_sap',
        '-registered_number': '-registered_number',
        '-type': '-type',
        '-state_number': '-state_number',
        '-status': '-status',
        '-city_name': '-id_address__id_city__city_name',
        '-state': '-id_address__id_city__id_state__name',
        '-country': '-id_address__id_city__id_state__id_country',
        '-create_date': '-create_date',
    }

    if request.query_params.get('ordering') :
        order_by = request.query_params.get('ordering')
    else:
        order_by = kwargs_order['company_name']

    ids=generic_queryset_filter(request, Company, 'id_company', **kwargs)
    company_obj=Company.objects.filter(id_company__in=ids).order_by(order_by)\
        .select_related('id_address').select_related('id_address__id_city').select_related('id_address__id_city__id_state') \
        .select_related('id_address__id_city__id_state__id_country').prefetch_related('id_company_contacts') \
        .prefetch_related('id_company_eletric').prefetch_related('id_company_bank')
    return company_obj
