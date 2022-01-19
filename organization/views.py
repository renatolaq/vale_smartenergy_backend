import csv
import json

from django.http import HttpResponse
from rest_framework import viewsets, status, generics, serializers
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
from itertools import chain
import collections

from core.models import Log
from core.views import generic_log_search, generic_log_search_basic, generic_paginator, validates_data_used_file
from core.serializers import LogSerializer
from core.attachment_utility import get_leaves, generic_csv, generic_pdf, generic_data_csv_list, generic_xls
from organization.models import Segment, Business, DirectorBoard, AccountantArea, Product, OrganizationalType, ElectricalGrouping, ProductionPhase
from organization.serializers import OrganisationSegmentSerializer, OrganisationBusinessSerializer, \
    OrganisationDirectorBoardSerializer, OrganisationAccountantAreaSerializer, OrganisationProductSerializer, OrganisationAgrupationEletrictSerializer, OrganizationProductionPhaseSerializer
from organization.serializersViews import OrganizationSegmentSerializerView, OrganizationBusinessSerializerView, \
    OrganizationDirectorBoardSerializerView, OrganizationAccountSerializerView, OrganizationProductSerializerView, \
    FeedSerializers, OrganizationSerializerView, OrganizationAgrupationEletrictSerializerView, OrganizationProductionPhaseSerializerView
from locales.translates_function import translate_language_header, translate_language, translate_language_error
from SmartEnergy.auth import check_module
import SmartEnergy.auth.permissions as permissions
import SmartEnergy.auth.modules as modules
from unicodedata import normalize
from django.core.paginator import Paginator


class LogViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Log monipulation
    """
    queryset = Log.objects.all()
    serializer_class = LogSerializer


# Search organization
class CustomPaginationClass(PageNumberPagination):
    page_size_query_param = 'page_size'


class OrganizationFind(generics.ListAPIView):
    """
    API endpoint companies filtered
    """
    serializer_class = FeedSerializers
    pagination_class = CustomPaginationClass
    @check_module(modules.organizational, [permissions.VIEW, permissions.EDITN1])
    def get_queryset(self):
        """
        Filtering against query parameter in the URL.
        """
        try:
            filter_params = Q()

            queryset1 = AccountantArea.objects.all()
            queryset2 = DirectorBoard.objects.all()
            queryset3 = Business.objects.all()
            queryset4 = Product.objects.all()
            queryset5 = Segment.objects.all()
            queryset6 = ElectricalGrouping.objects.all()
            queryset7 = ProductionPhase.objects.all()

            model = self.request.query_params.get('model', None)
            description = self.request.query_params.get('description', None)
            status = self.request.query_params.get('status', None)
            ordering = self.request.query_params.get('ordering', None)

            if description is not None:
                filter_params = Q(description__contains=description)
            if status is not None:
                filter_params.add(Q(status__contains=status), Q.AND)

            queryset = []
            if model is not None:  # check if it was sorted by type
                if model == "1":  # Accountant Area
                    if queryset1:  # check for data
                        queryset1 = queryset1.filter(filter_params)
                        queryset = queryset1
                if model == "2":  # Director Board
                    if queryset2:  # check for data
                        queryset2 = queryset2.filter(filter_params)
                        queryset = queryset2
                if model == "3":  # Business
                    if queryset3:  # check for data
                        queryset3 = queryset3.filter(filter_params)
                        queryset = queryset3
                if model == "4":  # Product
                    if queryset4:  # check for data
                        queryset4 = queryset4.filter(filter_params)
                        queryset = queryset4
                if model == "5":  # Segment
                    if queryset5:  # check for data
                        queryset5 = queryset5.filter(filter_params)
                        queryset = queryset5
                if model == "6":  # ElectricalGrouping
                    if queryset6:  # check for data
                        queryset6 = queryset6.filter(filter_params)
                        queryset = queryset6
                if model == "7":  # ElectricalGrouping
                    if queryset7:  # check for data
                        queryset7 = queryset7.filter(filter_params)
                        queryset = queryset7
            else:  # otherwise select all types
                queryset1 = queryset1.filter(filter_params)
                queryset2 = queryset2.filter(filter_params)
                queryset3 = queryset3.filter(filter_params)
                queryset4 = queryset4.filter(filter_params)
                queryset5 = queryset5.filter(filter_params)
                queryset6 = queryset6.filter(filter_params)
                queryset7 = queryset7.filter(filter_params)
                queryset = list(chain(queryset1, queryset3, queryset2, queryset6, queryset4, queryset5, queryset7))

            if ordering is not None:  # ordering default model
                if ordering == "-model":
                    queryset = list(chain(queryset5, queryset4, queryset6, queryset2, queryset3, queryset1))
                if ordering == "description":
                    queryset = sorted(queryset, key=lambda instance: instance.description, reverse=False)
                elif ordering == "-description":
                    queryset = sorted(queryset, key=lambda instance: instance.description, reverse=True)
                if ordering == "status":
                    queryset = sorted(queryset, key=lambda instance: instance.status, reverse=False)
                elif ordering == "-status":
                    queryset = sorted(queryset, key=lambda instance: instance.status, reverse=True)

            results = list()
            for entry in queryset:
                item_type = entry.__class__.__name__.lower()
                if isinstance(entry, Segment):
                    serializer = OrganizationSegmentSerializerView(entry, context=self.get_serializer_context())
                elif isinstance(entry, Business):
                    serializer = OrganizationBusinessSerializerView(entry, context=self.get_serializer_context())
                elif isinstance(entry, DirectorBoard):
                    serializer = OrganizationDirectorBoardSerializerView(entry, context=self.get_serializer_context())
                elif isinstance(entry, AccountantArea):
                    serializer = OrganizationAccountSerializerView(entry, context=self.get_serializer_context())
                elif isinstance(entry, Product):
                    serializer = OrganizationProductSerializerView(entry, context=self.get_serializer_context())
                elif isinstance(entry, ElectricalGrouping):
                    serializer = OrganizationAgrupationEletrictSerializerView(entry, context=self.get_serializer_context())
                elif isinstance(entry, ProductionPhase):
                    serializer = OrganizationProductionPhaseSerializerView(entry, context=self.get_serializer_context())

                results.append({'item_type': item_type, 'data': serializer.data})
            return results

        except:
            return Response(status=status.HTTP_404_NOT_FOUND)

    pagination_class = CustomPaginationClass


def remover_acentos(txt):
    return normalize('NFKD', txt).encode('ASCII', 'ignore').decode('ASCII')

def function_find_basic(request):
    model = request.query_params.get('model', None)
    description = request.query_params.get('description', '')
    status = request.query_params.get('status', '')
    ordering = request.query_params.get('ordering', None)
    list_type=[
        {'type': remover_acentos(translate_language('Área contábil', request)), 'model' : AccountantArea, 'id_value': 1},
        {'type': remover_acentos(translate_language('Diretoria', request)), 'model' : DirectorBoard, 'id_value': 2},
        {'type': remover_acentos(translate_language('Negócio', request)), 'model': Business, 'id_value': 3},
        {'type': remover_acentos(translate_language('Produto', request)), 'model' : Product, 'id_value': 4},
        {'type': remover_acentos(translate_language('Segmento', request)), 'model': Segment, 'id_value': 5},
        {'type': remover_acentos(translate_language('Agrupamento Elétrico', request)), 'model' : ElectricalGrouping, 'id_value': 6},
        {'type': remover_acentos(translate_language('Fase Produtiva', request)), 'model' : ProductionPhase, 'id_value': 7}
    ]

    if ordering=='-model':
        list_type= sorted(list_type, key = lambda k: k['type'], reverse=True)
    else:
        list_type= sorted(list_type, key = lambda k: k['type'])
    
    response_obj=[]
    valid_obj=False
    for obj_item in list_type:
        if model is None:
            valid_obj=True
        else:
            if int(model) == obj_item['id_value']:
                valid_obj=True
        if valid_obj:
            valid_obj=False
            if description and status:
                return_value=obj_item['model'].objects.filter(description__contains=description, status=status)
            elif description:
                return_value=obj_item['model'].objects.filter(description__contains=description)
            elif status:
                return_value=obj_item['model'].objects.filter(status=status)
            else:
                return_value=obj_item['model'].objects.all()
            response_obj.append(return_value)

    reponse_finaly=[]
    for obj_item_all in response_obj:
        reponse_finaly = list(chain(reponse_finaly, obj_item_all))

    if ordering == "description":
        reponse_finaly = sorted(reponse_finaly, key=lambda instance: instance.description, reverse=False)
    elif ordering == "-description":
        reponse_finaly = sorted(reponse_finaly, key=lambda instance: instance.description, reverse=True)
    elif ordering == "status":
        reponse_finaly = sorted(reponse_finaly, key=lambda instance: instance.status, reverse=False)
    elif ordering == "-status":
        reponse_finaly = sorted(reponse_finaly, key=lambda instance: instance.status, reverse=True)

    return reponse_finaly

@api_view(['GET'])
@check_module(modules.organizational, [permissions.VIEW, permissions.EDITN1])
def session_organizational_find_basic(request, format=None):
    reponse_finaly =function_find_basic(request)
    data, page_count, page_next, page_previous = generic_paginator(request, reponse_finaly)
    reponse_finaly_json=[]
    for entry in data:
        item_type = entry.__class__.__name__.lower()
        if isinstance(entry, Segment):
            serializer = OrganizationSegmentSerializerView(entry, context=request)
        elif isinstance(entry, Business):
            serializer = OrganizationBusinessSerializerView(entry, context=request)
        elif isinstance(entry, DirectorBoard):
            serializer = OrganizationDirectorBoardSerializerView(entry, context=request)
        elif isinstance(entry, AccountantArea):
            serializer = OrganizationAccountSerializerView(entry, context=request)
        elif isinstance(entry, Product):
            serializer = OrganizationProductSerializerView(entry, context=request)
        elif isinstance(entry, ElectricalGrouping):
            serializer = OrganizationAgrupationEletrictSerializerView(entry, context=request)
        elif isinstance(entry, ProductionPhase):
            serializer = OrganizationProductionPhaseSerializerView(entry, context=request)

        reponse_finaly_json.append({'item_type': item_type, 'data': serializer.data})
    
    response = collections.OrderedDict([
            ('count', page_count),
            ('next', page_next),
            ('previous', page_previous),
            ('results', reponse_finaly_json)
    ])
    return Response(response)

#############Segment
class OrganizationSegmentViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Organization monipulation
    """
    queryset = Segment.objects.all()
    serializer_class = OrganisationSegmentSerializer


