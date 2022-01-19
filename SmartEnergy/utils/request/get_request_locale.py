def get_request_locale(request):
    return request.LANGUAGE_CODE or 'en-us'