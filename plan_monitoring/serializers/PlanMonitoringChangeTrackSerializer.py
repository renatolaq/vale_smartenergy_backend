from rest_framework import serializers


class PlanMonitoringChangeTrackSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    planMonitoringRevision = serializers.IntegerField(source="plan_monitoring_revision")
    comment = serializers.CharField(allow_blank=True)
    user = serializers.CharField()
    changeAt = serializers.DateTimeField(source="change_at")
    action = serializers.CharField()