from rest_framework import serializers

from .SaveContractAllocationReportDestinationSerializer import SaveContractAllocationReportDestinationSerializer

class SaveContractAllocationReportSourceSerializer(serializers.Serializer):
    type = serializers.CharField()
    sourceUnitId = serializers.IntegerField(source="source_id", required=False, allow_null=True)
    sourceContractId = serializers.IntegerField(source="source_id", required=False, allow_null=True)
    available_power = serializers.FloatField(default=0)
    availableForSale = serializers.FloatField(source="for_sale")
    cost = serializers.FloatField(default=0)
    balance = serializers.IntegerField(default=0)
    destinations = SaveContractAllocationReportDestinationSerializer(many=True, source="allocations")

    def to_internal_value(self, data):
        ret = super().to_internal_value(data)
        ret["source_id"] = data.get("sourceContractId") or data["sourceUnitId"]
        return ret