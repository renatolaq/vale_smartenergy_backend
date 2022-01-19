from locales.pt_translate.pt import data as pt_language
from locales.en_translate.en import data as en_language


def get_language(request):
    language = 'pt'
    if 'HTTP_ACCEPT_LANGUAGE' in request.META and request.META['HTTP_ACCEPT_LANGUAGE']:
        language = request.META['HTTP_ACCEPT_LANGUAGE']
    return language


def translate_language_log(label, request):

    language = get_language(request)
    if language in ['en', 'en-US']:
        return ( en_language[label] if label in en_language else label )
    elif language == 'pt-BR':
        return ( pt_language[label] if label in pt_language else label )
    else:
        return ( pt_language[label] if label in pt_language else label )


def translate_language(label, request):
    language = get_language(request)
    if language in ['en', 'en-US']:
        return ( en_language[label] if label in en_language else "" )
    elif language == 'pt-BR':
        return ( pt_language[label] if label in pt_language else "" )
    else:
        return ( pt_language[label] if label in pt_language else "" )


def translate_language_error(label, request):

    language = get_language(request)
    if language in ['en', 'en-US']:
        return ( en_language[label] if label in en_language else "" )
    elif language == 'pt-BR':
        return ( pt_language[label] if label in pt_language else "" )
    else:
        return ( pt_language[label] if label in pt_language else "" )


def translate_language_header(header, request):

    language = get_language(request)
    header_tranlate = header

    if language in ['en', 'en-US']:
        for k, v in header.items():
            header_tranlate[k] = (en_language[v] if v in en_language else v)
    elif language == 'pt-BR':
        for k, v in header.items():
            header_tranlate[k] = (pt_language[v] if v in pt_language else v)
    else:  # default == pt
        for k, v in header.items():
            header_tranlate[k] = (pt_language[v] if v in pt_language else v)

    return header_tranlate


def translate_label(label, request):

    language = get_language(request)
    if language in ['en', 'en-US']:
        return en_language[label] if label in en_language else ''
    else:
        return pt_language[label] if label in pt_language else ''

def translate_label_by_request(label, request, default=""):
    language = get_language(request)

    return translate_label_by_language(label, language, default)

def translate_label_by_language(label, language, default=""):

    if language in ['en', 'en-US']:
        return en_language[label] if label in en_language else default
    else:
        return pt_language[label] if label in pt_language else default


def translate_logical_and(request):

    language = get_language(request)
    if language in ['en', 'en-US']:
        return 'and'
    return 'e'
