from uuid import uuid4
import sys
import logging

from django.urls import path, re_path
from rest_framework import routers
from rest_framework.decorators import api_view
from rest_framework.exceptions import MethodNotAllowed, PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError
from django.core.exceptions import ObjectDoesNotExist
from .services.ErrorWithCode import ErrorWithCode
from .views import automatic_update_this_year_plan_monitoring, list_company_plan_monitoring, \
    update_company_plan_monitoring, get_plan_monitoring, \
    calculate_plan_monitoring, justify_plan_monitoring, create_plan_monitoring_from_budget, export_plan_monitoring, \
    create_all_plan_monitoring_from_budget


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
        except (MethodNotAllowed, PermissionDenied) as ex:
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
                    for detail in errors:
                        ret.append({
                            "code": "INPUT_ERROR",
                            "source": source,
                            "message": f"The field value is invalid `{source}` ({detail.code})"
                        })
                else:
                    for error in errors:
                        ret.extend(get_error_detail(errors[error], f"{source}/{error}"))
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
    path('v1/projectedmonitoring/',
         http_method_handling(get=list_company_plan_monitoring)),
    path('v1/projectedmonitoring/<int:id>',
         http_method_handling(put=update_company_plan_monitoring, get=get_plan_monitoring)),
    path('v1/projectedmonitoring/<int:id>/calculatePlanMonitoring',
         http_method_handling(post=calculate_plan_monitoring)),
    path('v1/projectedmonitoring/<int:id>/justify',
         http_method_handling(post=justify_plan_monitoring)),
    path('v1/projectedmonitoring/createOrUpdatePlanFromBudget/<int:company>/<int:year>',
         http_method_handling(get=create_plan_monitoring_from_budget)),
    path('v1/projectedmonitoring/export', http_method_handling(get=export_plan_monitoring)),
    path('v1/projectedmonitoring/all/updateRealized',
         http_method_handling(post=automatic_update_this_year_plan_monitoring)),
    path('v1/projectedmonitoring/createOrUpdatePlanFromBudget',
         http_method_handling(post=create_all_plan_monitoring_from_budget))
]
