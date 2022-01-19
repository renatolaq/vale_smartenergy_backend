from rest_framework import serializers
from .DeepSerializer import DeepSerializer

class EnergyContractPrioritizationSummarySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    revision = DeepSerializer(source="last_revision.revision", converter=int)
    order = DeepSerializer(source="last_revision.order", converter=int)
    name = serializers.CharField()
    type = serializers.CharField()
    subtype = serializers.CharField()
    changeAt = DeepSerializer(source="last_revision.change_at")
    user = DeepSerializer(source="last_revision.user")
    active = DeepSerializer(source="last_revision.active", converter=bool)
    changeJustification = DeepSerializer(source="last_revision.change_justification")
    contractsEdited = DeepSerializer(source="last_revision.contracts_edited", converter=bool)
    generatorsEdited = DeepSerializer(source="last_revision.generators_edited", converter=bool)
    consumersEdited = DeepSerializer(source="last_revision.consumers_edited", converter=bool)
    parametersEdited = DeepSerializer(source="last_revision.parameters_edited", converter=bool)
