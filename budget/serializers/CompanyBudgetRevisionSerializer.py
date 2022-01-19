from rest_framework import serializers
from .MonthlyBudgetSerializer import MonthlyBudgetSerializer


class CompanyBudgetRevisionSerializer(serializers.Serializer):
    revision = serializers.IntegerField()
    state = serializers.CharField()
    consumptionLimit = serializers.FloatField(source="consumption_limit")
    contractUsageFactorOffpeak = serializers.FloatField(
        source="contract_usage_factor_offpeak")
    contractUsageFactorPeak = serializers.FloatField(
        source="contract_usage_factor_peak")
    canChangeContractUsageFactor = serializers.BooleanField(
        source="can_change_contract_usage_factor", allow_null=True)
    firstYearBudget = MonthlyBudgetSerializer(source="firstyear_budget")
    secondYearBudget = MonthlyBudgetSerializer(source="secondyear_budget")
    thirdYearBudget = MonthlyBudgetSerializer(source="thirdyear_budget")
    fourthYearBudget = MonthlyBudgetSerializer(source="fourthyear_budget")
    fifthYearBudget = MonthlyBudgetSerializer(source="fifthyear_budget")
