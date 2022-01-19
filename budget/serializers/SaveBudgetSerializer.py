from rest_framework import serializers


class SaveBudgetSerializer(serializers.Serializer):
    contractedPeakPowerDemand = serializers.FloatField(
        source="contracted_peak_power_demand", allow_null=True)
    contractedOffPeakPowerDemand = serializers.FloatField(
        source="contracted_offpeak_power_demand", allow_null=True)
    estimatedPeakPowerDemand = serializers.FloatField(
        source="estimated_peak_power_demand", allow_null=True)
    estimatedOffPeakPowerDemand = serializers.FloatField(
        source="estimated_offpeak_power_demand", allow_null=True)
    consumptionPeakPowerDemand = serializers.FloatField(
        source="consumption_peak_power_demand", allow_null=True, required=False)
    consumptionOffPeakPowerDemand = serializers.FloatField(
        source="consumption_offpeak_power_demand", allow_null=True, required=False)
    totalConsumption = serializers.FloatField(
        source="total_consumption", allow_null=True, required=False)
    production = serializers.FloatField(allow_null=True)
    productiveStops = serializers.FloatField(
        source="productive_stops", allow_null=True)
