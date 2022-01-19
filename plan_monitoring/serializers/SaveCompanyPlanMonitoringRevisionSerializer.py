from rest_framework import serializers
from .SaveMonthlyPlanMonitoringSerializer import SaveMonthlyPlanMonitoringSerializer
from .SavePlanMonitoringSerializer import SavePlanMonitoringSerializer


class SaveCompanyPlanMonitoringRevisionSerializer(serializers.Serializer):
    firstYear = SaveMonthlyPlanMonitoringSerializer(source="firstyear_plan_monitoring")
    secondYear = SaveMonthlyPlanMonitoringSerializer(source="secondyear_plan_monitoring")