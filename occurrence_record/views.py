from babel.core import Locale
from SmartEnergy.utils.request.get_request_locale import get_request_locale
from SmartEnergy.utils.deep_get_value import deep_get_value
from typing import Dict, List, Mapping
from django.db.models.expressions import Subquery
from .serializers import EventSerializer, EventTypeSerializer, OccurrenceAttachmentSerializer, \
    OccurrenceCauseSerializer, OccurrenceSerializer, OccurrenceTypeSerializer, AppliedProtectionSerializer
from rest_framework import status
from rest_framework.response import Response
from django.db.models import F
from django.db.models.functions import Trim
from django.db import connection, transaction
import collections
from babel.dates import format_datetime, get_timezone
from babel.numbers import format_decimal

from core.attachment_utility import generic_csv, generic_pdf, generic_xls
from core.views import  generic_queryset_filter_ex, generic_paginator, generic_log_search, only_number, \
    generic_log_search_basic, save_file
from locales.translates_function import translate_language_header, translate_language, translate_language_error
from SmartEnergy.auth import check_module
import SmartEnergy.auth.permissions as permissions
import SmartEnergy.auth.modules as modules
from consumption_metering_reports.utils import StrSQL

from occurrence_record.models import ManualEvent, Occurrence, Event, OccurrenceBusiness, OccurrenceProduct,\
    OccurrenceCause, OccurrenceType, AppliedProtection, EventType, OccurrenceAttachment
from company.models import Company
from company.serializersViews import CompanySerializerViewBasicData
from organization.serializersViews import OrganizationProductSerializerView, OrganizationBusinessSerializerView
from organization.models import Product, Business
from SmartEnergy.utils.exception.ErroWithCode import ErrorWithCode

@check_module(modules.occurrence_record, [permissions.VIEW, permissions.EDITN1, permissions.EDITN2])
def get_occurrence_list(request):
    data, page_count, page_next, page_previous = query_data(request)
    data = OccurrenceSerializer(data, many=True).data
    response_return = {
        'count': page_count,
        'next': page_next,
        'previous': page_previous,
        'results': data}
    return Response(response_return, status=status.HTTP_200_OK)


@check_module(modules.occurrence_record, [permissions.VIEW, permissions.EDITN1, permissions.EDITN2])
def get_company_list_with_participation_sepp(request):
    query = Company.objects.filter(
        gauge_company__participation_sepp='S',
        gauge_company__status='S').order_by('company_name').distinct()

    return Response(CompanySerializerViewBasicData(query, many=True).data, status=status.HTTP_200_OK)


@check_module(modules.occurrence_record, [permissions.VIEW, permissions.EDITN1, permissions.EDITN2])
def get_event_list(request):
    kwargs = {        
        'gauge_point': 'gauge_point__id_source__display_name__contains',
        'event_type': 'event_type',
        'utc_events_begin': 'utc_events_begin__gte',
        'utc_events_begin_end': 'utc_events_begin__lte',
        'utc_creation': 'utc_creation__gte',
        'utc_creation_end': 'utc_creation__lte',
        'events_duration': 'events_duration_rounded__startswith',
        'events_magnitude': 'events_magnitude_rounded__startswith',
        'type_usage_contract': 'type_usage_contract',
        'occurrence': {'field': 'occurrence_id', 'allow_null': True, 'converter': int},
        'start_date': 'utc_events_begin__gte',
        'end_date': 'utc_events_begin__lte',
        'company': 'gauge_point__id_company_id',
        'event_date': 'utc_events_begin__date',
    }
    kwargs_order = {
        'gauge_point': 'gauge_point__id_source__display_name',
        'event_type': 'event_type__name_event_type',
        'utc_events_begin': 'utc_events_begin',
        'utc_creation': 'utc_creation',
        'events_duration': 'events_duration',
        'events_magnitude': 'events_magnitude',
        'type_usage_contract': 'type_usage_contract',
        'event_date': 'utc_events_begin__date', 

        '-gauge_point': '-gauge_point__id_source__display_name',
        '-event_type': '-event_type__name_event_type',
        '-utc_events_begin': '-utc_events_begin',
        '-utc_creation': '-utc_creation',
        '-events_duration': '-events_duration',
        '-events_magnitude': '-events_magnitude',
        '-event_date': '-utc_events_begin__date',
        '-type_usage_contract': '-type_usage_contract',
    }

    order_by = kwargs_order['gauge_point']
    if request.query_params.get('ordering') in kwargs_order:
        order_by = kwargs_order[request.query_params.get('ordering')]

    query = Event.objects.filter(gauge_point__participation_sepp='S').annotate(events_duration_rounded=Trim(StrSQL(F('events_duration'), 21, 6)),
                           events_magnitude_rounded=Trim(StrSQL(F('events_magnitude'), 21, 6)))
    query = generic_queryset_filter_ex(request, query, **kwargs)
    query = query.annotate(events_duration_rounded=Trim(StrSQL(F('events_duration'), 21, 6)),
                           events_magnitude_rounded=Trim(StrSQL(F('events_magnitude'), 21, 6)))

    query = Event.objects.filter(
        id_event__in=Subquery(query.values('id_event')))

    query = query.order_by(order_by) \
        .select_related('gauge_point').select_related('gauge_point__id_company')\
        .select_related('gauge_point__id_source').select_related('gauge_point__id_source__id_meter_type')\
        .select_related('gauge_point__id_electrical_grouping').select_related('event_type')

    data, page_count, page_next, page_previous = generic_paginator(
        request, query)
    data = EventSerializer(data, many=True).data
    response_return = collections.OrderedDict([
        ('count', page_count),
        ('next', page_next),
        ('previous', page_previous),
        ('results', data)
    ])
    return Response(response_return, status=status.HTTP_200_OK)


