from gauge_point.models import GaugeData
from global_variables.models import GlobalVariable
from company.models import Company
from manual_import.models import Ksb1, UploadFile
from django.db.models import Value
import json, re
from decimal import Decimal
from copy import deepcopy
from datetime import datetime, timedelta, date
from itertools import chain

from django.db import transaction
from django.db.models import F, Sum, DecimalField, CharField, Q
from django.db.models.expressions import OuterRef, Subquery
from django.db.models.query import QuerySet
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_404_NOT_FOUND, HTTP_403_FORBIDDEN, \
    HTTP_412_PRECONDITION_FAILED, HTTP_201_CREATED
from .models import CompanyReference, StatisticalIndex, CostType
from balance_report_market_settlement.models import Balance, DetailedBalance, MacroBalance, PriorizedCliq, Report
from agents.models import Agents
from energy_composition.models import EnergyComposition, ApportiomentComposition
from consumption_metering_reports.models import MeteringReportData, MeteringReportValue
from .serializers import IndexesDataSerializer, CompanyReferenceSerializer, StatisticalIndexSerializer, \
    SapSendSerialiazer
from .log_utils import LogUtils
from .utils import is_before_or_equal_nth_brazilian_workday, get_local_timezone, is_nth_brazilian_workday, \
    strip_accents, OldIndexesCheck, ChargebackCheck
from SmartEnergy.handler_logging import HandlerLog
from collections import namedtuple


class SAPService:
    def send_indexes_transaction(self, index):

        sap_values_queryset = index.results.filter(unity='kWh').values(
            'id_apport__id_energy_composition__cost_center').annotate(
            cost_center=F('id_apport__id_energy_composition__cost_center'),
            statistical_index=F('id_apport__volume_code'),
            value=Sum('value'),
            unity=F('unity')
        ).union(index.results.filter(unity='R$').values('id_apport__id_energy_composition__cost_center').annotate(
            cost_center=F('id_apport__id_energy_composition__cost_center'),
            statistical_index=F('id_apport__cost_code'),
            value=Sum('value'),
            unity=F('unity')
        ), all=True
        ).union(index.results.filter(unity='%').values('id_apport__id_energy_composition__cost_center').annotate(
            cost_center=F('id_apport__id_energy_composition__cost_center'),
            statistical_index=F('id_apport__volume_code'),
            value=Sum('value'),
            unity=F('unity')
        ), all=True)

        serialized_sap = SapSendSerialiazer(data=sap_values_queryset, many=True)
        serialized_sap.is_valid()

        sap_request = {
            'cost_financial_area': '123',
            'cost_centers_list': [
                serialized_sap.data
            ],
            'lauching_start_date': '2019-11-14T15:56:00.000',
            'lauching_end_date': '2019-11-14T15:56:00.000',
            'entrance_start_date': '2019-11-14T15:56:00.000',
            'entrance_end_date': '2019-11-14T15:56:00.000'
        }
        # TODO: endpoint to sap comes here
        sap_response = {
            "status": 501,
            "data": {
                "document_number": 1234,
                "message": "data received"
            }
        }

        return sap_response

    def send_reverse_transaction(self, report):
        queryset = CompanyReference.objects.all()
        serializer_class = CompanyReferenceSerializer
        document_number = report.sap_document_number
        sap_request = {
            'document_number': document_number
        }
        # TODO: endpoint to sap comes here
        sap_response = {
            "status": 503,
            "data": {
                "document_number": None,
                "message": "SAP service unavailable"
            }
        }

        return sap_response

    def get_statistical_indexes_from_sap(self, indexes_dict, logger):
        # TODO SAP request here
        '''
            4.1.5. INTEGRAÇÃO COM O SAP
            Ao clicar no botão para visualizar os dados, devemos
            solicitar os dados ao SAP, considerando a empresa, o tipo
            e o período selecionado;
        '''
        try:
            raise NotImplementedError('SAP integration hasn\'t been implemented.')
        except:
            logger.warning('SAP integration hasn\'t been implemented.')
            return []


