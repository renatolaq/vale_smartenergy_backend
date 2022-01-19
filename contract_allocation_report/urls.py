from uuid import uuid4
import sys
import logging

from django.urls import path, re_path
from rest_framework.response import Response
from rest_framework import routers
from rest_framework.decorators import api_view
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.exceptions import ValidationError, ErrorDetail
from django.core.exceptions import ObjectDoesNotExist
from .ErrorWithCode import ErrorWithCode
from rest_framework import status
from .views import list_contract_allocation_report, get_contract_allocation_report, \
    save_contract_allocation_report, get_contract_allocation_report_history, get_contract_allocation_report_revision, \
    activate_contract_allocation_report, deactivate_contract_allocation_report, generate_contract_allocation_report, \
    list_balance, list_balance_source_destination, consolidate_contract_allocation_report, manual_calculate_contract_allocation_report, \
    manual_save_contract_allocation_report


def http_method_handling(get=None, post=None, put=None, delete=None):
    @api_view(['POST', 'GET', 'PUT', 'DELETE'])
    def local(request, **kwargs):
        try:
            if request.method == "POST" and post != None:
                return post(request, **kwargs)
            elif request.method == "GET" and get != None:
                return get(request, **kwargs)
            elif request.method == "PUT" and put != None:
                return put(request, **kwargs)
            elif request.method == "DELETE" and delete != None:
                return delete(request, **kwargs)
            else:
                raise MethodNotAllowed(request.method)
        except MethodNotAllowed as ex:
            raise ex
        except ErrorWithCode as ex:
            error_id = uuid4()
            logging.error(f"Error while process request - error trace id ({error_id})",
                          exc_info=sys.exc_info())
            return Response({
                "id": error_id,
                "errors": ex.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        except ValidationError as ex:
            def get_error_detail(errors, source):
                ret = []
                if type(errors) is list:
                    for index, detail in enumerate(errors):
                        if(type(detail) is ErrorDetail):
                            ret.append({
                                "code": "INPUT_ERROR",
                                "source": source,
                                "message": f"The field value is invalid `{source}` ({detail.code})"
                            })
                        else:
                            for error in detail:
                                ret.extend(get_error_detail(
                                    detail[error], f"{source}/{index}/{error}"))
                else:
                    for error in errors:
                        ret.extend(get_error_detail(
                            errors[error], f"{source}/{error}"))
                return ret

            error_id = uuid4()
            logging.error(f"Error while process request - validation error - error trace id ({error_id})",
                          exc_info=sys.exc_info())

            errors = []
            for error in ex.args:
                errors.extend(get_error_detail(error, ""))

            return Response({
                "id": error_id,
                "errors": errors
            }, status=status.HTTP_400_BAD_REQUEST)
        except ObjectDoesNotExist as ex:
            error_id = uuid4()
            logging.error(f"Not found item in database - error trace id ({error_id})",
                          exc_info=sys.exc_info())

            return Response({
                "id": error_id,
                "errors": [
                    {
                        "code": "ITEM_NOT_FOUND",
                        "source": "",
                        "message": f"not found item in database - {ex.args[0]}"
                    }
                ]
            }, status=status.HTTP_404_NOT_FOUND)
        except:
            error_id = uuid4()
            logging.error(f"Unknown error while process request - error trace id ({error_id})",
                          exc_info=sys.exc_info())

            ex = sys.exc_info()[0]
            return Response({
                "id": error_id,
                "errors": [
                    {
                        "code": "UNKNOWN_ERROR",
                        "source": "",
                        "message": "An unhandled error occurred"
                    }
                ]
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    return local


urlpatterns = [
    path('v1/contractAllocationReport/', http_method_handling(
        get=list_contract_allocation_report,
        post=save_contract_allocation_report)),
    path('v1/contractAllocationReport/<int:id>', http_method_handling(
        get=get_contract_allocation_report,
        put=save_contract_allocation_report)),
    path('v1/contractAllocationReport/<int:id>/history', http_method_handling(
        get=get_contract_allocation_report_history)),
    path('v1/contractAllocationReport/<int:id>/revision/<int:revision>', http_method_handling(
        get=get_contract_allocation_report_revision)),
    path('v1/contractAllocationReport/<int:id>/activate', http_method_handling(
        put=activate_contract_allocation_report)),
    path('v1/contractAllocationReport/<int:id>/deactivate', http_method_handling(
        put=deactivate_contract_allocation_report)),
    path('v1/contractAllocationReport/generate/<int:year>/<int:month>/<int:balance>', http_method_handling(
        get=generate_contract_allocation_report)),
    path('v1/contractAllocationReport/balance/<int:year>/<int:month>', http_method_handling(
        get=list_balance)),
    path('v1/contractAllocationReport/balance/<int:id>/getSourcesDestinations', http_method_handling(
        get=list_balance_source_destination)),
    path('v1/contractAllocationReport/consolidate/<int:id>', http_method_handling(
        put=consolidate_contract_allocation_report)),
    path('v1/contractAllocationReport/manual/calculate', http_method_handling(
        post=manual_calculate_contract_allocation_report)),
    path('v1/contractAllocationReport/manual/calculate/<int:id>', http_method_handling(
        post=manual_calculate_contract_allocation_report)),
    path('v1/contractAllocationReport/manual', http_method_handling(
        post=manual_save_contract_allocation_report)),
    path('v1/contractAllocationReport/manual/<int:id>', http_method_handling(
        put=manual_save_contract_allocation_report)),
]