@check_module(modules.occurrence_record, [permissions.VIEW, permissions.EDITN1, permissions.EDITN2])
def get_event_type_list(request):
    query = EventType.objects.all().order_by('name_event_type')
    return Response(EventTypeSerializer(query, many=True).data, status=status.HTTP_200_OK)


@check_module(modules.occurrence_record, [permissions.VIEW, permissions.EDITN1, permissions.EDITN2])
def get_applied_protection_list(request):
    query = AppliedProtection.objects.all().order_by('description')
    return Response(AppliedProtectionSerializer(query, many=True).data, status=status.HTTP_200_OK)


@check_module(modules.occurrence_record, [permissions.VIEW, permissions.EDITN1, permissions.EDITN2])
def get_occurrence_type_list(request):
    query = OccurrenceType.objects.all().order_by('description')
    return Response(OccurrenceTypeSerializer(query, many=True).data, status=status.HTTP_200_OK)


@check_module(modules.occurrence_record, [permissions.VIEW, permissions.EDITN1, permissions.EDITN2])
def get_occurrence_cause_list(request):
    query = OccurrenceCause.objects.all().order_by('description')
    return Response(OccurrenceCauseSerializer(query, many=True).data, status=status.HTTP_200_OK)


@check_module(modules.occurrence_record, [permissions.VIEW, permissions.EDITN1, permissions.EDITN2])
def get_valids_business_list(request):
    id_events = request.query_params.get('id_events', False)
    query = Business.objects.all()
    if id_events:
        query = query.filter(business_energyComposition__id_company__gauge_company__gaugePoint_pqEvents__in = id_events.split('|'))
    return Response(OrganizationBusinessSerializerView(query, many=True).data, status=status.HTTP_200_OK)


@transaction.atomic
@check_module(modules.occurrence_record, [permissions.EDITN1, permissions.EDITN2])
def save_occurrence(request, pk=None):
    serializer_context = {
        'request': request,
        'observation_log': request.data.get('observation_log', "") or ""
    }
    occurrence = Occurrence.objects.get(pk=pk) if pk else None

    ocurrence_serializer = OccurrenceSerializer(occurrence,
                                                data=request.data, context=serializer_context)
    ocurrence_serializer.is_valid(True)
    ocurrence_serializer.save()
    return Response(ocurrence_serializer.data, status=status.HTTP_200_OK if pk else status.HTTP_201_CREATED)


@check_module(modules.occurrence_record, [permissions.VIEW, permissions.EDITN1, permissions.EDITN2])
def get_occurrence(request, pk):
    occurrence = Occurrence.objects \
        .prefetch_related('events').prefetch_related('events__event_type').prefetch_related('events__type_usage_contract') \
        .prefetch_related('events__gauge_point').prefetch_related('events__gauge_point__id_electrical_grouping')\
        .prefetch_related('events__gauge_point__id_company').prefetch_related('events__gauge_point__id_source') \
        .prefetch_related('occurrence_business').prefetch_related('occurrence_business__business')\
        .prefetch_related('occurrence_product').prefetch_related('occurrence_product__product')\
        .get(pk=pk)

    return Response(OccurrenceSerializer(occurrence).data, status=status.HTTP_200_OK)


