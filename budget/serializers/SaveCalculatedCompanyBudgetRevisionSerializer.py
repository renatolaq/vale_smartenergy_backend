from rest_framework import serializers
from .MonthlyBudgetSerializer import MonthlyBudgetSerializer
from .BudgetSerializer import BudgetSerializer


class SaveCalculatedCompanyBudgetRevisionSerializer(serializers.Serializer):
    consumptionLimit = serializers.FloatField(
        source="consumption_limit", allow_null=True)
    contractUsageFactorPeak = serializers.FloatField(
        source="contract_usage_factor_peak", default=1)
    contractUsageFactorOffpeak = serializers.FloatField(
        source="contract_usage_factor_offpeak", default=1)
    canChangeContractUsageFactor = serializers.BooleanField(
        source="can_change_contract_usage_factor", allow_null=True, required=False, default=False)
    firstYearBudget = MonthlyBudgetSerializer(source="firstyear_budget")
    secondYearBudget = MonthlyBudgetSerializer(source="secondyear_budget")
    thirdYearBudget = BudgetSerializer(source="thirdyear_budget")
    fourthYearBudget = BudgetSerializer(source="fourthyear_budget")
    fifthYearBudget = BudgetSerializer(source="fifthyear_budget")
