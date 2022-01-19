from rest_framework import serializers
from .CompanyBudgetRevisionSerializer import CompanyBudgetRevisionSerializer
from .BudgetChangeTrackSerializer import BudgetChangeTrackSerializer


class CompanyBudgetSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    company = serializers.IntegerField(source="company_id")
    year = serializers.IntegerField()
    calculationMode = serializers.CharField(source='calculation_mode')
    budgets = CompanyBudgetRevisionSerializer(source="companybudgetrevision_set", many=True)
    changeTrack = BudgetChangeTrackSerializer(source="budgetchangetrack_set", many=True)