class StatisticalIndexService:
    logger = HandlerLog()
    window_day = 1
    limit_hour = 15

    def generate_data(self, apportionment_composition_query, request, get_success_headers):
        params = request.data['params']
        company_id = params.get('company_id')
        index_type = params.get('index_type', 'A')
        opt = params.get('opt', '')
        year = params.get('year')
        month = params.get('month')
        data_result_vol = None
        serialized_data_cost = None
        total_cost = Decimal('0.000')
        CONVERSION_FACTOR_MWh_TO_kWh = 1000

        self.clear_temporary_index() # deleting old temporary indexes

        if index_type not in ['V', 'C', 'A']:
            return Response({"message": "error_invalid_index"}, HTTP_412_PRECONDITION_FAILED)

        if index_type not in ['V'] and opt not in ['1', '2']:
            return Response({"message": "error_cost_index_flag"}, HTTP_412_PRECONDITION_FAILED)

        company = Company.objects.get(pk=company_id)

        if not apportionment_composition_query.exists():
            return Response({"message": "error_no_apportionment_composition", "args": [company.company_name]},
                            HTTP_412_PRECONDITION_FAILED)

        # fixed apportionment rate 
        try:
            fixed_apportionment_rate_variable = GlobalVariable.objects.get(variable__name='TARIFA FIXA DE RATEIO')
        except GlobalVariable.DoesNotExist:
            return Response({"message": "error_fixed_rated_apprt_not_found"}, HTTP_412_PRECONDITION_FAILED)

        # Volume
        if company.type.upper() == 'I':
            try:
                balance_report = Report.objects.get(status='C', month=month, year=year,
                                                    report_type__initials__exact='BDE')
            except Report.DoesNotExist:
                return Response({"message": "error_no_consolidated_balance"}, HTTP_404_NOT_FOUND)

            if apportionment_composition_query:
                consumer_units = apportionment_composition_query.exclude(id_energy_composition__cost_center='1720032')

                # Fetching the consumed volume for the consumer units from the detailed report
                for apportionment_composition in consumer_units:
                    if apportionment_composition not in (None, ''):
                        cost_center = apportionment_composition.id_energy_composition.cost_center
                    else:
                        return Response({"message": "error_no_cost_center"}, HTTP_412_PRECONDITION_FAILED)

                    total_volume = MeteringReportValue.objects.filter(
                        metering_report_data__report__id__exact=balance_report.id_reference.id,
                        metering_report_data__id_company__id_company__exact=apportionment_composition.id_energy_composition.id_company.id_company
                    ).aggregate(Sum('total_consumption_loss'))['total_consumption_loss__sum'] or Decimal('0.0')

                    apportionment_composition.value = total_volume * CONVERSION_FACTOR_MWh_TO_kWh

                vale_apportionment = apportionment_composition_query.filter(id_energy_composition__cost_center='1720032')
                if not vale_apportionment.exists():
                    return Response({"message": "vale_cost_center_not_founded"}, HTTP_412_PRECONDITION_FAILED)

                # The calculation for the statistical index for the cost center 1720032 follow different rules
                # It is the sum of the energy sold by the Vale agent for the companies on buyers_profiles
                if vale_apportionment.exists():
                    vale_cost_center_1720032 = vale_apportionment.first()
                    vale_volume_indexes = []
                    CPBS_SAP_ID = ['1112']
                    SALOBO_SAP_ID = ['1064']
                    FERROUS_SAP_ID = ['1619', '1625']
                    try:
                        vale_profile_list = self.generate_profile_id_list(['1001'])
                        buyers_profiles = {
                            'Empresas Externas': self.generate_profile_id_list(CPBS_SAP_ID + SALOBO_SAP_ID + FERROUS_SAP_ID), #id's to exclude
                            'CPBS': self.generate_profile_id_list(CPBS_SAP_ID),
                            'Salobo': self.generate_profile_id_list(SALOBO_SAP_ID),
                            'Ferrous': self.generate_profile_id_list(FERROUS_SAP_ID)
                        }
                        detailed_balance_sold = DetailedBalance.objects.filter(
                            id_balance__id_balance_type__description__exact='PROFILE',
                            id_balance__id_report__pk__exact=balance_report.pk,
                            id_detailed_balance_type__description__exact='SALE'
                        )
                    except Exception as e:
                        return Response({"message": "agent_not_founded",
                                         "args": [str(e)]}, HTTP_412_PRECONDITION_FAILED)

                    detailed_balance_cliq_list = detailed_balance_sold.values_list('id_contract_cliq', flat=True)
                    cliqs_sold_by_vale_agent = PriorizedCliq.objects.filter(
                        id__in=detailed_balance_cliq_list,
                        id_vendor_profile__in=vale_profile_list,
                        id_report=balance_report.pk
                    ).exclude(
                        cliq_type='transferencia'
                    ).exclude(
                        double_status='I'
                    )

                    for associated_company, buyer_profiles in buyers_profiles.items():
                        buyer_profiles_filter = Q(id_buyer_profile__in=buyer_profiles)
                        if associated_company == 'Empresas Externas':
                            priorized_cliq_ids = cliqs_sold_by_vale_agent.exclude(buyer_profiles_filter)
                        else:
                            priorized_cliq_ids = cliqs_sold_by_vale_agent.filter(buyer_profiles_filter)

                        volume_sold_in_MWh = detailed_balance_sold.filter(
                            id_contract_cliq__in=priorized_cliq_ids
                        ).aggregate(Sum('volume'))['volume__sum'] or Decimal('0.0')

                        buyer_index = deepcopy(vale_cost_center_1720032)
                        buyer_index.value = volume_sold_in_MWh * CONVERSION_FACTOR_MWh_TO_kWh
                        buyer_index.associated_company = associated_company
                        vale_volume_indexes.append(buyer_index)

                    volume_results = list(chain(consumer_units, vale_volume_indexes))
                    serialized_data_vol = IndexesDataSerializer(data=volume_results, many=True)
                    serialized_data_vol.is_valid()
                    data_result_vol = serialized_data_vol.data[:]
        elif company.type.upper() == 'F':
            if apportionment_composition_query:
                for apport_composition in apportionment_composition_query:
                    border_comsumption = Decimal('0.0')
                    energy_composition = apport_composition.id_energy_composition
                    apport_composition.unit = '%'
                    cost_center = energy_composition.cost_center

                    if cost_center in (None, ''):
                        return Response({"message": "error_no_cost_center"}, HTTP_412_PRECONDITION_FAILED)

                    try:
                        total_consumption = self.kpi_formulae_resolver(energy_composition, month, year)

                        border = ApportiomentComposition.objects.get(
                            id_energy_composition__id_company__company_name=energy_composition.id_company.company_name,
                            id_company__type='I',
                            status__in=['S', 's', '1']
                        ).id_energy_composition
                        border_comsumption = self.kpi_formulae_resolver(border, month, year)
                    except ApportiomentComposition.MultipleObjectsReturned as e:
                        return Response({"message": "more_than_one_border_founded"}, HTTP_412_PRECONDITION_FAILED)
                    except ApportiomentComposition.DoesNotExist as e:
                        return Response({"message": "no_apportioment_composition_founded"}, HTTP_412_PRECONDITION_FAILED)
                    except GaugeData.DoesNotExist:
                        return Response({"message": "error_no_gauge_data"}, HTTP_412_PRECONDITION_FAILED)
                    except Exception as e:
                        return Response({"message": "error_invalid_kpi_formulae"}, HTTP_412_PRECONDITION_FAILED)

                    if total_consumption > Decimal('0.0') and border_comsumption > Decimal('0.0'):
                        # the value should be a percentage
                        energy_composition.value = (total_consumption / border_comsumption) * 100
                        apport_composition.value = energy_composition.value
                    else:
                        energy_composition.value = Decimal('0.0')
                        apport_composition.value = Decimal('0.0')

                serialized_data_vol = IndexesDataSerializer(data=apportionment_composition_query, many=True)
                serialized_data_vol.is_valid()
                data_result_vol = serialized_data_vol.data[:]
            else:
                return Response({"message": "error_energy_comp_not_found", "args": [company.company_name]},
                                HTTP_412_PRECONDITION_FAILED)

        # Cost
        if company.type.upper() == 'I' and index_type in ['C', 'A']:
            cost_results = []
            # total cost of area
            try:
                last_upload_file = UploadFile.objects \
                    .filter(ksb1__time_period=month, ksb1__exercise=year) \
                    .order_by("date_upload").last()

                KSB1_data = Ksb1.objects.filter(
                    cost_center__startswith='172',
                    cost_element__startswith='50',
                    time_period=month,
                    exercise=year,
                    upload_file = last_upload_file
                ) \
                .exclude(cost_center__in=['1720012', '1720030', '1720031']) \
                .exclude(cost_element__exact='5090500002')

            except Ksb1.DoesNotExist or UploadFile.DoesNotExist:
                return Response({"message": "error_total_cost_calculation"}, HTTP_412_PRECONDITION_FAILED)

            if not KSB1_data.exists():
                return Response({"message": "error_no_KSB1_data"}, HTTP_412_PRECONDITION_FAILED)

            ct = sum(filter(None, KSB1_data.values_list('mr_value', flat=True)))
            total_cost = ct

            if opt == '1':
                # summation consumer unit costs
                sum_cuc = Decimal('0.0')

                for apportionment_composition in consumer_units:
                    consumer_cost = (apportionment_composition.value / CONVERSION_FACTOR_MWh_TO_kWh) * fixed_apportionment_rate_variable.value
                    sum_cuc += consumer_cost
                    apportionment_composition.value = consumer_cost
                    apportionment_composition.unit = 'R$'

                if vale_apportionment.exists():
                    vale_cost_index = deepcopy(vale_cost_center_1720032)
                    vale_cost_index.value = ct - sum_cuc
                    vale_cost_index.unit = 'R$'

                cost_results = list(chain(consumer_units, [vale_cost_index]))

            elif opt == '2':
                # this sum should take into consideration the 1720032 cost center
                sum_volume = sum(apprt_composition.value for apprt_composition in volume_results)
                if sum_volume:
                    tfr_opt2 = ct / sum_volume
                else:
                    tfr_opt2 = Decimal('0.0')

                for apportionment_composition in volume_results:
                    apportionment_composition.value *= tfr_opt2
                    apportionment_composition.unit = 'R$'

                cost_results = volume_results

            serialized_data_cost = IndexesDataSerializer(data=cost_results, many=True)
            serialized_data_cost.is_valid()

        # Volume
        if index_type == 'V' and not data_result_vol is None:
            index_data_list = data_result_vol
        # Cost
        elif index_type == 'C' and not serialized_data_cost is None:
            index_data_list = serialized_data_cost.data
        # Both
        elif index_type == 'A':
            if not data_result_vol is None and not serialized_data_cost is None:
                data_result_vol.extend(serialized_data_cost.data)
                index_data_list = data_result_vol
            elif not data_result_vol is None and serialized_data_cost is None:
                index_data_list = data_result_vol
            elif data_result_vol is None and not serialized_data_cost is None:
                index_data_list = serialized_data_cost.data
            else:
                index_data_list = None
        else:
            index_data_list = None

        index_name = self.create_index_name(f'IE_{index_type}', month, year)

        if index_data_list is None:
            return Response({f"message": "error_generating_index"}, HTTP_412_PRECONDITION_FAILED)

        creation_date = datetime.utcnow()
        # check if do not exists another index from the same company, type and date and create in database if doesn't exists
        serializer_create_data = {
            "id_company": company_id,
            "transaction_type": index_type,
            "month": month,
            "year": year,
            "index_name": index_name,
            "creation_date": creation_date,
            "status": "0",
            "cost_type": opt if opt in CostType.values() else None,
            "total_cost": round(total_cost, 8) if opt in CostType.values() else None,
            "results": index_data_list
        }

        serializer = CompanyReferenceSerializer(data=serializer_create_data)

        serializer.is_valid(raise_exception=True)
        validated_indexes = []

        try:
            with transaction.atomic():

                serializer.save(status="0", index_name=index_name)

                for index_data in index_data_list:
                    serializer_data = {
                        "id_reference": Decimal(serializer.data.get("id")),
                        "value": index_data.get("value"),
                        "unity": index_data.get("unit"),
                        "id_apport": index_data.get("id_apport"),
                        "associated_company": index_data.get("associated_company")
                    }
                    index_serializer = StatisticalIndexSerializer(data=serializer_data)
                    index_serializer.is_valid(raise_exception=True)
                    validated_indexes.append(index_serializer)

                for validated_index in validated_indexes:
                    validated_index.save()

            headers = get_success_headers(serializer.data)
            index = serializer.instance

            return Response(CompanyReferenceSerializer(index).data, status=HTTP_201_CREATED, headers=headers)
        except EnergyComposition.DoesNotExist as e:
            return Response({"message": "error_no_cost_center"}, HTTP_412_PRECONDITION_FAILED)

    def create_index_name(self, initials, month, year):
        """Create the statistical index name"""
        existing_indexes = CompanyReference.objects.filter(
                month=month, 
                year=year
            ).exclude(
                status__in=['0']
            ).values('index_name').distinct().count()
        sequential = 0
        if existing_indexes != 999:
            sequential = 1 + existing_indexes
        return f'{initials}_{str(month).zfill(2)}_{str(year).zfill(4)}_{str(sequential).zfill(3)}'

    def kpi_formulae_resolver(self, energy_composition, month, year):
        total_consumption = Decimal('0.0')
        kpi_formulae = energy_composition.kpi_formulae

        # Replace formule values
        for formulae in re.finditer(r'(?:\{(?P<express>[^}{]+)\})', kpi_formulae.replace('\"', '')):
            formulae = formulae.groupdict()
            if 'express' in formulae:
                express_json = re.sub(r'(?i)([\w_\-\d]+)\:', r'"\1":', formulae['express'])
                express_dic = json.loads('{' + express_json.replace('\'', '"') + '}')
                if 'id' in express_dic:
                    id_gauce = express_dic['id']
                    sum_gauge = GaugeData.objects.filter(
                        id_gauge=id_gauce,
                        utc_gauge__year=year,
                        utc_gauge__month=month,
                        id_measurements__measurement_name__exact='Active Energy CCEE'
                    ).aggregate(Sum('value'))['value__sum'] or 0.0
                    kpi_formulae = kpi_formulae.replace(formulae['express'], str(sum_gauge)) \
                        .replace('{', '(') \
                        .replace('}', ')')
        value = Decimal(eval(kpi_formulae))
        total_consumption += value
        energy_composition.value = value
        return total_consumption

    def filter_indexes(self, indexes_dict, key, value):
        response = []
        for item in indexes_dict:
            if strip_accents(str(value)).lower() in strip_accents(str(item[key])).lower():
                response.append(item)
        return response

    def get_statistical_indexes_filtered_ordered(self, indexes_dict, request):
        unity = request.query_params.get('unity', None)
        if unity:
            indexes_dict = self.filter_indexes(indexes_dict, 'unity', unity)

        cost_center = request.query_params.get('cost_center', None)
        if cost_center:
            indexes_dict = self.filter_indexes(indexes_dict, 'cost_center', cost_center)

        statistic_index = request.query_params.get('statistic_index', None)
        if statistic_index:
            indexes_dict = self.filter_indexes(indexes_dict, 'statistic_index', statistic_index)

        formatted_value = request.query_params.get('formatted_value', None)
        if formatted_value:
            formatted_value = formatted_value.replace('.', 'temp').replace(',', '.').replace('temp', '')
            indexes_dict = self.filter_indexes(indexes_dict, 'formatted_value', formatted_value)

        associated_company = request.query_params.get('associated_company', None)
        if associated_company:
            indexes_dict = self.filter_indexes(indexes_dict, 'associated_company', associated_company)

        ordenation_field = request.query_params.get('ordering', 'cost_center')

        desc = ordenation_field.startswith('-')
        ordenation_field = ordenation_field if not ordenation_field.startswith('-') else ordenation_field[
                                                                                         1:len(ordenation_field)]

        if ordenation_field == 'formatted_value':
            indexes_dict = sorted(indexes_dict, key=lambda k: Decimal(k[ordenation_field]), reverse=desc)
        else:
            indexes_dict = sorted(indexes_dict, key=lambda k: strip_accents(str(k[ordenation_field])).lower(),
                                  reverse=desc)
        return indexes_dict

    def send_index(self, request, index):

        if not self.check_window_time(index):
            return Response({"message": "error_send_past_workday_limit"}, HTTP_412_PRECONDITION_FAILED)

        if index.total_cost and (index.total_cost < Decimal('0')):
            return Response({"message": "msg_total_cost_netative_value"}, HTTP_412_PRECONDITION_FAILED)

        negative_items = index.results.filter(value__lt=Value(Decimal('0')))
        if negative_items.exists():
            return Response({
                "message": "msg_generated_indexes_have_negative_value",
                "args": [', '.join(map(lambda company: str(company[0]), negative_items.values_list('associated_company')))]
                }, HTTP_412_PRECONDITION_FAILED)

        old_indexes_check = self.check_exist_valid(index)
        if old_indexes_check.status == OldIndexesCheck.NO_CHARGEBACK:
            return Response({"message": "error_index_already_sent"}, HTTP_403_FORBIDDEN)
        elif old_indexes_check.status == OldIndexesCheck.UNFINISHED_CHARGEBACK:
            return Response({"message": "error_unfinished_chargeback", 
                            "args": [old_indexes_check.index_name]}, HTTP_403_FORBIDDEN)
        
        index.status = 1
        index.save()

        # send the data to sap
        sap_service = SAPService()
        sap_response = sap_service.send_indexes_transaction(index)

        # change the status acordigly to sap return
        if sap_response["status"] == 200:
            index.status = "2"  # transaction finished
            index.sap_document_number = sap_response["data"]["document_number"]
        else:
            index.status = "3"  # communication failed

        # update the database entry
        index.save()
        log = LogUtils()
        log.save_log(index.pk, index._meta.db_table, CompanyReferenceSerializer(index).data,
                        observation=sap_response, request=request)

        if not sap_response['status'] == HTTP_200_OK:
            return Response({"message": "error_sap_communication"}, status=sap_response['status'])

        return Response(CompanyReferenceSerializer(index).data, status=HTTP_201_CREATED)

    def reverse_index(self, get_object, get_serializer, request):
        instance = get_object()
        serializer = get_serializer(instance)
        observation = request.query_params.get('observation_logs', '')
        date = datetime.now(get_local_timezone())

        if not self.check_window_time(instance):
            return Response({"message": "error_chargeback_past_workday_limit"}, HTTP_412_PRECONDITION_FAILED)

        new_instance = deepcopy(instance)
        new_instance.pk = None
        new_instance.status = "5"
        new_instance.creation_date = date
        new_instance.save()
        instance.status = "5"
        instance.save()

        statistical_indexes = StatisticalIndex.objects.filter(id_reference_id=instance.pk)
        for statistical_index in statistical_indexes:
            statistical_index.pk = None
            statistical_index.id_reference = new_instance
            statistical_index.save()

        sap_service = SAPService()
        sap_response = sap_service.send_reverse_transaction(instance)

        if sap_response["status"] == 200:
            new_instance.status = "6"
            new_instance.sap_document_number = sap_response["data"]["document_number"]
        else:
            new_instance.status = "7"
            new_instance.sap_document_number = None

        new_instance.save()
        log = LogUtils()
        log.save_log(instance.pk, instance._meta.db_table,
                     serializer.data, action_type="DELETE", observation=observation, request=request)

        new_serializer = get_serializer(new_instance)
        new_log = LogUtils()
        new_log.save_log(new_instance.pk, new_instance._meta.db_table,
                         new_serializer.data, action_type="UPDATE", observation=observation, request=request)

        if not sap_response['status'] == HTTP_200_OK:
            return Response({"message": "error_sap_communication"}, sap_response['status'])

        return Response(CompanyReferenceSerializer(new_instance).data, HTTP_200_OK)

    def resend_index(self, get_object, get_serializer, request):
        instance = get_object()

        if not self.check_window_time(instance):
            return Response({"message": "error_send_past_workday_limit"}, HTTP_412_PRECONDITION_FAILED)
        
        if instance.status in ['3', '7', '9']:
            sap_document_number = request.data.get('sap_document_number', '')
            status = '4' if instance.status in ['3', '9'] else '8'
            instance.sap_document_number = sap_document_number
            instance.status = status
            instance.save()
            serializer = get_serializer(instance)
            log = LogUtils()
            log.save_log(instance.pk, instance._meta.db_table,
                         serializer.data, action_type="UPDATE", request=request)
            return Response(CompanyReferenceSerializer(instance).data, HTTP_200_OK)
        else:
            return Response({"message": "error_invalid_status_update"}, HTTP_403_FORBIDDEN)
    
    def save_index(self, get_object, get_serializer, request):
        TEMPORARY_STATUS = "0"
        instance = get_object()

        if not self.check_window_time(instance):
            return Response({"message": "error_save_indexes_past_workday_limit"}, HTTP_412_PRECONDITION_FAILED)
        
        if self.saved_indexes_check(instance):
            return Response({"message": "error_already_saved_index"}, HTTP_412_PRECONDITION_FAILED)

        if instance.total_cost and (instance.total_cost < Decimal('0')):
            return Response({"message": "msg_save_total_cost_netative_value"}, HTTP_412_PRECONDITION_FAILED)

        negative_items = instance.results.filter(value__lt=Value(Decimal('0')))
        if negative_items.exists():
            return Response({
                "message": "msg_save_indexes_have_negative_value",
                "args": [', '.join(map(lambda company: str(company[0]), negative_items.values_list('associated_company')))]
                }, HTTP_412_PRECONDITION_FAILED)

        if instance.status != TEMPORARY_STATUS:
            return Response({"message": "error_invalid_status_update"}, HTTP_403_FORBIDDEN)

        old_indexes_check = self.check_exist_valid(instance)
        if old_indexes_check.status == OldIndexesCheck.NO_CHARGEBACK:
            return Response({"message": "error_index_already_sent"}, HTTP_403_FORBIDDEN)
        elif old_indexes_check.status == OldIndexesCheck.UNFINISHED_CHARGEBACK:
            return Response({"message": "error_unfinished_chargeback", 
                            "args": [old_indexes_check.index_name]}, HTTP_403_FORBIDDEN)
        
        observation = request.query_params.get('observation_logs', 'Salvar índice (Save index).')

        instance.status = "9" # saved status had to be 9 because it was added later
        instance.save()

        serializer = get_serializer(instance)

        log = LogUtils()
        log.save_log(instance.pk, instance._meta.db_table,
                     serializer.data, action_type="UPDATE", observation=observation, request=request)
        return Response(serializer.data, HTTP_200_OK)

    def generate_profile_id_list(self, agent_sap_id_list):
        """
        Given a list with SAP id associated to an Agent's Comapany returns a list of all 
        profiles' ids associated to it

        Arguments:
        agent_sap_id_list - List of SAP ids 
        """
        agent_list = Agents.objects.prefetch_related('profile_agent').filter(
            status='S',
            id_company__id_sap__in=agent_sap_id_list
        )
        if not agent_list.exists():
            raise Exception(", ".join(id for id in agent_sap_id_list))

        profile_list = self.generate_profile_list_from_agent_queryset(agent_list)
        return profile_list

    def generate_profile_list_from_agent_queryset(self, agent_queryset):
        """
        Given an agent_queryset it returns a list of all associated profile ids
        """
        profile_list = []
        for agent in agent_queryset:
            profile_list.extend(agent.profile_agent.all().values_list('id_profile', flat=True))
        return profile_list

    def check_exist_valid(self, index):
        """
        Checks if there are indexes already sent to SAP that haven't been charge chargebacked.

        :return: ChargebackCheck with a status and the index name. The possible statuses are:
            UNFINISHED_CHARGEBACK: there is an index sent to SAP whose chargeback hansn't been completed
            NO_CHARGEBACK: there is an index sent to SAP with no chargeback
            OK: there are no indexes sent to SAP or the index chargeback has been completed
        """

        SENT_TO_SAP = ['1', '2', '3', '4']
        CHARGEBACK = ['5', '6', '7', '8']
        UNFINISHED_CHARGEBACK = ['5', '7']

        indexes_sent_to_sap = CompanyReference.objects.filter(
            id_company=index.id_company,
            month=index.month,
            year=index.year,
            transaction_type__in=[index.transaction_type, 'A'],
            status__in=SENT_TO_SAP + UNFINISHED_CHARGEBACK
        ).exclude(
            pk=index.id
        )

        if indexes_sent_to_sap.exists():
            for current_index in indexes_sent_to_sap:
                index_chargeback = CompanyReference.objects.filter(
                    index_name=current_index.index_name,
                    status__in=UNFINISHED_CHARGEBACK
                )

                if not (current_index.status in UNFINISHED_CHARGEBACK):
                    index_chargeback = index_chargeback.exclude(pk=current_index.id)

                if not index_chargeback.exists():
                    return ChargebackCheck(OldIndexesCheck.NO_CHARGEBACK, current_index.index_name)

                if index_chargeback.count() == 2:
                    return ChargebackCheck(OldIndexesCheck.UNFINISHED_CHARGEBACK, current_index.index_name)
        
        return ChargebackCheck(OldIndexesCheck.OK, index.index_name)

    def saved_indexes_check(self, index):
        """Checks if there are saved indexes for a given company, month and year"""
        SAVED = '9'
        saved_indexes = CompanyReference.objects.filter(
            id_company=index.id_company,
            month=index.month,
            year=index.year,
            transaction_type__in=[index.transaction_type, 'A'],
            status=SAVED
        )
        return saved_indexes.exists()

    def check_window_time(self, index):
        date = datetime.now(get_local_timezone())
        is_current_month = (index.year == date.year and index.month == date.month)
        is_before_nth_day = True
        if index.month < 12:
            is_before_nth_day = is_before_or_equal_nth_brazilian_workday(index.year, index.month + 1, self.window_day)
        else:
            is_before_nth_day = is_before_or_equal_nth_brazilian_workday(index.year + 1, 1, self.window_day)
        return (is_current_month or
                (is_before_nth_day or
                 (is_nth_brazilian_workday(date, self.window_day) and date.hour <= self.limit_hour)))

    def clear_temporary_index(self):
        """Selecting temporary indexes (status = 0) which are older than 1 hour"""
        datetime_now = datetime.now(get_local_timezone())
        delta_time = 1
        try:
            temp_company_reference = CompanyReference.objects.filter(
                status__exact='0',
                creation_date__lte=(datetime_now - timedelta(hours=delta_time))
            )
            count = len(temp_company_reference)
            if count > 0:
                try:
                    for reference in temp_company_reference:
                        # Getting the statistical indexes entries that are related to the specific reference
                        index = reference.results.all()
                        index.delete()
                    temp_company_reference.delete()
                    detail = f'[{count}] statistical index(es) were removed.'
                    self.logger.info(detail)
                except Exception as e:
                    detail = f'ERROR: clear_temporary_index failed: {str(e)}'
                    self.logger.error(detail)
        except Exception as e:
            detail = f'ERROR: clear_temporary_index failed: {str(e)}'
            self.logger.error(detail)

    def generate_and_sender_statistical_indexes(self, request, get_success_headers):
        """
        Checks if it is the first work day of the month only on weekdays, if it is, checks if there is
        a statistical indexes saved last month, if there isn't a saved statistical indexes saves a new statistical
        indexes and send it.
        """
        DEACTIVATED = ['0', 'n', 'N']
        INTERNAL = 'I'
        SUBSIDIARY = 'F'
        DAYS = 1
        datetime_now = datetime.now(get_local_timezone())

        # Check if is the spected workday
        if datetime_now.month == 1:
            indexes_date = date(int(datetime_now.year) - 1, 12, 1)
        else:
            indexes_date = date(int(datetime_now.year), int(datetime_now.month) - 1, 1)

        # Get companies
        try:
            companies_id = ApportiomentComposition.objects.filter(status='S').values('id_company_id').distinct()
            companies = Company.objects.all().exclude(
                status__in=DEACTIVATED
            ).filter(
                pk__in=companies_id,
                type__in=[INTERNAL, SUBSIDIARY]
            ).order_by('company_name')

        except Company.DoesNotExist:
            self.logger.error("ERROR: No companies found in database.")
            return

        for company in companies:
            # Check if you have a statistical index sent in the previous month
            active = ['1', '2', '3', '4']
            statistical_indexes = StatisticalIndex.objects.filter(
                id_reference__month__exact=indexes_date.month,
                id_reference__year__exact=indexes_date.year,
                id_reference__id_company__id_company__exact=company.id_company,
                id_reference__status__in=active
            )
            if not statistical_indexes.exists():
                # Generate a statistical index
                queryset = ApportiomentComposition.objects.select_related('id_company').filter(
                    status='S',
                    id_company__pk=company.id_company
                ).annotate(
                    value=Value('0', output_field=DecimalField()),
                    unit=Value('kWh', output_field=CharField()),
                    associated_company=F('id_energy_composition__id_company__company_name')
                ).order_by('id_company__company_name')

                # Saves a report with a temporary status
                params = {
                    'params': {
                        'company_id': company.id_company,
                        'year': indexes_date.year,
                        'month': indexes_date.month,
                        'index_type': 'A',
                        'opt': '1'
                    }
                }
                mock = namedtuple('Mock', ['data'])
                mock.data = params

                generated_indexes = self.generate_data(queryset, mock, get_success_headers)
                if generated_indexes.status_code is not 201:
                    self.logger.error(
                        f'ERROR: Fail to generate the statistical indexes for company [{company.company_name}]')
                else:
                    # Send a statistical index
                    generated_indexex_dict = generated_indexes.data
                    index = CompanyReference.objects.get(pk=generated_indexex_dict['id'])
                    saved_indexes = self.send_index(request, index)
                    if saved_indexes.status_code is not 200:
                        self.logger.error(
                            f'ERROR: Fail to send statistical-indexes temp_id: [{generated_indexex_dict["id"]} to SAP.')
        self.logger.info(f'INFO: Job Generate and sender Statistical Indexes was successfully ran at {datetime_now}')

    @transaction.atomic
    def update_flat_rate_apportionment(self):
        """
            Checks if it is the second work day of the month only on weekdays, if it is, update the fixed apportionment
            rate with last value from global variables.
        """
        datetime_now = datetime.now(get_local_timezone())
        if datetime_now.month == 1:
            indexes_date = date(int(datetime_now.year) - 1, 12, 1)
        else:
            indexes_date = date(int(datetime_now.year), int(datetime_now.month) - 1, 1)

        logger = HandlerLog()
        logger.info(f'INFO: Job Update flat rate apportionment was successfully ran at {datetime_now}')
        # TODO Change data source from database to SAP endpoint
        statistical_indexes = StatisticalIndex.objects.filter(
            id_reference__month=indexes_date.month,
            id_reference__year=indexes_date.year,
            id_reference__status__in=['2', '4']
        )
        if len(statistical_indexes) == 0:
            logger.error('ERROR: Statistical indices not found.')

        try:
            tfr = GlobalVariable.objects.filter(variable__name='TARIFA FIXA DE RATEIO').first()
        except GlobalVariable.DoesNotExist:
            logger.error("ERROR: Fixed apportionment rate not found in database.")

        try:
            last_upload_file = UploadFile.objects \
                    .filter(ksbs1_set__time_period=month, ksbs1_set__exercise=year) \
                    .order_by("date_upload").last()

            ct = Ksb1.objects.filter(
                cost_center__startswith='172',
                cost_element__startswith='50',
                time_period=indexes_date.month,
                exercise=indexes_date.year,
                upload_file = last_upload_file) \
                .exclude(cost_center__in=['1720012', '1720030', '1720031']) \
                .exclude(cost_element__exact='5090500002').aggregate(Sum('mr_value'))['mr_value__sum'] or 0.0
        except Ksb1.DoesNotExist:
            ct = 0.0
            logger.error("ERROR: Unable to calculate total cost, cost center not found.")

        sum_cuc = Decimal(0)
        statistical_indexes_vale = []
        cve = Decimal()
        cuc = Decimal()

        for statistical_index in statistical_indexes:
            if statistical_index.id_apport.id_energy_composition.cost_center == '1720032':
                statistical_indexes_vale.append(statistical_index)
                continue
            if statistical_index.value == Decimal():
                continue
            cuc = statistical_index.value * tfr.value
            statistical_index.rate_apportionment = Decimal(statistical_index.value / cuc)
            statistical_index.save()
            sum_cuc += statistical_index.value

        for statistical_index_vale in statistical_indexes_vale:
            cve = Decimal(ct) - sum_cuc
            statistical_index_vale.rate_apportionment = Decimal(statistical_index_vale.value / cve)
            statistical_index_vale.save()
