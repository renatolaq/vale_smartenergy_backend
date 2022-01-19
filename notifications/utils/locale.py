def get_request_language(request):
    language = 'pt_BR'
    if 'HTTP_ACCEPT_LANGUAGE' in request.META and request.META['HTTP_ACCEPT_LANGUAGE']:
        language = request.META['HTTP_ACCEPT_LANGUAGE'].replace('-', '_')

    return language