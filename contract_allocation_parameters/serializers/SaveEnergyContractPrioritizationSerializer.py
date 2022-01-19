from rest_framework import serializers

from .SaveEnergyContractPrioritizationConsumerSerializer import SaveEnergyContractPrioritizationConsumerSerializer
from .SaveEnergyContractPrioritizationContractSerializer import SaveEnergyContractPrioritizationContractSerializer
from .SaveEnergyContractPrioritizationParameterSerializer import SaveEnergyContractPrioritizationParameterSerializer

class SaveEnergyContractPrioritizationSerializer(serializers.Serializer):
    name = serializers.CharField()
    type = serializers.CharField()
    subtype = serializers.CharField()
    #changeJustification = serializers.CharField()
    active = serializers.BooleanField()
    contracts = SaveEnergyContractPrioritizationContractSerializer(many=True)
    generators = serializers.ListField(child=serializers.IntegerField())
    consumers = SaveEnergyContractPrioritizationConsumerSerializer(many=True)
    parameters = SaveEnergyContractPrioritizationParameterSerializer(many=True)