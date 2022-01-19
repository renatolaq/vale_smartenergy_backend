from rest_framework import serializers


class SavePlanMonitoringSerializer(serializers.Serializer):
    projectedPeakPowerDemand = serializers.FloatField(source='projected_peakpower_demand', allow_null=True, required=False)
    projectedOffPeakPowerDemand = serializers.FloatField(source='projected_offpeak_power_demand', allow_null=True, required=False)
    projectedPeakPowerConsumption = serializers.FloatField(source='projected_peak_power_consumption', allow_null=True, required=False)
    projectedOffPeakPowerConsumption = serializers.FloatField(source='projected_offpeak_power_consumption', allow_null=True, required=False)
    projectedTotalConsumption = serializers.FloatField(source='projected_total_consumption', allow_null=True, required=False)
    projectedProduction = serializers.FloatField(source='projected_production', allow_null=True, required=False)
    projectedProductiveStops = serializers.FloatField(source='projected_productive_stops', allow_null=True, required=False)

    
    
    realizedPeakPowerDemand = serializers.FloatField(source="realized_peakpower_demand", allow_null=True, required=False)
    realizedOffPeakPowerDemand = serializers.FloatField(source="realized_offpeak_power_demand", allow_null=True, required=False)
    
    realizedPeakPowerConsumption = serializers.FloatField(source="realized_peak_power_consumption", allow_null=True, required=False)
    realizedOffPeakPowerConsumption = serializers.FloatField(source="realized_offpeak_power_consumption", allow_null=True, required=False)
    realizedTotalConsumption = serializers.FloatField(source="realized_total_consumption", allow_null=True, required=False)
    
    realizedProduction = serializers.FloatField(source="realized_production", allow_null=True, required=False)
    