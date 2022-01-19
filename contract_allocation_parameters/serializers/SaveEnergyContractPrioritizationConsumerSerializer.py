from rest_framework import serializers

class SaveEnergyContractPrioritizationConsumerSerializer(serializers.Serializer):
    state = serializers.IntegerField(allow_null=True)
    units = serializers.ListField(child=serializers.IntegerField())