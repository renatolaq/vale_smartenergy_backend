from rest_framework import serializers
from .CompanyBudgetRevisionSerializer import CompanyBudgetRevisionSerializer
from .BudgetChangeTrackSerializer import BudgetChangeTrackSerializer


class CompanyBudgetSerializerSummary(serializers.Serializer):
    id = serializers.IntegerField()
    company = serializers.IntegerField(source="company_id")
    year = serializers.IntegerField()
    calculationMode = serializers.CharField(source='calculation_mode')
    budgets = serializers.SerializerMethodField()
    changeTrack = BudgetChangeTrackSerializer(source="budgetchangetrack_set", many=True)

    def get_budgets(self, obj):
        return [{
            "revision": obj['companybudgetrevision_set'][0].revision,
            "state": str(obj['companybudgetrevision_set'][0].state),
            "consumptionLimit": obj['companybudgetrevision_set'][0].consumption_limit,
            "contractUsageFactorPeak": obj['companybudgetrevision_set'][0].contract_usage_factor_peak,
            "contractUsageFactorOffpeak": obj['companybudgetrevision_set'][0].contract_usage_factor_offpeak,
            "canChangeContractUsageFactor": obj['companybudgetrevision_set'][0].can_change_contract_usage_factor,
        }]
