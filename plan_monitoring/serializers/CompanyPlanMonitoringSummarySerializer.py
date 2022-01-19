from rest_framework import serializers
from .CompanyPlanMonitoringRevisionSerializer import CompanyPlanMonitoringRevisionSerializer
from .PlanMonitoringChangeTrackSerializer import PlanMonitoringChangeTrackSerializer


class CompanyPlanMonitoringSummarySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    company = serializers.IntegerField(source="company_id")
    year = serializers.IntegerField()
    calculationMode = serializers.CharField(source='calculation_mode')
    state = serializers.SerializerMethodField()
    
    def get_state(self, obj):
        if isinstance(obj, dict):
            return "WithOpenJustifications" if obj.get("has_open_justification") else "NoOpenJustification"
        else:
            return "WithOpenJustifications" if obj.has_open_justification else "NoOpenJustification"