from rest_framework import serializers
from .BudgetSerializer import BudgetSerializer


class MonthlyBudgetSerializer(serializers.Serializer):
    january = BudgetSerializer()
    february = BudgetSerializer()
    march = BudgetSerializer()
    april = BudgetSerializer()
    may = BudgetSerializer()
    june = BudgetSerializer()
    july = BudgetSerializer()
    august = BudgetSerializer()
    september = BudgetSerializer()
    october = BudgetSerializer()
    november = BudgetSerializer()
    december = BudgetSerializer()