@check_module(modules.occurrence_record, [permissions.VIEW, permissions.EDITN1, permissions.EDITN2])
def get_occurrence_log(request, pk):
    def resolve_value(item):
        return item['value'] if isinstance(item, Mapping) else item

    kwargs = {'core': Occurrence,
              'core_pk': 'id_occurrence',
              'core+': [],
              'child': []}
    log = generic_log_search(pk, **kwargs)

    log['OCCURRENCE_BUSINESS'] = []
    for item_occu_business in OccurrenceBusiness.objects.filter(occurrence_id=pk):
        kwargs = {'core': OccurrenceBusiness,
                  'core_pk': 'id_occurrence_business',
                  'core+': [],
                  'child': []}
        log_occu_business = generic_log_search(item_occu_business.pk, **kwargs)
        for item_log in log_occu_business['OCCURRENCE_BUSINESS']:
            log['OCCURRENCE_BUSINESS'].append(item_log)

    log['OCCURRENCE_PRODUCT'] = []
    for item_occu_product in OccurrenceProduct.objects.filter(occurrence_id=pk):
        kwargs = {'core': OccurrenceProduct,
                  'core_pk': 'id_occurrence_product',
                  'core+': [],
                  'child': []}
        log_occu_product = generic_log_search(item_occu_product.pk, **kwargs)
        for item_log in log_occu_product['OCCURRENCE_PRODUCT']:
            log['OCCURRENCE_PRODUCT'].append(item_log)

    log['MANUAL_EVENTS'] = []
    for item_manual_event in ManualEvent.objects.filter(occurrence_id=pk):
        kwargs = {'core': ManualEvent,
                  'core_pk': 'id_manual_event',
                  'core+': [],
                  'child': []}
        log_manual_event = generic_log_search(item_manual_event.pk, **kwargs)
        for item_log in log_manual_event['PQ_EVENTS_MANUAL']:
            log['MANUAL_EVENTS'].append(item_log)

    log_response = generic_log_search_basic(log)

    list_ids_business = []
    list_ids_product = []
    for item in log_response: 
        if item['OCCURRENCE_BUSINESS']:
            def process(item_business):
                id_business = item_business['new_value']['business']
                list_ids_business.append(resolve_value(id_business))

            if type(item['OCCURRENCE_BUSINESS']) == list:
                for item_business in item['OCCURRENCE_BUSINESS']:
                    process(item_business)
            else:
                process(item['OCCURRENCE_BUSINESS'])

        if item['OCCURRENCE_PRODUCT']:
            def process(item_product):
                id_product = item_product['new_value']['product']
                list_ids_product.append(resolve_value(id_product))

            if type(item['OCCURRENCE_PRODUCT']) == list:
                for itemProduct in item['OCCURRENCE_PRODUCT']:
                    process(itemProduct)
            else:
                process(item['OCCURRENCE_PRODUCT'])        

    ids_events = []
    ids_applied_protections = []
    ids_occurrence_type = []
    ids_occurrence_cause = []
    ids_company = []
    for item in log_response: 
        def fix_register(data):
            if not "events" in data:            
                data['events'] = list(map(int, Event.objects.filter(
                    occurrence=data['id_occurrence']).values_list('id_event', flat=True)))
            
            if isinstance(data["events"], Mapping) and "until" in data["events"]:
                ids_events.extend(data['events']['value'])
            else:
                ids_events.extend(data['events'])

            if data.get('applied_protection'):
                ids_applied_protections.append(
                    resolve_value(data['applied_protection']))

            if data.get('occurrence_type'):
                ids_occurrence_type.append(
                    resolve_value(data['occurrence_type']))

            if data.get('occurrence_cause'):
                ids_occurrence_cause.append(
                    resolve_value(data['occurrence_cause']))

            if data.get('company'):
                ids_company.append(
                    resolve_value(data['company']))           

        if "old_value" in item['OCCURRENCE'] and item['OCCURRENCE']['old_value']:
            fix_register(item['OCCURRENCE']['old_value'])

        if "new_value" in item['OCCURRENCE'] and item['OCCURRENCE']['new_value']:
            fix_register(item['OCCURRENCE']['new_value'])

    related_business = OrganizationBusinessSerializerView(Business.objects.filter(
        pk__in=only_number(list_ids_business)), many=True, context=request).data
    related_products = OrganizationProductSerializerView(Product.objects.filter(
        pk__in=only_number(list_ids_product)), many=True, context=request).data
    applied_protections = AppliedProtectionSerializer(AppliedProtection.objects.filter(
        pk__in=only_number(ids_applied_protections)), many=True, context=request).data
    occurrence_types = OccurrenceTypeSerializer(OccurrenceType.objects.filter(
        pk__in=only_number(ids_occurrence_type)), many=True, context=request).data
    occurrence_causes = OccurrenceCauseSerializer(OccurrenceCause.objects.filter(
        pk__in=only_number(ids_occurrence_cause)), many=True, context=request).data
    companies = CompanySerializerViewBasicData(Company.objects.filter(
        pk__in=only_number(ids_company)), many=True, context=request).data
    events = Event.objects.filter(pk__in=only_number(ids_events)) \
        .select_related('event_type') \
        .select_related('gauge_point').select_related('gauge_point__id_electrical_grouping') \
        .select_related('gauge_point__id_company').select_related('gauge_point__id_source')
    events = EventSerializer(events, many=True, context=request).data

    kwargs = {'logs': log_response}
    kwargs['static_relateds'] = {
        "business": related_business,
        "product": related_products,
        "applied_protection": applied_protections,
        "occurrence_type": occurrence_types,
        "occurrence_cause": occurrence_causes,
        "companies": companies,
        "event": events
    }
    return Response(kwargs, status=status.HTTP_200_OK)


