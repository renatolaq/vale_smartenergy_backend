from company.models import Company
from balance_report_market_settlement.models import Report
from global_variables.models import GlobalVariable
import json
from rest_framework import serializers
from .models import CompanyReference, StatisticalIndex
from datetime import datetime
from .utils import get_local_timezone, is_nth_brazilian_workday, is_before_or_equal_nth_brazilian_workday


class StatisticalIndexSerializer(serializers.ModelSerializer):
    formatted_value = serializers.SerializerMethodField()
    unity = serializers.CharField()
    statistic_index = serializers.SerializerMethodField()
    associated_company = serializers.CharField()
    cost_center = serializers.CharField(read_only=True, source='id_apport.id_energy_composition.cost_center')

    def get_statistic_index(self, serialized_object):
        if serialized_object.unity in ['kWh', '%']:
            return serialized_object.id_apport.volume_code
        elif serialized_object.unity in ['R$']:
            return serialized_object.id_apport.cost_code

    def get_formatted_value(self, serialized_object):
        return '{:.4f}'.format(serialized_object.value)

    class Meta:
        model = StatisticalIndex
        fields = ['id', 'id_reference', 'id_apport', 'value', 'formatted_value', 'unity', 'statistic_index',
                  'associated_company', 'cost_center']


class CompanyReferenceSerializer(serializers.ModelSerializer):
    company_name = serializers.SerializerMethodField()
    index_name = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    is_updatable = serializers.SerializerMethodField()
    can_send = serializers.SerializerMethodField()
    results = StatisticalIndexSerializer(many=True, read_only=True)
    chargeback = serializers.SerializerMethodField()
    flat_rate_apportionment = serializers.SerializerMethodField()

    def get_company_name(self, serialized_object):
        return serialized_object.id_company.company_name

    def get_index_name(self, serialized_object):
        return serialized_object.index_name

    def get_status(self, serialized_object):
        return serialized_object.status
    
    def get_is_updatable(self, serialized_object):
        return serialized_object.status in ['3', '7']

    def get_can_send(self, serialized_object):
        return serialized_object.status in ['0', '3', '7', '9']

    def get_chargeback(self, serialized_object):
        window_day = 1
        limit_hour = 15
        date = datetime.now(get_local_timezone())
        report_year = int(serialized_object.year)
        report_month = int(serialized_object.month)
        is_current_month = (report_year == date.year and report_month == date.month)
        is_before_nth_day = is_before_or_equal_nth_brazilian_workday(date.year, date.month, window_day - 1)
        if (is_current_month or
            (is_before_nth_day or
             (is_nth_brazilian_workday(date, window_day) and date.hour <= limit_hour))) and \
                serialized_object.status in ['2', '4']:
            return True
        return False

    def get_flat_rate_apportionment(self, serialized_object):
        tfr = GlobalVariable.objects.filter(variable__name='TARIFA FIXA DE RATEIO').first()
        return '{:,.4f}'.format(tfr.value).replace(',', '_').replace('.', ',').replace('_', '.')
    
    class Meta:
        model = CompanyReference
        fields = ['id', 'id_company', 'chargeback', 'is_updatable', 'can_send', 'company_name',
                  'transaction_type', 'month', 'year', 'index_name', 'creation_date',
                  'sap_document_number', 'flat_rate_apportionment', 'status', 'cost_type',
                   'total_cost', 'results']


class ReportsSerializer(serializers.ModelSerializer):
    report_name = serializers.SerializerMethodField()
    report_data = serializers.SerializerMethodField()
    company_name = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    sap_document_number = serializers.CharField()

    def get_report_data(self, serialized_object):
        return json.loads(serialized_object.report)

    def get_report_name(self, serialized_object):
        creation_date = datetime.fromisoformat(str(serialized_object.creation_date))
        return f'{serialized_object.report_type.initials}_{creation_date.date().strftime("%d%m%Y")}_{creation_date.strftime("%H%M")}'

    def get_status(self, serialized_object):
        if serialized_object.status is not None:
            return serialized_object.status
        else:
            return '0'

    def get_company_name(self, serialized_object):
        return serialized_object.id_company.company_name

    class Meta:
        model = Report
        fields = ['id', 'report_name', 'report_type', 'creation_date', 'status', 'id_company', 'company_name',
                  'report_data', 'report', 'sap_document_number', 'month', 'year']


class CompaniesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ['id_company', 'company_name', 'type']


class IndexesDataSerializer(serializers.Serializer):
    statistic_index = serializers.SerializerMethodField()
    value = serializers.SerializerMethodField()
    unit = serializers.CharField()
    id_apport = serializers.IntegerField()
    associated_company = serializers.CharField()

    def get_statistic_index(self, serialized_object):
        if serialized_object.unit in ['kWh', '%']:
            return serialized_object.volume_code
        elif serialized_object.unit in ['R$']:
            return serialized_object.cost_code

    def get_value(self, serialized_object):
        return '{:.8f}'.format(serialized_object.value)


class SapSendSerialiazer(serializers.Serializer):
    cost_center = serializers.CharField()
    statistical_index = serializers.CharField()
    value = serializers.SerializerMethodField()
    unity = serializers.CharField()

    def get_statistical_index(self, serialized_object):
        return serialized_object.statistical_index

