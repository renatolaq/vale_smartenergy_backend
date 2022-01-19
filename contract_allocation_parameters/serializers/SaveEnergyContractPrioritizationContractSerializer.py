from rest_framework import serializers

class SaveEnergyContractPrioritizationContractSerializer(serializers.Serializer):
    provider = serializers.IntegerField(allow_null=True)
    contracts = serializers.ListField(child=serializers.IntegerField())