@check_module(modules.occurrence_record, [permissions.VIEW, permissions.EDITN1, permissions.EDITN2])
def get_occurrence_report(request):
    format_file = request.query_params.get('format_file', None)
    if format_file not in ["csv", "pdf", "xlsx"]:
        raise ErrorWithCode.from_error(
            "ERROR_FORMAT_FILE", "Invalid file format", "", details={"validFormats": ["csv", "pdf", "xlsx"]})

    query, _, _, _ = query_data(request)

    header = {
        'company_name': 'field_company_registration_occurrence',
        'occurrence_type': 'field_occurrence_type',
        'occurrence_date': 'field_occurrence_date',
        'electrical_grouping': 'field_electrical_grouping',
        'responsible': 'field_responsible',
        'phone': 'field_phone',
        'cellphone': 'field_cellphone',
        'carrier': 'field_carrier',
        'business': 'field_business',
        'key_circuit_breaker_identifier': 'field_key_circuit_breaker_identifier',
        'applied_protection': 'field_applied_protection',
        'occurrence_duration': 'field_occurrence_duration',
        'occurrence_cause': 'field_occurrence_cause',
        'total_stop_time': 'field_total_stop_time',
        'product': 'field_product',
        'lost_production': 'field_lost_production',
        'financial_loss': 'field_financial_loss',
        'description': 'field_description',
        'status': 'Status'
    }
    header = translate_language_header(header, request)
    mapping = [
        'company_name',
        'occurrence_type',
        'occurrence_date',
        'electrical_grouping',
        'responsible',
        'phone',
        'cellphone',
        'carrier',
        'business',
        'key_circuit_breaker_identifier',
        'applied_protection',
        'occurrence_duration',
        'occurrence_cause',
        'total_stop_time',
        'product',
        'lost_production',
        'financial_loss',
        'description',
        'status'
    ]
    
    formated_occurrences = []

    user_timezone = get_timezone(request.query_params.get('user_timezone', 'UTC'))
    locale = Locale.parse(request.query_params.get('locale') or get_request_locale(request), sep="-")
    format_date = lambda v: format_datetime(v, locale=locale, tzinfo=user_timezone, format="short")
    format_number = (lambda v: v) if format_file != 'pdf' else lambda v: format_decimal(v, locale=locale)
    
    for occurrence in query:
        formated = {
            'company_name': deep_get_value(occurrence, 'company.company_name'),
            'occurrence_type': deep_get_value(occurrence, 'occurrence_type.description'),
            'occurrence_date': deep_get_value(occurrence, 'occurrence_date', converter=format_date),
            'electrical_grouping': deep_get_value(occurrence, 'electrical_grouping.description'),
            'responsible': deep_get_value(occurrence, 'responsible'),
            'phone': deep_get_value(occurrence, 'phone'),
            'cellphone': deep_get_value(occurrence, 'cellphone'),
            'carrier': deep_get_value(occurrence, 'carrier'),
            'business': deep_get_value(occurrence, 'occurrence_business.0.business.description'),
            'key_circuit_breaker_identifier': deep_get_value(occurrence, 'key_circuit_breaker_identifier'),
            'applied_protection': deep_get_value(occurrence, 'applied_protection.description'),
            'occurrence_duration': deep_get_value(occurrence, 'occurrence_duration'),            
            'occurrence_cause': deep_get_value(occurrence, 'occurrence_cause_detail.description'),
            'total_stop_time': deep_get_value(occurrence, 'total_stop_time', converter=format_number),
            'product': deep_get_value(occurrence, 'occurrence_product.0.product.description'),
            'lost_production': deep_get_value(occurrence, 'occurrence_product.0.lost_production', converter=format_number),
            'financial_loss': deep_get_value(occurrence, 'occurrence_product.0.financial_loss', converter=format_number),
            'description': deep_get_value(occurrence, 'description'),
            'status': translate_language("field_status_"+(deep_get_value(occurrence, 'status')), request)
        }

        formated_occurrences.append(formated)

    if format_file == 'csv':
        return generic_csv(mapping, header, formated_occurrences, "report.csv")
    elif format_file == 'pdf':
        return generic_pdf(mapping, header, formated_occurrences, "report.pdf", landscape=True)
    else:
        styles = [
            {
                "fields": ['events_duration', 'events_magnitude'],
                "number_format": '#,##0.#######'
            },
            {
                "fields": ['lost_production'],
                "number_format": '#,##0.0000'
            },
            {
                "fields": ['financial_loss'],
                "number_format": 'R$ #,##0.0000'
            }
        ]
        return generic_xls(mapping, header, formated_occurrences, "report.xlsx", styles)


