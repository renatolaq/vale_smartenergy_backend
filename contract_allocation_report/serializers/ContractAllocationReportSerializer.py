from rest_framework import serializers
from itertools import groupby
from typing import List
import datetime

from .DeepSerializer import DeepSerializer
from ..models.Destination import Destination
from ..models.Source import Source, SourceType
from ..models.StateDestination import StateDestination


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


class ContractAllocationReportSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    revision = DeepSerializer(source="last_revision.revision", converter=int)
    referenceMonth = DeepSerializer(source="reference_month")
    type = DeepSerializer(source="last_revision.type", converter=str)
    balance = DeepSerializer(source="last_revision.balance.id", converter=int)
    balanceName = DeepSerializer(source="last_revision.balance.report_name", converter=str)    
    active = DeepSerializer(source="last_revision.active", converter=bool)
    ICMSCost = DeepSerializer(source="last_revision.icms_cost")
    ICMSCostNotCreditable = DeepSerializer(
        source="last_revision.icms_cost_not_creditable")
    manual = DeepSerializer(source="last_revision.manual")
    sources = serializers.SerializerMethodField()

    def get_sources(self, obj):
        def destinations(destinations: List[Destination]):
            ret = []
            for destination in destinations:
                ret.append({
                    "unitId": destination.unit.id_company,
                    "unitName": destination.unit.company_name,
                    "allocatedPower": destination.allocated_power,
                    "ICMSCost": destination.icms_cost,
                    "ICMSCostNotCreditable": destination.icms_cost_not_creditable
                })
            return ret

        def destinations_states(states: List[StateDestination]):
            ret = []
            for state in states:
                ret.append({
                    "stateId": int(state.state.id_state),
                    "stateName": state.state.name,
                    "allocatedPower": state.allocated_power
                })
            return ret

        ret = []

        sources: List[Source] = deep_get(obj, "last_revision.source_set").all()

        for source in sources:
            ret.append({
                "sourceContractId": int(source.contract.id_contract_cliq) if source.type == SourceType.contract else None,
                "sourceUnitId": int(source.unit.id_company),
                "sourceName": source.unit.company_name,
                "type": source.type.verbose_name,
                "availablePower": source.available_power,
                "availableForSale": source.available_for_sale,
                "cost": source.cost,
                "balance": int(source.balance_id_origin),
                "destinations": destinations(source.destination_set.all()),
                "destinationStates": destinations_states(source.statedestination_set.all())
            })
        return ret
