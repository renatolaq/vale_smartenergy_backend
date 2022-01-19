from rest_framework import serializers

class SaveEnergyContractPrioritizationParameterSerializer(serializers.Serializer):
    provider = serializers.IntegerField(allow_null=True)
    contract = serializers.IntegerField(allow_null=True)
    state = serializers.IntegerField(allow_null=True)
    unit = serializers.IntegerField(allow_null=True)
    value = serializers.FloatField()