@check_module(modules.occurrence_record, [permissions.EDITN1, permissions.EDITN2])
def post_occurence_attachment(request, occurrence_id):
    serializer_context = {
        'request': request,
        'observation_log': ""
    }

    if 'attachment' in request.FILES:
        file = request.FILES['attachment']
        request.data['attachment_path'] = save_file(file)
    else:
        raise ErrorWithCode.from_error(
            "NO_FILE_UPLOADED", "No files uploaded", "/attachment")

    request.data['occurrence'] = occurrence_id
    serializer = OccurrenceAttachmentSerializer(
        data=request.data, context=serializer_context)
    serializer.is_valid(True)
    serializer.save()
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@check_module(modules.occurrence_record, [permissions.VIEW, permissions.EDITN1, permissions.EDITN2])
def get_occurence_attachment_list(request, occurrence_id):
    query = OccurrenceAttachment.objects.filter(
        occurrence_id=occurrence_id).order_by('attachment_name', 'attachment_revision')
    return Response(OccurrenceAttachmentSerializer(query, many=True).data)


@check_module(modules.occurrence_record, [permissions.VIEW, permissions.EDITN1, permissions.EDITN2])
def get_occurrence_dashboard(request):
    # GRAPH # 1=occurrence quantity /// 2=production downtime in hours
    # AGROUPING #4=Unity /// 1=electricalGrouping /// 3=OccurrenceType // GeneratorFact_variable=occurrencesPerGeneratingFactor
    def _function_format_data_graph(object_returned, graph_type, value_grouping):

        list_response_function = []
        if graph_type == 1:  # occurrence quantity
            key_graph = "num_occorence"
        else:  # production downtime in hours
            key_graph = "total_duration"

        if value_grouping == "GeneratorFact_variable":
            json_response = []
            count_total = 0
            for item_obj in object_returned:
                value_response = item_obj[key_graph]
                if value_response > 0:
                    pk_key_json = (
                        str(item_obj['pk']) if item_obj['pk'] else "0")
                    json_response.append({
                        "agrouping": translate_language("OCCURRENCE_CAUSE_PK_"+pk_key_json, request),
                        # key to translate grouping in frontEnd
                        "pk": "registrations_occurences.translate.occurrence_cause_pk_"+pk_key_json,
                        "value": value_response
                    })
                    count_total += value_response

            json_response.append({'name': 'total', 'count': count_total})
            list_response_function = json_response

        elif value_grouping == "3":
            json_response = []
            count_total = 0
            for value_pk in range(0, 4, 1):
                json_response.append({
                    "agrouping": translate_language("OCCURRENCE_TYPE_PK_"+str(value_pk), request),
                    # key to translate grouping in frontEnd
                    "pk": "registrations_occurences.translate.occurrence_type_pk_"+str(value_pk),
                    "value": 0
                })

            for item_obj in object_returned:
                value_response = item_obj[key_graph]
                pk_position_json = (
                    int(item_obj['pk']) if item_obj['pk'] else 0)

                json_response[pk_position_json]['value'] = value_response
                count_total += value_response

            json_response.append({'name': 'total', 'count': count_total})
            list_response_function = json_response

        else:
            list_ids_useds_function = []
            for object_posi in range(len(object_returned)):
                obj_extern = object_returned[object_posi]
                if not obj_extern['pk'] in list_ids_useds_function:
                    json_response = {
                        'agrouping': obj_extern['agrouping_name'] if obj_extern['agrouping_name'] else translate_language("WITHOUT_AGROUP", request),
                        "0": 0, "1": 0, "2": 0, "3": 0
                    }
                    count_total = 0
                    for item_intern in range(object_posi, len(object_returned), +1):
                        obj_intern = object_returned[item_intern]
                        if obj_extern['pk'] != obj_intern['pk']:
                            break
                        else:
                            value_response = obj_intern[key_graph]
                            if obj_intern['id_occurrence_type']:
                                json_response[str(
                                    obj_intern['id_occurrence_type'])] = value_response
                            else:
                                json_response['0'] = value_response

                            count_total += value_response

                    json_response['count'] = count_total
                    list_response_function.append(json_response)
                    list_ids_useds_function.append(obj_extern['pk'])

        return list_response_function

    def _insert_data_in_json(json_response, date_init, date_end):
        for item_json in json_response:
            if item_json == "chartOptionQuantityOccurrence":
                graph_type = 1
            elif item_json == "chartOptionTimeStopProduction":
                graph_type = 2

            if 'data' in json_response[item_json]['parametrization']:
                value = json_response[item_json]['parametrization']
                object_returned = my_custom_sql_graph(
                    value['grouping'], date_init, date_end)
                json_response[item_json]['parametrization'] = {
                    'data': _function_format_data_graph(object_returned, graph_type, value['grouping'])}

            if 'data' in json_response[item_json]['byGeneratorFact']:
                object_returned = my_custom_sql_graph(
                    "GeneratorFact_variable", date_init, date_end)
                json_response[item_json]['byGeneratorFact'] = {'data': _function_format_data_graph(
                    object_returned, graph_type, "GeneratorFact_variable")}

    def _create_json_dasboard(json_response):
        date_start = request.data.get('period', {}).get('start', None)
        date_end = request.data.get('period', {}).get('end', None)
        if date_start == None or len(date_start.split()) == 0\
                or date_end == None or len(date_end.split()) == 0:
            raise ErrorWithCode.from_error(
                "RANGE_DATE_REQUIRED", "Start/End dates required")

        for item_json in json_response:
            if item_json != "period" and item_json in ["chartOptionQuantityOccurrence", "chartOptionTimeStopProduction"] and not (json_response[item_json] is None):
                if json_response[item_json]['parametrization']['checked']:
                    value_if = json_response[item_json]['parametrization']
                    if value_if['type'] in ["0", "1"] and (value_if['grouping'] > "0" and value_if['grouping'] < "5"):
                        json_response[item_json]['parametrization']['data'] = []
                    else:
                        raise ErrorWithCode.from_error(
                            "GROUP_AND_TYPE_REQUIRED", "For this graphic group and type are required")

                if json_response[item_json]['byGeneratorFact']['checked']:
                    value_if = json_response[item_json]['byGeneratorFact']
                    if value_if['type'] in ["0", "1"]:
                        json_response[item_json]['byGeneratorFact']['data'] = []
                    else:
                        raise ErrorWithCode.from_error(
                            "TYPE_REQUIRED", "For this graphic type is required")

        json_response.pop('period')
        _insert_data_in_json(json_response, date_start, date_end)
        return True, json_response

    json_valid, json_returned = _create_json_dasboard(request.data)
    connection.queries
    if json_valid:
        return Response(json_returned, status=status.HTTP_200_OK)
    else:
        return Response(json_returned, status=status.HTTP_400_BAD_REQUEST)

