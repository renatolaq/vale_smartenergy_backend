from rest_framework import serializers
from .SaveCalculatedCompanyBudgetRevisionSerializer import SaveCalculatedCompanyBudgetRevisionSerializer


class SaveCalculatedCompanyBudgetSerializer(serializers.Serializer):
    company = serializers.IntegerField(source='company_id')
    year = serializers.IntegerField()    
    calculationMode = serializers.CharField(source='calculation_mode')
    budget = SaveCalculatedCompanyBudgetRevisionSerializer()
    