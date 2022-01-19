from rest_framework import serializers
from .SaveCompanyBudgetRevisionSerializer import SaveCompanyBudgetRevisionSerializer


class SaveCompanyBudgetSerializer(serializers.Serializer):
    company = serializers.IntegerField(source='company_id', required=False)
    year = serializers.IntegerField(required=False)
    budget = SaveCompanyBudgetRevisionSerializer()
    calculationMode = serializers.CharField(source='calculation_mode', required=False)