from rest_framework import serializers

from .SaveContractAllocationReportSourceSerializer import SaveContractAllocationReportSourceSerializer

class SaveContractAllocationReportSerializer(serializers.Serializer):
    balance = serializers.IntegerField()
    changeJustification = serializers.CharField(required=False)
    sources = SaveContractAllocationReportSourceSerializer(many=True)