from rest_framework import serializers
from ..models.Budget import Budget

class ValueSerializer(serializers.Field):
    def __init__(self, read_only=False, write_only=False, required=None, default=serializers.empty, 
        initial=serializers.empty, source=None, label=None, help_text=None, style=None, error_messages=None, validators=None, allow_null=False):
        super().__init__(read_only=read_only, write_only=write_only, required=required, default=default, initial=initial, source="*",
                         label=label, help_text=help_text, style=style, error_messages=error_messages, validators=validators, allow_null=allow_null)
        self.__local_field = source

    def to_representation(self, obj):
        if(self.__local_field is None):
            self.__local_field = self.field_name
        ret = {
            'value': obj.__dict__.get(self.__local_field) if isinstance(obj, Budget) else obj.get(self.__local_field),
            'alerts': obj.__dict__.get(self.__local_field + '_alerts', []) 
                if isinstance(obj, Budget) 
                else obj.get(self.__local_field + '_alerts', []) or [],
            'readonly': obj.__dict__.get(self.__local_field + '_readonly', False) 
                if isinstance(obj, Budget) 
                else obj.get(self.__local_field + '_readonly', False) or False
        }
        if(ret['alerts'] is None):
            ret['alerts'] = []
        if(ret['readonly'] is None):
            ret['readonly'] = False
        return ret

    def to_internal_value(self, data):
        return {
            self.__local_field: data.get("value"),
            self.__local_field + '_alerts': data.get("value", []),
            self.__local_field + '_readonly': data.get("readonly", False)
        }


class BudgetSerializer(serializers.Serializer):
    contractedPeakPowerDemand = ValueSerializer(
        source="contracted_peak_power_demand", allow_null=True)
    contractedOffPeakPowerDemand = ValueSerializer(
        source="contracted_offpeak_power_demand", allow_null=True)
    estimatedPeakPowerDemand = ValueSerializer(
        source="estimated_peak_power_demand", allow_null=True)
    estimatedOffPeakPowerDemand = ValueSerializer(
        source="estimated_offpeak_power_demand", allow_null=True)
    consumptionPeakPowerDemand = ValueSerializer(
        source="consumption_peak_power_demand", allow_null=True)
    consumptionOffPeakPowerDemand = ValueSerializer(
        source="consumption_offpeak_power_demand", allow_null=True)
    production = ValueSerializer(allow_null=True)
    productiveStops = ValueSerializer(
        source="productive_stops", allow_null=True)
    totalConsumption = ValueSerializer(
        source="total_consumption", allow_null=True, read_only=True)
    utilizationFactorConsistencyOffPeakPower = ValueSerializer(
        source="utilization_factor_consistency_offpeakpower", allow_null=True, read_only=True)
    utilizationFactorConsistencyPeakPower = ValueSerializer(
        source="utilization_factor_consistency_peakpower", allow_null=True, read_only=True)
    loadFactorConsistencyOffPeakPower = ValueSerializer(
        source="loadfactor_consistency_offpeakpower", allow_null=True, read_only=True)
    loadFactorConsistencyPeakPower = ValueSerializer(
        source="loadfactor_consistency_peakpower", allow_null=True, read_only=True)
    uniqueLoadFactorConsistency = ValueSerializer(
        source="uniqueload_factor_consistency", allow_null=True, read_only=True)
    modulationFactorConsistency = ValueSerializer(
        source="modulation_factor_consistency", allow_null=True, read_only=True)
    specificConsumption = ValueSerializer(
        source="specific_consumption", allow_null=True, read_only=True)