#############Business
class OrganizationBusinessViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Organization monipulation
    """
    queryset = Business.objects.all()
    serializer_class = OrganisationBusinessSerializer


#############DirectorBoard
class OrganizationDirectorBoardViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Organization monipulation
    """
    queryset = DirectorBoard.objects.all()
    serializer_class = OrganisationDirectorBoardSerializer


#############AccountantArea
class OrganizationAccountantAreaViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Organization monipulation
    """
    queryset = AccountantArea.objects.all()
    serializer_class = OrganisationAccountantAreaSerializer

#############AccountantArea
class OrganizationProductionPhaseViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Organization monipulation
    """
    queryset = ProductionPhase.objects.all()
    serializer_class = OrganizationProductionPhaseSerializer


@api_view(['GET'])
#@check_module(modules.organizational, [permissions.VIEW, permissions.EDITN1])
def show_organization(request, model):
    if model==1:
        organization=OrganizationAccountSerializerView(AccountantArea.objects.filter(status='S').order_by('description'), many=True, context=request)
    elif model==2:
        organization=OrganizationDirectorBoardSerializerView(DirectorBoard.objects.filter(status='S').order_by('description'), many=True, context=request)
    elif model==3:
        organization=OrganizationBusinessSerializerView(Business.objects.filter(status='S').order_by('description'), many=True, context=request)
    elif model==4:
        organization=OrganizationProductSerializerView(Product.objects.filter(status='S').order_by('description'), many=True, context=request)
    elif model==5:
        organization=OrganizationSegmentSerializerView(Segment.objects.filter(status='S').order_by('description'), many=True, context=request)
    elif model==6:
        organization=OrganizationAgrupationEletrictSerializerView(ElectricalGrouping.objects.filter(status='S').order_by('description'), many=True, context=request)
    elif model==7:
        organization=OrganizationProductionPhaseSerializerView(ProductionPhase.objects.filter(status='S').order_by('description'), many=True, context=request)
    else: 
        return Response(status=status.HTTP_404_NOT_FOUND)   
    return Response(organization.data)


