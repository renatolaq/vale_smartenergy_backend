import logging
import sys
from uuid import uuid4
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.exceptions import ErrorDetail, MethodNotAllowed, ParseError, PermissionDenied, ValidationError
from rest_framework.response import Response
from ..exception.ErroWithCode import ErrorWithCode


def http_method_handling(get=None, post=None, put=None, delete=None):
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
                    for index, detail in enumerate(errors):
                        if isinstance(detail, ErrorDetail):
                            ret.append({
                                "code": "INPUT_ERROR",
                                "source": source,
                                "message": f"The field value is invalid `{source}` ({detail.code})({str(detail)})"
                            })
                        elif isinstance(detail, str):
                            ret.append({
                                "code": "INPUT_ERROR",
                                "source": source,
                                "message": f"The field value is invalid `{source}` ({str(detail)})"
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
        except ParseError as ex:
            error_id = uuid4()
            logging.error(f"Unknown error while process request json- error trace id ({error_id})",
                          exc_info=ex)

            return Response({
                "id": error_id,
                "errors": [
                    {
                        "code": "JSON_PARSE_ERROR",
                        "source": "",
                        "message": f"An unhandled error occurred - {ex.args[0]}"
                    }
                ]
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
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
    
    api_methods = []
    if get:
        api_methods.append("GET")
    if post:
        api_methods.append("POST")
    if put:
        api_methods.append("PUT")
    if delete:
        api_methods.append("DELETE")

    return api_view(api_methods)(local)