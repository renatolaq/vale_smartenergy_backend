from gc import get_objects

from django.db.models import F
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework import status, viewsets

from rest_framework.response import Response
from rest_framework.serializers import DjangoValidationError

from .models import GlobalVariable, State, Unity, Variable
from .services.global_variables_service import (get_states_service, get_icmss_service, create_icms_service, update_icms_service, delete_icms_service, get_taxes_tariffs_service,
                                                create_update_taxes_tariffs_service, get_indexes_service, create_index_service, update_index_service, get_icms_logs_service, get_taxes_tariffs_logs_service, get_indexes_logs_service)
from .serializers import (ConflictError, GlobalVariablesSerializer,
                          StateSerializer)
from SmartEnergy.auth import check_permission, check_module
import SmartEnergy.auth.permissions as permissions
import SmartEnergy.auth.groups as groups
import SmartEnergy.auth.modules as modules


class GlobalVariablesViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Global Variable Point manipulation
    """
    pass


@api_view(['GET'])
@check_module(modules.global_variables, [permissions.VIEW, permissions.EDITN1])
def icms_logs(request, format=None):
    if request.method == 'GET':
        message, status = get_icms_logs_service()
        return Response(message, status)


@api_view(['GET'])
@check_module(modules.global_variables, [permissions.VIEW, permissions.EDITN1])
def taxes_tariffs_logs(request, format=None):
    if request.method == 'GET':
        message, status = get_taxes_tariffs_logs_service()
        return Response(message, status)


@api_view(['GET'])
@check_module(modules.global_variables, [permissions.VIEW, permissions.EDITN1])
def indexes_logs(request, format=None):
    if request.method == 'GET':
        message, status = get_indexes_logs_service()
        return Response(message, status)


@api_view(['GET'])
def states(request, format=None):
    if request.method == 'GET':
        message, status = get_states_service()
        return Response(message, status)


@api_view(['GET', 'POST', 'PUT', 'DELETE'])
def icms_aliquot(request, format=None):
    if request.method == 'GET':
        return get_icms_wrapper(request)
    elif request.method == 'POST':
        return post_icms_wrapper(request)
    elif request.method == 'PUT':
        return put_icms_wrapper(request)
    elif request.method == 'DELETE':
        return delete_icms_wrapper(request)


@check_module(modules.global_variables, [permissions.VIEW, permissions.EDITN1])
def get_icms_wrapper(request):
    message, status = get_icmss_service()
    return Response(message, status)


@check_module(modules.global_variables, [permissions.EDITN1])
def post_icms_wrapper(request):
    message, status = create_icms_service(request.data, request)
    return Response(message, status)


@check_module(modules.global_variables, [permissions.EDITN1])
def put_icms_wrapper(request):
    message, status = update_icms_service(request.data, request)
    return Response(message, status)


@check_module(modules.global_variables, [permissions.EDITN1])
def delete_icms_wrapper(request):
    message, status = delete_icms_service(request.data, request)
    return Response(message, status)


@api_view(['GET', 'POST', 'PUT', 'DELETE'])
def taxes_and_tariffs(request, format=None):
    if request.method == 'GET':
        return get_taxes_and_tariffs_wrapper(request)
    elif request.method == 'POST':
        return post_taxes_and_tariffs_wrapper(request)
    elif request.method == 'PUT':
        pass
    elif request.method == 'DELETE':
        pass


@check_module(modules.global_variables, [permissions.VIEW, permissions.EDITN1])
def get_taxes_and_tariffs_wrapper(request):
    message, status = get_taxes_tariffs_service()
    return Response(message, status)


@check_module(modules.global_variables, [permissions.EDITN1])
def post_taxes_and_tariffs_wrapper(request):
    message, status = create_update_taxes_tariffs_service(request.data, request)
    return Response(message, status)


@api_view(['GET', 'POST', 'PUT'])
def indexes(request, format=None):
    if request.method == 'GET':
        return get_indexes_wrapper(request)
    elif request.method == 'POST':
        return post_indexes_wrapper(request)
    if request.method == 'PUT':
        return put_indexes_wrapper(request)


@check_module(modules.global_variables, [permissions.VIEW, permissions.EDITN1])
def get_indexes_wrapper(request):
    message, status = get_indexes_service()
    return Response(message, status)


@check_module(modules.global_variables, [permissions.EDITN1])
def post_indexes_wrapper(request):
    message, status = create_index_service(request.data, request)
    return Response(message, status)


@check_module(modules.global_variables, [permissions.EDITN1])
def put_indexes_wrapper(request):
    message, status = update_index_service(request.data, request)
    return Response(message, status)
