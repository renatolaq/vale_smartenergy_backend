from rest_framework import serializers
from itertools import groupby

from .DeepSerializer import DeepSerializer


def deep_get(dictionary, keys):
    keys = [""] + keys.split(".")

    def it(o):
        keys.pop(0)
        if(not keys or o is None):
            return o
        if isinstance(o, dict):
            return it(o.get(keys[0]))
        return it(getattr(o, keys[0]))
    return it(dictionary)


class EnergyContractPrioritizationSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    revision = DeepSerializer(source="last_revision.revision", converter=int)
    order = DeepSerializer(source="last_revision.order", converter=int)
    name = serializers.CharField()
    type = serializers.CharField()
    subtype = serializers.CharField()
    active = DeepSerializer(source="last_revision.active", converter=bool)
    contracts = serializers.SerializerMethodField()
    generators = serializers.SerializerMethodField()
    consumers = serializers.SerializerMethodField()
    parameters = serializers.SerializerMethodField()

    def get_contracts(self, obj):
        ret = []
        contracts = groupby(deep_get(
            obj, "last_revision.contract_set").all(), lambda x: x.company_provider)
        for provider, contracts_cliq in contracts:
            ret.append({
                "provider": provider,
                "contracts": list(filter(None, map(lambda v: v.contract_cliq_provider, contracts_cliq)))
            })
        return ret

    def get_generators(self, obj):
        generators = list(deep_get(obj, "last_revision.generator_set").all())
        return map(lambda v: int(v.company_generator), generators)

    def get_consumers(self, obj):
        ret = []
        consumers = groupby(deep_get(
            obj, "last_revision.consumer_set").all(), lambda x: x.state_consumer)
        for state, company_comsumers in consumers:
            ret.append({
                "state": state,
                "units": list(filter(None, map(lambda v: v.company_consumer, company_comsumers)))
            })
        return ret

    def get_parameters(self, obj):
        parameters = list(deep_get(obj, "last_revision.parameter_set").all())
        return map(lambda v: {
            "provider": int(v.company_provider) if v.company_provider is not None else None,
            "contract": int(v.contract_cliq_provider) if v.contract_cliq_provider is not None else None,
            "state": int(v.state_comsumer) if v.state_comsumer is not None else None,
            "unit": int(v.company_comsumer) if v.company_comsumer is not None else None,
            "value": v.value
        }, parameters)