def my_custom_sql_graph(type_graph, date_init, date_end):
    def dictfetchall(cursor):  # Return all rows from a cursor as a dict
        columns = [col[0] for col in cursor.description]
        return [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]

    row: list[dict] = None

    # occurrence quantity(Aggrouping_electrical) /// production downtime in hours(Aggrouping_electrical)
    if type_graph == "1":
        with connection.cursor() as cursor:
            cursor.execute(f"""
                SELECT distinct occurrence.id_electrical_grouping as pk, electricalGrouping.description as agrouping_name, 
                	   occurrence.id_occurrence_type,
                	   ISNULL(COUNT(occurrence.id_occurrence), 0) as 'num_occorence',
                	   ISNULL(SUM(occurrence.TOTAL_STOP_TIME), 0) as total_duration
                  FROM OCCURRENCE as occurrence
                 INNER JOIN ELECTRICAL_GROUPING as electricalGrouping
                    ON occurrence.id_electrical_grouping = electricalGrouping.id_electrical_grouping
                 WHERE occurrence.occurrence_date BETWEEN CONVERT(datetime2, '{date_init}', 127) AND CONVERT(datetime2, '{date_end}', 127) 
                   AND occurrence.STATUS='S'
                 GROUP BY occurrence.id_electrical_grouping, electricalGrouping.description, occurrence.id_occurrence_type
                 ORDER BY electricalGrouping.description, occurrence.id_occurrence_type""")
            row = dictfetchall(cursor)
        cursor.close()

    # occurrence quantity(business) /// production downtime in hours(business)
    elif type_graph == "2":
        with connection.cursor() as cursor:
            cursor.execute(f"""
                SELECT occurrence_business.id_business as pk,
                       business.description  as agrouping_name,
                       occurrence.id_occurrence_type ,
                       ISNULL(COUNT(occurrence.id_occurrence), 0) as 'num_occorence',
                       ISNULL(SUM(occurrence.TOTAL_STOP_TIME), 0) as total_duration
                  FROM OCCURRENCE_BUSINESS as occurrence_business
                 INNER JOIN BUSINESS as business
                    ON occurrence_business.id_business = business.id_business
                 INNER JOIN OCCURRENCE as occurrence
                    ON occurrence_business.ID_OCCURRENCE = occurrence.ID_OCCURRENCE
                 WHERE occurrence.occurrence_date BETWEEN CONVERT(datetime2, '{date_init}', 127) AND CONVERT(datetime2, '{date_end}', 127)  
                 GROUP BY occurrence_business.id_business, business.description,
                       occurrence.id_occurrence_type
                 ORDER BY occurrence_business.id_business, occurrence.id_occurrence_type""")
            row = dictfetchall(cursor)
        cursor.close()

    # occurrence quantity(OccurrenceType) or production downtime in hours(OccurrenceType)
    elif type_graph == "3":
        with connection.cursor() as cursor:
            cursor.execute(f"""
                SELECT occurrence.id_occurrence_type as pk,
                       ISNULL(COUNT(occurrence.id_occurrence), 0) as 'num_occorence',
                       ISNULL(SUM(occurrence.TOTAL_STOP_TIME), 0) as total_duration 
                  FROM OCCURRENCE as occurrence 
                 WHERE occurrence.occurrence_date BETWEEN CONVERT(datetime2, '{date_init}', 127) AND CONVERT(datetime2, '{date_end}', 127) 
                   AND occurrence.STATUS='S'
                 GROUP BY occurrence.id_occurrence_type
                 ORDER BY occurrence.id_occurrence_type""")
            row = dictfetchall(cursor)
        cursor.close()

    # occurrence quantity(Unity) /// production downtime in hours(Unity)
    elif type_graph == "4":
        with connection.cursor() as cursor:
            cursor.execute(f"""
                SELECT company.id_company as pk, company.company_name as agrouping_name,
                       occurrence.id_occurrence_type, occurrenceType.description,
                	   ISNULL(COUNT(occurrence.id_occurrence), 0) as 'num_occorence',
                	   ISNULL(SUM(occurrence.TOTAL_STOP_TIME), 0) as total_duration 
                  FROM OCCURRENCE as occurrence 
                  LEFT JOIN OCCURRENCE_TYPE as occurrenceType 
                    ON occurrence.id_occurrence_type = occurrenceType.id_occurrence_type 
                 INNER JOIN COMPANY as company 
                    ON occurrence.id_company = company.id_company 
                 WHERE occurrence.occurrence_date BETWEEN CONVERT(datetime2, '{date_init}', 127) AND CONVERT(datetime2, '{date_end}', 127)  
                   AND occurrence.STATUS='S' 
                 GROUP BY company.id_company, company.company_name, occurrence.id_occurrence_type, 
                       occurrenceType.description 
                 ORDER BY company.id_company, occurrence.id_occurrence_type""")
            row = dictfetchall(cursor)
        cursor.close()

    # number of occurrences per generating factor or downtime in hours by generating factor
    elif type_graph == "GeneratorFact_variable":
        with connection.cursor() as cursor:
            cursor.execute(f"""
                SELECT occurrence.id_occurrence_cause as pk,
                       ISNULL(COUNT(occurrence.id_occurrence), 0) as 'num_occorence',
                       ISNULL(SUM(occurrence.TOTAL_STOP_TIME), 0) as total_duration 
                  FROM OCCURRENCE as occurrence 
                 WHERE occurrence.occurrence_date BETWEEN CONVERT(datetime2, '{date_init}', 127) AND CONVERT(datetime2, '{date_end}', 127)    
                   AND occurrence.STATUS='S' 
                 GROUP BY occurrence.id_occurrence_cause
                 ORDER BY occurrence.id_occurrence_cause""")
            row = dictfetchall(cursor)
        cursor.close()

    return row