def valida_Description(request, description, model, pk):
    
    translation = translate_language_error('error_description_equal', request)
    if model == 1:
        if AccountantArea.objects.filter(description=description):
            accountantArea = AccountantArea.objects.filter(description=description)
            if accountantArea[0].pk != pk:
                raise serializers.ValidationError(translation)
        return description
    elif model == 2:
        if DirectorBoard.objects.filter(description=description):
            directorBoard = DirectorBoard.objects.filter(description=description)
            if directorBoard[0].pk != pk:
                raise serializers.ValidationError(translation)
        return description
    elif model == 3:
        if Business.objects.filter(description=description):
            business = Business.objects.filter(description=description)
            if business[0].pk != pk:
                raise serializers.ValidationError(translation)
        return description
    elif model == 4:
        if Product.objects.filter(description=description):
            product = Product.objects.filter(description=description)
            if product[0].pk != pk:
                raise serializers.ValidationError(translation)
        return description
    elif model == 5:
        if Segment.objects.filter(description=description):
            segment = Segment.objects.filter(description=description)
            if segment[0].pk != pk:
                raise serializers.ValidationError(translation)
        return description
    elif model == 6:
        if ElectricalGrouping.objects.filter(description=description):
            electricalGrouping = ElectricalGrouping.objects.filter(description=description)
            if electricalGrouping[0].pk != pk:
                raise serializers.ValidationError(translation)
        return description
    elif model == 7:
        if ProductionPhase.objects.filter(description=description):
            productionPhase = ProductionPhase.objects.filter(description=description)
            if productionPhase[0].pk != pk:
                raise serializers.ValidationError(translation)
        return description

@api_view(['GET'])
@check_module(modules.organizational, [permissions.VIEW, permissions.EDITN1])
def session_organizational_get(request, format=None):
    """
        List all organizations
    """
    observation_log = ""
    if 'observation_log' in request.data:
        observation_log = request.data['observation_log']

    serializer_context = {
        'request': request,
        'observation_log': observation_log
    }

    if request.method == 'GET':
        organizationSegment = Segment.objects.all()
        organizationBusiness = Business.objects.all()
        organizationDirectorBoard = DirectorBoard.objects.all()
        organizationAccountantArea = AccountantArea.objects.all()
        organizationProduct = Product.objects.all()
        organizationEletricGroup = ElectricalGrouping.objects.all()
        organizationProductionPhase = ProductionPhase.objects.all()

        serializer = OrganizationSegmentSerializerView(organizationSegment, many=True, context=serializer_context)
        serializerBusiness = OrganizationBusinessSerializerView(organizationBusiness, many=True,
                                                                context=serializer_context)
        serializerDirectorBoard = OrganizationDirectorBoardSerializerView(organizationDirectorBoard, many=True,
                                                                          context=serializer_context)
        serializerAccountantArea = OrganizationAccountSerializerView(organizationAccountantArea, many=True,
                                                                     context=serializer_context)
        serializerProduct = OrganizationProductSerializerView(organizationProduct, many=True,
                                                              context=serializer_context)
        serializerEletricGroup = OrganizationAgrupationEletrictSerializerView(organizationEletricGroup, many=True,
                                                              context=serializer_context)
        serializerProductionPhase = OrganizationProductionPhaseSerializerView(organizationProductionPhase, many=True,
                                                              context=serializer_context)

        total = serializer.data + serializerBusiness.data + serializerDirectorBoard.data \
            + serializerAccountantArea.data + serializerProduct.data + serializerEletricGroup.data + serializerProductionPhase.data
        return Response(total)

