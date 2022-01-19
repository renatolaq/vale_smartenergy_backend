from rest_framework import serializers
from .PlanMonitoringSerializer import PlanMonitoringSerializer


class MonthlyPlanMonitoringSerializer(serializers.Serializer):
    january = PlanMonitoringSerializer()
    february = PlanMonitoringSerializer()
    march = PlanMonitoringSerializer()
    april = PlanMonitoringSerializer()
    may = PlanMonitoringSerializer()
    june = PlanMonitoringSerializer()
    july = PlanMonitoringSerializer()
    august = PlanMonitoringSerializer()
    september = PlanMonitoringSerializer()
    october = PlanMonitoringSerializer()
    november = PlanMonitoringSerializer()
    december = PlanMonitoringSerializer()
