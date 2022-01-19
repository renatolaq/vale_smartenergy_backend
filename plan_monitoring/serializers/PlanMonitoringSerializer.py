from rest_framework import serializers
from ..models.PlanMonitoring import PlanMonitoring


class ValueSerializer(serializers.Field):
    def __init__(self, read_only=False, write_only=False, required=None, default=serializers.empty,
                 initial=serializers.empty, source=None, label=None, help_text=None, style=None, error_messages=None, validators=None, allow_null=False):
        super().__init__(read_only=read_only, write_only=write_only, required=required, default=default, initial=initial, source="*",
                         label=label, help_text=help_text, style=style, error_messages=error_messages, validators=validators, allow_null=allow_null)
        self.local_field = source

    def to_representation(self, obj):
        if(self.local_field is None):
            self.local_field = self.field_name
        ret = {
            'value': obj.__dict__.get(self.local_field) if isinstance(obj, PlanMonitoring) else obj.get(self.local_field),
            'alerts': obj.__dict__.get(self.local_field + '_alerts', [])
                if isinstance(obj, PlanMonitoring)
                else obj.get(self.local_field + '_alerts', []) or [],
            'readonly': obj.__dict__.get(self.local_field + '_readonly', False) 
                if isinstance(obj, PlanMonitoring) 
                else obj.get(self.local_field + '_readonly', False) or False
        }
        if(ret['alerts'] is None):
            ret['alerts'] = []
        
        ret['alerts'] = map(lambda alert: {
            "alert": alert.split(':')[0],
            "justificationChangeTrackId": int(alert.split(':')[1]) if alert.split(':')[1] else None
        }, ret['alerts'])

        if(ret['readonly'] is None):
            ret['readonly'] = False

        return ret

    def to_internal_value(self, data):
        return {
            self.local_field: data.get("value"),
            self.local_field + '_alerts':
                map(lambda alert:
                    alert.get('alert') + ":" +
                    alert.get("justificationChangeTrackId", ""),
                    data.get("alerts", [])),
            self.__local_field + '_readonly': data.get("readonly", False)
        }


class PlanMonitoringSerializer(serializers.Serializer):
    contractedPeakPowerDemand = ValueSerializer(source="contracted_peak_power_demand", allow_null=True)
    contractedOffPeakPowerDemand = ValueSerializer(source="contracted_offpeak_power_demand", allow_null=True)
    realizedPeakPowerDemand = ValueSerializer(source="realized_peakpower_demand", allow_null=True)
    realizedOffPeakPowerDemand = ValueSerializer(source="realized_offpeak_power_demand", allow_null=True)
    estimatedPeakPowerDemand = ValueSerializer(source="estimated_peakpower_demand", allow_null=True)
    estimatedOffPeakPowerDemand = ValueSerializer(source="estimated_offpeak_power_demand", allow_null=True)
    projectedPeakPowerDemand = ValueSerializer(source="projected_peakpower_demand", allow_null=True)
    projectedOffPeakPowerDemand = ValueSerializer(source="projected_offpeak_power_demand", allow_null=True)
    projectedPeakPowerConsumption = ValueSerializer(source="projected_peak_power_consumption", allow_null=True)
    projectedOffPeakPowerConsumption = ValueSerializer(source="projected_offpeak_power_consumption", allow_null=True)
    realizedPeakPowerConsumption = ValueSerializer(source="realized_peak_power_consumption", allow_null=True)
    realizedOffPeakPowerConsumption = ValueSerializer(source="realized_offpeak_power_consumption", allow_null=True)
    estimatedPeakPowerConsumption = ValueSerializer(source="estimated_peak_power_consumption", allow_null=True)
    estimatedOffPeakPowerConsumption = ValueSerializer(source="estimated_offpeak_power_consumption", allow_null=True)
    estimatedProduction = ValueSerializer(source="estimated_production", allow_null=True)
    realizedProduction = ValueSerializer(source="realized_production", allow_null=True)
    projectedProduction = ValueSerializer(source="projected_production", allow_null=True)
    estimatedProductiveStops = ValueSerializer(source="estimated_productive_stops", allow_null=True)
    projectedProductiveStops = ValueSerializer(source="projected_productive_stops", allow_null=True)
    estimatedTotalConsumption = ValueSerializer(source="estimated_total_consumption", allow_null=True)
    realizedTotalConsumption = ValueSerializer(source="realized_total_consumption", allow_null=True)
    projectedTotalConsumption = ValueSerializer(source="projected_total_consumption", allow_null=True)
    variationConsumptionEstimatedRealized = ValueSerializer(source="variation_consumption_estimated_realized", allow_null=True)
    variationConsumptionEstimatedProjected = ValueSerializer(source="variation_consumption_estimated_projected", allow_null=True)
    realizedUtilizationFactorConsistencyOffPeakPower = ValueSerializer(source="realized_utilization_factor_consistency_offpeakpower", allow_null=True)
    realizedUtilizationFactorConsistencyPeakPower = ValueSerializer(source="realized_utilization_factor_consistency_peakpower", allow_null=True)
    realizedLoadFactorConsistencyOffPeakPower = ValueSerializer(source="realized_load_factor_consistency_offpeakpower", allow_null=True)
    realizedLoadFactorConsistencyPeakPower = ValueSerializer(source="realized_load_factor_consistency_peakpower", allow_null=True)
    realizedUniqueLoadFactorConsistency = ValueSerializer(source="realized_uniqueload_factor_consistency", allow_null=True)
    realizedModulationFactorConsistency = ValueSerializer(source="realized_modulation_factor_consistency", allow_null=True)
    estimatedSpecificConsumption = ValueSerializer(source="estimated_specific_consumption", allow_null=True)
    realizedSpecificConsumption = ValueSerializer(source="realized_specific_consumption", allow_null=True)
    projectedSpecificConsumption = ValueSerializer(source="projected_specific_consumption", allow_null=True)
    variationSpecificConsumptionEstimatedRealized = ValueSerializer(source="variation_specific_consumption_estimated_realized", allow_null=True)
    variationSpecificConsumptionEstimatedProjected = ValueSerializer(source="variation_specific_consumption_estimated_projected", allow_null=True)
