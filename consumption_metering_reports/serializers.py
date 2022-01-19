import json
from decimal import Decimal, ROUND_FLOOR
from datetime import datetime
from rest_framework import serializers
from .models import Report, MeteringReportData, ReportType, Log
import locale


class SavedReportSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    report_name = serializers.CharField()
    creation_date = serializers.DateTimeField()
    status = serializers.CharField()
    month = serializers.CharField()
    year = serializers.CharField()


def get_formated_energy_value(value):
    rounded_number = f'{value:.3f}'.replace('.', ',')
    return f'{rounded_number[:len(rounded_number) -7]}.{rounded_number[len(rounded_number) - 7:]}' if value >= 1000 else rounded_number


def get_formated_metering_days_value(value):
    return f'{value:.2f}'.replace('.', ',')


class ReportDataSerializer(serializers.Serializer):
    ccee_code = serializers.SerializerMethodField()
    gauge_tag = serializers.SerializerMethodField()
    id_company = serializers.SerializerMethodField()
    associated_company = serializers.SerializerMethodField()
    metering_days_ccee = serializers.SerializerMethodField()
    metering_days_vale = serializers.SerializerMethodField()
    data_source = serializers.CharField()
    def get_ccee_code(self, serialized_object):
        return serialized_object.ccee_code
    def get_gauge_tag(self, serialized_object):
        return serialized_object.gauge_tag
    def get_associated_company(self, serialized_object):
        return serialized_object.associated_company
    def get_id_company(self, serialized_object):
        return serialized_object.id_company.id_company
    def get_metering_days_ccee(self, serialized_object):
        return get_formated_metering_days_value(serialized_object.metering_days_ccee)
    def get_metering_days_vale(self, serialized_object):
        return get_formated_metering_days_value(serialized_object.metering_days_vale)


class ProjectedConsumptionReportDataSerializer(ReportDataSerializer):
    id = serializers.SerializerMethodField()
    projected_consumption_ccee = serializers.SerializerMethodField()
    projected_consumption_vale = serializers.SerializerMethodField()
    ccee_vs_vale = serializers.SerializerMethodField()
    def get_id(self, serialized_object):
        return serialized_object.id
    def get_projected_consumption_ccee(self, serialized_object):
        return get_formated_energy_value(serialized_object.projected_consumption_ccee)
    def get_projected_consumption_vale(self, serialized_object):
        return get_formated_energy_value(serialized_object.projected_consumption_vale)
    def get_ccee_vs_vale(self, serialized_object):
        try:
            return '{:,.2f}'.format(serialized_object.ccee_vs_vale).replace(',', '_').replace('.', ',').replace('_', '.')
        except AttributeError:
            return '100,00'


class ProjectedConsumptionReportSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    report_name = serializers.CharField()
    creation_date = serializers.DateTimeField()
    status = serializers.CharField()
    month = serializers.CharField()
    year = serializers.CharField()
    metering_report_data = ProjectedConsumptionReportDataSerializer(many=True, required=False)


class ProjectedConsumptionReportViewSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    next = serializers.CharField()
    previous = serializers.CharField()
    results = ProjectedConsumptionReportSerializer(many=True)


class ProjectedConsumptionReportDataViewSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    next = serializers.CharField()
    previous = serializers.CharField()
    report_name = serializers.CharField()
    month = serializers.CharField()
    year = serializers.CharField()
    limit_ccee_vale = serializers.DecimalField(max_digits=18, decimal_places=9)
    results = ProjectedConsumptionReportDataSerializer(many=True)


class GrossConsumptionReportDataSerializer(ReportDataSerializer):
    gross_consumption_ccee = serializers.SerializerMethodField()
    gross_consumption_vale = serializers.SerializerMethodField()
    def get_gross_consumption_ccee(self, serialized_object):
        return get_formated_energy_value(serialized_object.gross_consumption_ccee)
    def get_gross_consumption_vale(self, serialized_object):
        return get_formated_energy_value(serialized_object.gross_consumption_vale)


class GrossConsumptionReportSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    report_name = serializers.CharField()
    creation_date = serializers.DateTimeField()
    status = serializers.CharField()
    month = serializers.CharField()
    year = serializers.CharField()
    metering_report_data = GrossConsumptionReportDataSerializer(many=True, required=False)


class GrossConsumptionReportViewSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    next = serializers.CharField()
    previous = serializers.CharField()
    results = GrossConsumptionReportSerializer(many=True)


class GrossConsumptionReportDataViewSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    next = serializers.CharField()
    previous = serializers.CharField()
    report_name = serializers.CharField()
    month = serializers.CharField()
    year = serializers.CharField()
    limit_ccee_vale = serializers.DecimalField(max_digits=18, decimal_places=9)
    results = GrossConsumptionReportDataSerializer(many=True)


class DetailedConsumptionReportDataSerializer(serializers.Serializer):
    id = serializers.SerializerMethodField()
    director_board = serializers.SerializerMethodField()
    business = serializers.SerializerMethodField()
    consumer = serializers.SerializerMethodField()
    projected_consumption_off_peak = serializers.SerializerMethodField()
    projected_consumption_on_peak = serializers.SerializerMethodField()
    total_projected_consumption = serializers.SerializerMethodField()
    loss_percentage = serializers.SerializerMethodField()
    total_projected_consumption_more_loss_type_1 = serializers.SerializerMethodField()
    total_projected_consumption_more_loss_type_2 = serializers.SerializerMethodField()
    loss_type = serializers.SerializerMethodField()
    projected_consumption_ccee = serializers.SerializerMethodField()
    projected_consumption_vale = serializers.SerializerMethodField()

    def get_id(self, serialized_object):
        return serialized_object.id
    def get_director_board(self, serialized_object):
        return serialized_object.director_board
    def get_business(self, serialized_object):
        return serialized_object.business
    def get_consumer(self, serialized_object):
       
        try:
            return serialized_object.associated_company
        except AttributeError:
            pass
        try:
            return serialized_object.consumer
        except AttributeError:
            pass

        return ""
        
    def get_projected_consumption_off_peak(self, serialized_object):
        if serialized_object.projected_consumption_off_peak is not None:
            return '{:,.3f}'.format(serialized_object.projected_consumption_off_peak).replace(',', '_').replace('.', ',').replace('_', '.')
        else:
            return serialized_object.projected_consumption_off_peak
    def get_projected_consumption_on_peak(self, serialized_object):
        if serialized_object.projected_consumption_on_peak is not None:
            return '{:,.3f}'.format(serialized_object.projected_consumption_on_peak).replace(',', '_').replace('.', ',').replace('_', '.')
        else:
            return serialized_object.projected_consumption_on_peak
    def get_total_projected_consumption(self, serialized_object):
        if serialized_object.total_projected_consumption is not None:
            return '{:,.3f}'.format(serialized_object.total_projected_consumption).replace(',', '_').replace('.', ',').replace('_', '.')
        else:
            return serialized_object.total_projected_consumption
    def get_loss_percentage(self, serialized_object):
        if serialized_object.loss_percentage is not None:
            return '{:,.2f}'.format(serialized_object.loss_percentage).replace(',', '_').replace('.', ',').replace('_', '.')
        else:
            return serialized_object.loss_percentage
    def get_total_projected_consumption_more_loss_type_1(self, serialized_object):
        if serialized_object.total_projected_consumption_more_loss_type_1 is not None:
            return '{:,.3f}'.format(serialized_object.total_projected_consumption_more_loss_type_1).replace(',', '_').replace('.', ',').replace('_', '.')
        else:
            return serialized_object.total_projected_consumption_more_loss_type_1
    def get_total_projected_consumption_more_loss_type_2(self, serialized_object):
        if serialized_object.total_projected_consumption_more_loss_type_2 is not None:
            return '{:,.3f}'.format(serialized_object.total_projected_consumption_more_loss_type_2).replace(',', '_').replace('.', ',').replace('_', '.')
        else: 
            return serialized_object.total_projected_consumption_more_loss_type_2

    def get_loss_type(self, serialized_object):
        if serialized_object.loss_type is not None:
            return 'type' + serialized_object.loss_type
        else:
            return 'type1'
    
    def get_projected_consumption_ccee(self, serialized_object):
        if serialized_object.projected_consumption_off_peak is not None:
            return '{:,.3f}'.format(serialized_object.projected_consumption_ccee).replace(',', '_').replace('.', ',').replace('_', '.')
        else:
            return serialized_object.projected_consumption_ccee

    def get_projected_consumption_vale(self, serialized_object):
        if serialized_object.projected_consumption_off_peak is not None:
            return '{:,.3f}'.format(serialized_object.projected_consumption_vale).replace(',', '_').replace('.', ',').replace('_', '.')
        else:
            return serialized_object.projected_consumption_vale
            
class DetailedConsumptionReportSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    report_name = serializers.CharField()
    referenced_report_name = serializers.CharField()
    creation_date = serializers.DateTimeField()
    status = serializers.CharField()
    month = serializers.CharField()
    year = serializers.CharField()
    metering_report_data = DetailedConsumptionReportDataSerializer(many=True, required=False)


class DetailedConsumptionReportViewSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    next = serializers.CharField()
    previous = serializers.CharField()
    results = DetailedConsumptionReportSerializer(many=True)

class DetailedConsumptionReportDataViewSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    next = serializers.CharField()
    previous = serializers.CharField()
    report_name = serializers.CharField()
    referenced_report_name = serializers.CharField()
    month = serializers.CharField()
    year = serializers.CharField()
    limit_ccee_vale = serializers.DecimalField(max_digits=18, decimal_places=9)
    results = DetailedConsumptionReportDataSerializer(many=True)



class LogSerializer(serializers.ModelSerializer):

    class Meta:
        model = Log
        fields = ['id', 'table_name', 'action_type', 'field_pk', 'old_value', 'new_value', 'observation', 'date', 'user']


class ProjectedConsumptionReportListSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    report_name = serializers.CharField(read_only=True)



#================================================================================
#================================================================================
#================================================================================
#================================================================================
class DetailedConsumptionReportDataSerializerNew(serializers.Serializer):
    id = serializers.SerializerMethodField()
    director_board = serializers.SerializerMethodField() #Diretoria (RPD)
    business = serializers.SerializerMethodField()  #Negócio (RPD)
    consumer = serializers.SerializerMethodField() #Consumidor (RDP)
    projected_consumption_off_peak = serializers.SerializerMethodField() #Consumo Projetado Fora Ponta (RPD)
    projected_consumption_on_peak = serializers.SerializerMethodField() #Consumo Projetado Ponta (RPD)
    total_projected_consumption = serializers.SerializerMethodField() #Consumo Projetado Total (RPD)
    loss_percentage = serializers.SerializerMethodField() #Perdas (RPD)
    total_projected_consumption_more_loss_type_1 = serializers.SerializerMethodField() #Consumo Projetado Total + Perdas (RPD)
    total_projected_consumption_more_loss_type_2 = serializers.SerializerMethodField()
    loss_type = serializers.SerializerMethodField() #Tipo de Perda (RPD).
    projected_consumption_ccee = serializers.SerializerMethodField() #Consumo Projetado CCEE (RCP)
    projected_consumption_vale = serializers.SerializerMethodField() #Consumo Projetado Vale (RCP)
    data_source = serializers.CharField() #Fonte de dados (RCP)
    metering_days_ccee = serializers.SerializerMethodField() #Dias de Medição CCEE (RCP)
    metering_days_vale = serializers.SerializerMethodField() #Dias de Medição Vale (RCP)
    ccee_vs_vale = serializers.SerializerMethodField() #CCEE x Vale (RCP)
    updated_consumption = serializers.BooleanField(required=False, allow_null=True)

    def get_id(self, serialized_object):
        return serialized_object.id
    def get_director_board(self, serialized_object):
        return serialized_object.director_board
    def get_business(self, serialized_object):
        return serialized_object.business
    def get_consumer(self, serialized_object):
       
        try:
            return serialized_object.associated_company
        except AttributeError:
            pass
        try:
            return serialized_object.consumer
        except AttributeError:
            pass

        return ""
        
    def get_projected_consumption_off_peak(self, serialized_object):
        if serialized_object.projected_consumption_off_peak is not None:
            return '{:,.3f}'.format(serialized_object.projected_consumption_off_peak).replace(',', '_').replace('.', ',').replace('_', '.')
        else:
            return serialized_object.projected_consumption_off_peak
    def get_projected_consumption_on_peak(self, serialized_object):
        if serialized_object.projected_consumption_on_peak is not None:
            return '{:,.3f}'.format(serialized_object.projected_consumption_on_peak).replace(',', '_').replace('.', ',').replace('_', '.')
        else:
            return serialized_object.projected_consumption_on_peak
    def get_total_projected_consumption(self, serialized_object):
        if serialized_object.total_projected_consumption is not None:
            return '{:,.3f}'.format(serialized_object.total_projected_consumption).replace(',', '_').replace('.', ',').replace('_', '.')
        else:
            return serialized_object.total_projected_consumption
    def get_loss_percentage(self, serialized_object):
        if serialized_object.loss_percentage is not None:
            return '{:,.2f}'.format(serialized_object.loss_percentage).replace(',', '_').replace('.', ',').replace('_', '.')
        else:
            return serialized_object.loss_percentage
    def get_total_projected_consumption_more_loss_type_1(self, serialized_object):
        if serialized_object.total_projected_consumption_more_loss_type_1 is not None:
            return '{:,.3f}'.format(serialized_object.total_projected_consumption_more_loss_type_1).replace(',', '_').replace('.', ',').replace('_', '.')
        else:
            return serialized_object.total_projected_consumption_more_loss_type_1
    def get_total_projected_consumption_more_loss_type_2(self, serialized_object):
        if serialized_object.total_projected_consumption_more_loss_type_2 is not None:
            return '{:,.3f}'.format(serialized_object.total_projected_consumption_more_loss_type_2).replace(',', '_').replace('.', ',').replace('_', '.')
        else: 
            return serialized_object.total_projected_consumption_more_loss_type_2

    def get_loss_type(self, serialized_object):
        if serialized_object.loss_type is not None:
            return 'type' + serialized_object.loss_type
        else:
            return 'type1'
    
    def get_projected_consumption_ccee(self, serialized_object):
        if serialized_object.projected_consumption_off_peak is not None:
            return '{:,.3f}'.format(serialized_object.projected_consumption_ccee).replace(',', '_').replace('.', ',').replace('_', '.')
        else:
            return serialized_object.projected_consumption_ccee

    def get_projected_consumption_vale(self, serialized_object):
        if serialized_object.projected_consumption_off_peak is not None:
            return '{:,.3f}'.format(serialized_object.projected_consumption_vale).replace(',', '_').replace('.', ',').replace('_', '.')
        else:
            return serialized_object.projected_consumption_vale
    
    def get_metering_days_ccee(self, serialized_object):
        return get_formated_metering_days_value(serialized_object.metering_days_ccee)

    def get_metering_days_vale(self, serialized_object):
        return get_formated_metering_days_value(serialized_object.metering_days_vale)

    def get_ccee_vs_vale(self, serialized_object):
        try:
            return '{:,.2f}'.format(serialized_object.ccee_vs_vale).replace(',', '_').replace('.', ',').replace('_', '.')
        except AttributeError:
            return '100,00'

class DetailedConsumptionReportSerializerNew(serializers.Serializer):
    id = serializers.IntegerField()
    report_name = serializers.CharField()
    creation_date = serializers.DateTimeField()
    status = serializers.CharField()
    month = serializers.CharField()
    year = serializers.CharField()
    referenced_report_name = serializers.CharField()
    metering_report_data = DetailedConsumptionReportDataSerializerNew(many=True, required=False)

class DetailedConsumptionReportViewSerializerNew(serializers.Serializer):
    count = serializers.IntegerField()
    next = serializers.CharField()
    previous = serializers.CharField()
    results = DetailedConsumptionReportSerializerNew(many=True)


class DetailedConsumptionReportDataViewSerializerNew(serializers.Serializer):
    count = serializers.IntegerField()
    next = serializers.CharField()
    previous = serializers.CharField()
    report_name = serializers.CharField()
    referenced_report_name = serializers.CharField()
    month = serializers.CharField()
    year = serializers.CharField()
    limit_ccee_vale = serializers.DecimalField(max_digits=18, decimal_places=9)
    results = DetailedConsumptionReportDataSerializerNew(many=True)

