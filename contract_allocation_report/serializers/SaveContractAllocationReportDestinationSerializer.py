from rest_framework import serializers

class SaveContractAllocationReportDestinationSerializer(serializers.Serializer):
    unitId = serializers.IntegerField(source="destination_id")
    allocatedPower = serializers.FloatField(source="allocation")
    icms_cost = serializers.FloatField(default=0)
    icms_cost_not_creditable = serializers.FloatField(default=0)