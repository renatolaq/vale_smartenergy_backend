from rest_framework import serializers
from .MonthlyPlanMonitoringSerializer import MonthlyPlanMonitoringSerializer

class CompanyPlanMonitoringRevisionSerializer(serializers.Serializer):
    revision = serializers.IntegerField()
    contractUsageFactorOffpeak = serializers.FloatField(
        source="contract_usage_factor_offpeak")
    contractUsageFactorPeak = serializers.FloatField(
        source="contract_usage_factor_peak")
    firstYear = MonthlyPlanMonitoringSerializer(source="firstyear_plan_monitoring")
    secondYear = MonthlyPlanMonitoringSerializer(source="secondyear_plan_monitoring")
    
