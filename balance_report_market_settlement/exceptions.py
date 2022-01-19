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

class AlreadyConsolidated(APIException):
    status_code = 412
    default_detail = 'Balance is already consolidated.'
    default_code = 'already_consolidated'

class OutOfDate(APIException):
    status_code = 412
    default_detail = 'Balance is out of date.'
    default_code = 'out_of_date'

class PastDateLimit(APIException):
    status_code = 412
    default_detail = 'The limit date already passed.'
    default_code = 'past_date_limit'

class AlreadySaved(APIException):
    status_code = 412
    default_detail = 'Balance is already saved.'
    default_code = 'already_saved'

class NoGenerationSeasonality(APIException):
    status_code = 412
    default_detail = 'A generating unit does not have a registered generation seasonality.'
    default_code = 'no_generation_seasonality'

class NoGenerationLoss(APIException):
    status_code = 412
    default_detail = 'A generating unit has no associated losses.'
    default_code = 'no_generation_losses'

class EmptySeasonality(APIException):
    status_code = 412
    default_detail = 'A seasoned contract does not have seasonality registered.'
    default_code = 'contract_empty_seasonality'

class NoTransferContractPriorization(APIException):
    status_code = 412
    default_detail = 'A transfer contract does not have prioritization.'
    default_code = 'transfer_no_priorization'

class NoFlexibilityLimit(APIException):
    status_code = 412
    default_detail = 'A flexible contract does not have flexibility.'
    default_code = 'flexibility_no_limit'

class InvalidContract(APIException):
    status_code = 412
    default_detail = 'An invalid cliq contract is registered in the system.'
    default_code = 'invalid_contract'
