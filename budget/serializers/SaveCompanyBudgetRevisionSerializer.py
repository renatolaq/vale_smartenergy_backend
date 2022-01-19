from rest_framework import serializers
from .SaveMonthlyBudgetSerializer import SaveMonthlyBudgetSerializer
from .SaveBudgetSerializer import SaveBudgetSerializer


class SaveCompanyBudgetRevisionSerializer(serializers.Serializer):
    consumptionLimit = serializers.FloatField(
        source="consumption_limit", allow_null=True)
    contractUsageFactorPeak = serializers.FloatField(
        source="contract_usage_factor_peak", default=1)
    contractUsageFactorOffpeak = serializers.FloatField(
        source="contract_usage_factor_offpeak", default=1)
    canChangeContractUsageFactor = serializers.BooleanField(
        source="can_change_contract_usage_factor", allow_null=True, required=False, default=False)
    firstYearBudget = SaveMonthlyBudgetSerializer(source="firstyear_budget")
    secondYearBudget = SaveMonthlyBudgetSerializer(source="secondyear_budget")
    thirdYearBudget = SaveBudgetSerializer(source="thirdyear_budget")
    fourthYearBudget = SaveBudgetSerializer(source="fourthyear_budget")
    fifthYearBudget = SaveBudgetSerializer(source="fifthyear_budget")
