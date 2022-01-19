from rest_framework import serializers
from .SaveCompanyPlanMonitoringRevisionSerializer import SaveCompanyPlanMonitoringRevisionSerializer


class SaveCompanyPlanMonitoringSerializer(serializers.Serializer):
    monitoringData = SaveCompanyPlanMonitoringRevisionSerializer(source="company_plan_monitoring")
    comment = serializers.CharField(required=False)