@api_view(['POST'])
@check_module(modules.organizational, [permissions.EDITN1])
def session_organizational_post(request, format=None):
    """
        create a new organization
    """
    observation_log = ""
    if 'observation_log' in request.data:
        observation_log = request.data['observation_log']

    serializer_context = {
        'request': request,
        'observation_log': observation_log
    }

    if request.method == 'POST':
        if 'data' in request.data and 'model' in request.data:
            data = request.data['data']
            model = request.data['model']
        else:
            raise serializers.ValidationError(translate_language_error('error_data_json_null', request) )

        
        if model == "1" or model == 1:  # AccountantArea
            serializer = OrganisationAccountantAreaSerializer(data=request.data['data'], context=serializer_context)
            if serializer.is_valid():
                valida_Description(request, data['description'], 1, 0)
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        elif model == "2" or model == 2:  # DirectorBoard
            serializer = OrganisationDirectorBoardSerializer(data=request.data['data'], context=serializer_context)
            if serializer.is_valid():
                valida_Description(request, data['description'], 2, 0)
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        elif model == "3" or model == 3:  # Business
            serializer = OrganisationBusinessSerializer(data=request.data['data'], context=serializer_context)
            if serializer.is_valid():
                valida_Description(request, data['description'], 3, 0)
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif model == "4" or model == 4:  # Product
            serializer = OrganisationProductSerializer(data=request.data['data'], context=serializer_context)
            if serializer.is_valid():
                valida_Description(request, data['description'], 4, 0)
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)

        if model == "5" or model == 5:  # Segment
            serializer = OrganisationSegmentSerializer(data=request.data['data'], context=serializer_context)
            if serializer.is_valid():
                valida_Description(request, data['description'], 5, 0)
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif model == "6" or model == 6:  # ElectricalGrouping
            serializer = OrganisationAgrupationEletrictSerializer(data=request.data['data'], context=serializer_context)
            if serializer.is_valid():
                valida_Description(request, data['description'], 6, 0)
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
        elif model == "7" or model == 7:  # ProductionPhase
            serializer = OrganizationProductionPhaseSerializer(data=request.data['data'], context=serializer_context)
            if serializer.is_valid():
                valida_Description(request, data['description'], 7, 0)
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)

        else:
            raise serializers.ValidationError(translate_language_error('error_type_not_exist', request) )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT'])
