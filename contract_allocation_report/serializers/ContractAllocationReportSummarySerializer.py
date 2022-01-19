from rest_framework import serializers
from .DeepSerializer import DeepSerializer
import datetime

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

class ContractAllocationReportSummarySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    revision = DeepSerializer(source="last_revision.revision", converter=int)
    type = DeepSerializer(source="last_revision.type", converter=str)
    active = DeepSerializer(source="last_revision.active", converter=bool)    
    referenceMonth = DeepSerializer(source="reference_month")
    changeAt = DeepSerializer(source="last_revision.change_at")
    balanceId = DeepSerializer(source="last_revision.balance.id", converter=int)
    user = DeepSerializer(source="last_revision.user", converter=str)
    balanceDate = serializers.SerializerMethodField()
    ICMSCost = DeepSerializer(source="last_revision.icms_cost")
    ICMSCostNotCreditable = DeepSerializer(source="last_revision.icms_cost_not_creditable")

    def get_balanceDate(self, obj):
        month = deep_get(obj, "last_revision.balance.month")
        year = deep_get(obj,"last_revision.balance.year")

        return datetime.date(int(year), int(month), 1)