def query_data(request):
    kwargs = {
        'description': 'description__contains',
        'created_date': 'created_date__date',
        'status': 'status',
        'situation': 'situation__contains',
        'company': 'company__company_name__contains',
        'occurrence_type': 'occurrence_type__id_occurrence_type',
        'electrical_grouping': 'electrical_grouping__id_electrical_grouping',
        'responsible': 'responsible__contains',
        'applied_protection': 'applied_protection__id_applied_protection',
        'occurrence_cause': 'occurrence_cause__id_occurrence_cause',
        'occurrence_date': 'occurrence_date__date'
    }

    kwargs_order = {
        'description': 'description',
        'created_date': 'created_date',
        'status': 'status',
        'situation': 'situation',
        'company': 'company__company_name',
        'occurrence_type': 'occurrence_type__description',
        'electrical_grouping': 'electrical_grouping__description',
        'responsible': 'responsible',
        'applied_protection': 'applied_protection__description',
        'occurrence_cause': 'occurrence_cause__description',
        'occurrence_date': 'occurrence_date',
        '-description': '-description',
        '-created_date': '-created_date',
        '-status': '-status',
        '-situation': '-situation',
        '-company': '-company__company_name',
        '-occurrence_type': '-occurrence_type__description',
        '-electrical_grouping': '-electrical_grouping__description',
        '-responsible': '-responsible',
        '-applied_protection': '-applied_protection__description',
        '-occurrence_cause': '-occurrence_cause__description',
        '-occurrence_date': '-occurrence_date'
    }

    query = generic_queryset_filter_ex(request, Occurrence, **kwargs)

    order_by = kwargs_order['description']
    if request.query_params.get('ordering') in kwargs_order:
        order_by = kwargs_order[request.query_params.get('ordering')]
    query = query.order_by(order_by)

    query = query.prefetch_related('events').prefetch_related('events__event_type').prefetch_related('events__type_usage_contract') \
        .prefetch_related('events__gauge_point').prefetch_related('events__gauge_point__id_electrical_grouping')\
        .prefetch_related('events__gauge_point__id_company').prefetch_related('events__gauge_point__id_source') \
        .prefetch_related('occurrence_business').prefetch_related('occurrence_business__business')\
        .prefetch_related('occurrence_product').prefetch_related('occurrence_product__product')

    return generic_paginator(request, query)