@check_module(modules.organizational, [permissions.EDITN1])
def session_organizational_put(request, pk, classe, format=None):
    """
        Retrieve, update or delete a specific organization.
    """
    observation_log = ""
    if 'observation_log' in request.data:
        observation_log = request.data['observation_log']

    serializer_context = {
        'request': request,
        'observation_log': observation_log
    }
    try:
        
        if classe == "1":  # AccountantArea
            organization = AccountantArea.objects.get(pk=pk)
        elif classe == "2":  # Director
            organization = DirectorBoard.objects.get(pk=pk)
        elif classe == "3":  # Business
            organization = Business.objects.get(pk=pk)
        elif classe == "4":  # Product
            organization = Product.objects.get(pk=pk)
        elif classe == "5":  # Segment
            organization = Segment.objects.get(pk=pk)
        elif classe == "6":  # ElectricalGrouping
            organization = ElectricalGrouping.objects.get(pk=pk)
        elif classe == "7":  # ProductionPhase
            organization = ProductionPhase.objects.get(pk=pk)
        else:
            raise serializers.ValidationError(translate_language_error('error_type_not_exist', request) )
    except:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'PUT':
        if 'data' in request.data and 'model' in request.data:
            data = request.data['data']
            model = request.data['model']
        else:
            raise serializers.ValidationError(translate_language_error('error_data_json_null', request) )

        if model == "1" or model == 1:  # AccountantArea
            serializer = OrganisationAccountantAreaSerializer(organization, data=request.data['data'],
                                                              context=serializer_context)
            if serializer.is_valid():
                valida_Description(request, data['description'], 1, pk)
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
        elif model == "2" or model == 2:  # DirectorBoard
            serializer = OrganisationDirectorBoardSerializer(organization, data=request.data['data'],
                                                             context=serializer_context)
            if serializer.is_valid():
                valida_Description(request, data['description'], 2, pk)
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
        elif model == "3" or model == 3:  # Business
            serializer = OrganisationBusinessSerializer(organization, data=request.data['data'],
                                                        context=serializer_context)
            if serializer.is_valid():
                valida_Description(request, data['description'], 3, pk)
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
        elif model == "4" or model == 4:  # Product
            serializer = OrganisationProductSerializer(organization, data=request.data['data'],
                                                       context=serializer_context)
            if serializer.is_valid():
                valida_Description(request, data['description'], 4, pk)
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
        elif model == "5" or model == 5:  # Segment
            serializer = OrganisationSegmentSerializer(organization, data=request.data['data'],
                                                       context=serializer_context)
            if serializer.is_valid():
                valida_Description(request, data['description'], 5, pk)
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)  
        elif model == "6" or model == 6:  # ElectricalGrouping
            serializer = OrganisationAgrupationEletrictSerializer(organization, data=request.data['data'],
                                                       context=serializer_context)
            if serializer.is_valid():
                valida_Description(request, data['description'], 6, pk)
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
        elif model == "7" or model == 7:  # ElectricalGrouping
            serializer = OrganizationProductionPhaseSerializer(organization, data=request.data['data'],
                                                       context=serializer_context)
            if serializer.is_valid():
                valida_Description(request, data['description'], 7, pk)
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            raise serializers.ValidationError(translate_language_error('error_type_not_exist', request) )
        
        return Response({translate_language_error('error_not_change', request) }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@check_module(modules.organizational, [permissions.VIEW, permissions.EDITN1])
def session_organizational_get_detail(request, pk, classe, format=None):
    """
        Retrieve, update or delete a specific organization.
    """
    observation_log = ""
    if 'observation_log' in request.data:
        observation_log = request.data['observation_log']

    serializer_context = {
        'request': request,
        'observation_log': observation_log
    }
    try:
        if classe == "1":  # AccountantArea
            organization = AccountantArea.objects.get(pk=pk)
        elif classe == "2":  # Director
            organization = DirectorBoard.objects.get(pk=pk)
        elif classe == "3":  # Business
            organization = Business.objects.get(pk=pk)
        elif classe == "4":  # Product
            organization = Product.objects.get(pk=pk)
        elif classe == "5":  # Segment
            organization = Segment.objects.get(pk=pk)
        elif classe == "6":  # ElectricalGrouping
            organization = ElectricalGrouping.objects.get(pk=pk)
        elif classe == "7":  # ProductionPhase
            organization = ProductionPhase.objects.get(pk=pk)
        else:
            raise serializers.ValidationError(translate_language_error('error_type_not_exist', request) )
    except:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        if classe == "1":  # Accountant Area
            serializer = OrganizationAccountSerializerView(organization, context=serializer_context)
            return Response(serializer.data)
        elif classe == "2":  # Director
            serializer = OrganizationDirectorBoardSerializerView(organization, context=serializer_context)
            return Response(serializer.data)
        elif classe == "3":  # Business
            serializer = OrganizationBusinessSerializerView(organization, context=serializer_context)
            return Response(serializer.data)
        elif classe == "4":  # Product
            serializer = OrganizationProductSerializerView(organization, context=serializer_context)
            return Response(serializer.data)
        elif classe == "5":  # Segment
            serializer = OrganizationSegmentSerializerView(organization, context=serializer_context)
            return Response(serializer.data)
        elif classe == "6":  # ElectricalGrouping
            serializer = OrganizationAgrupationEletrictSerializerView(organization, context=serializer_context)
            return Response(serializer.data)
        elif classe == "7":  # ProductionPhase
            serializer = OrganizationProductionPhaseSerializerView(organization, context=serializer_context)
            return Response(serializer.data)

@api_view(['GET'])
@check_module(modules.organizational, [permissions.VIEW, permissions.EDITN1])
def organization_find_file(request):
    if not (request.query_params.get('format_file', None) is None):
        format_file = request.query_params.get('format_file', None)
    else:
        return Response({'error': translate_language_error('error_format_file_csv_or_pdf', request) }, status=status.HTTP_400_BAD_REQUEST)

    #Retorna json com os dados ////INICIO
    reponse_finaly =function_find_basic(request)
    reponse_finaly_json=[]
    for entry in reponse_finaly:
        item_type = entry.__class__.__name__.lower()
        if isinstance(entry, Segment):
            serializer = OrganizationSegmentSerializerView(entry, context=request)
        elif isinstance(entry, Business):
            serializer = OrganizationBusinessSerializerView(entry, context=request)
        elif isinstance(entry, DirectorBoard):
            serializer = OrganizationDirectorBoardSerializerView(entry, context=request)
        elif isinstance(entry, AccountantArea):
            serializer = OrganizationAccountSerializerView(entry, context=request)
        elif isinstance(entry, Product):
            serializer = OrganizationProductSerializerView(entry, context=request)
        elif isinstance(entry, ElectricalGrouping):
            serializer = OrganizationAgrupationEletrictSerializerView(entry, context=request)
        elif isinstance(entry, ProductionPhase):
            serializer = OrganizationProductionPhaseSerializerView(entry, context=request)

        reponse_finaly_json.append({'item_type': item_type, 'data': serializer.data})
    #Retorna json com os dados ////FIM
    
    payload = reponse_finaly_json
    payload = json.dumps(payload, indent=4, default=str).encode('utf-8')
    rest = json.loads(payload)
    
    header = {
        'model': 'field_organization_type',
        'description': 'field_description',
        'status': 'field_organization_status'
    }
    header=translate_language_header(header, request)
    mapping = [
        'model', 
        'description', 
        'status'
    ]

    rest = generic_data_csv_list(rest, [])
    rest_data = []

    for index in range(len(rest)):
        if 'data' in rest[index] and rest[index]['data']:
            kwargs = rest[index]['data']
            new={
                'model': translate_language( ( validates_data_used_file(kwargs, ['model'], 0) ), request),
                'description': validates_data_used_file(kwargs, ['description'], 0),
                'status': translate_language("field_status_"+( validates_data_used_file(kwargs, ['status'], 0) ), request)
            }
            rest_data.append(new)
    try:
        if format_file == 'csv':
            return generic_csv(mapping, header, rest_data, translate_language('label_organizational_download', request) )
        elif format_file == 'xlsx':
            styles=[]
            return generic_xls(mapping, header, rest_data, translate_language('label_organizational_download', request), styles)
        elif format_file == 'pdf':
            return generic_pdf(mapping, header, rest_data, translate_language('label_organizational_download', request) )
        else:
            return Response({'error': translate_language_error('error_unknown_format_file', request)}, status=status.HTTP_400_BAD_REQUEST)
    except:  # pragma: no cover
        # just to protect endpoint
        return Response(translate_language_error('error_undefined', request), status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@check_module(modules.organizational, [permissions.VIEW, permissions.EDITN1])
def organization_log_basic(request, pk, classe, format=None):
    if request.method == 'GET':
        if classe == "1":  # AccountantArea
            kwargs = {'core': AccountantArea, 'core_pk': 'id_accountant', 'core+': [],
                      'child': []}
        
        elif classe == "2":  # DirectorBoard
            kwargs = {'core': DirectorBoard, 'core_pk': 'id_director', 'core+': [],
                      'child': []}

        elif classe == "3":  # Business
            kwargs = {'core': Business, 'core_pk': 'id_business', 'core+': [],
                      'child': []}

        elif classe == "4":  # Product
            kwargs = {'core': Product, 'core_pk': 'id_product', 'core+': [],
                      'child': []}

        elif classe == "5":  # Segment
            kwargs = {'core': Segment, 'core_pk': 'id_segment', 'core+': [],
                      'child': []}

        elif classe == "6":  # ElectricalGrouping
            kwargs = {'core': ElectricalGrouping, 'core_pk': 'id_electrical_grouping', 'core+': [],
                      'child': []}
        
        elif classe == "7":  # ProductionPhase
            kwargs = {'core': ProductionPhase, 'core_pk': 'id_production_phase', 'core+': [],
                      'child': []}

        
        return Response(generic_log_search_basic(generic_log_search(pk, **kwargs)) )
 
@api_view(['GET'])
@check_module(modules.organizational, [permissions.VIEW, permissions.EDITN1])
def show_values_organization(request, format=None):
    serializer = OrganizationSerializerView(OrganizationalType.objects.all().order_by('description'), many=True, context=request).data
    return Response(serializer, status=status.HTTP_200_OK)