from rest_framework import serializers


class BudgetChangeTrackSerializer(serializers.Serializer):
    budgetRevision = serializers.IntegerField(source="budget_revision")
    comment = serializers.CharField(allow_blank=True)
    user = serializers.CharField()
    changeAt = serializers.DateTimeField(source="change_at")
    state = serializers.CharField()