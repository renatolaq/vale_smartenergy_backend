from rest_framework.exceptions import APIException

class InternalError(APIException):
    status_code = 500
    default_detail = 'Something was wrong. Please contact the administrator.'
    default_code = 'internal_error'

class PreconditionFailed(APIException):
    status_code = 412
    default_detail = 'One or more precondition(s) were not satisfied.'
    default_code = 'precondition_failed'

class NotFound(APIException):
    status_code = 404
    default_detail = 'Data is not found.'
    default_code = 'not_found'

class AlreadySaved(APIException):
    status_code = 412
    default_detail = 'Report is already saved.'
    default_code = 'already_saved'
