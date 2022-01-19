from rest_framework import serializers
from .SavePlanMonitoringSerializer import SavePlanMonitoringSerializer


class SaveMonthlyPlanMonitoringSerializer(serializers.Serializer):
    january = SavePlanMonitoringSerializer(required=False)
    february = SavePlanMonitoringSerializer(required=False)
    march = SavePlanMonitoringSerializer(required=False)
    april = SavePlanMonitoringSerializer(required=False)
    may = SavePlanMonitoringSerializer(required=False)
    june = SavePlanMonitoringSerializer(required=False)
    july = SavePlanMonitoringSerializer(required=False)
    august = SavePlanMonitoringSerializer(required=False)
    september = SavePlanMonitoringSerializer(required=False)
    october = SavePlanMonitoringSerializer(required=False)
    november = SavePlanMonitoringSerializer(required=False)
    december = SavePlanMonitoringSerializer(required=False)
