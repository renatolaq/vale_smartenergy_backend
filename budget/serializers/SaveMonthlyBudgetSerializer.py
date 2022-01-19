from rest_framework import serializers
from .SaveBudgetSerializer import SaveBudgetSerializer


class SaveMonthlyBudgetSerializer(serializers.Serializer):
    january = SaveBudgetSerializer()
    february = SaveBudgetSerializer()
    march = SaveBudgetSerializer()
    april = SaveBudgetSerializer()
    may = SaveBudgetSerializer()
    june = SaveBudgetSerializer()
    july = SaveBudgetSerializer()
    august = SaveBudgetSerializer()
    september = SaveBudgetSerializer()
    october = SaveBudgetSerializer()
    november = SaveBudgetSerializer()
    december = SaveBudgetSerializer()
