from company.models import Company
from django.db import models
from datetime import datetime
from enum import Enum

from energy_composition.models import ApportiomentComposition
from organization.models import ElectricalGrouping


class StatisticalIndex(models.Model):
    id = models.AutoField(db_column='ID_STATISTICAL', primary_key=True)
    id_reference = models.ForeignKey('CompanyReference', related_name='results', on_delete=models.CASCADE, db_column='ID_REFERENCE')
    id_apport = models.ForeignKey(ApportiomentComposition, related_name='statistical_indexes', on_delete=models.DO_NOTHING, db_column='ID_APPORT')
    value = models.DecimalField(db_column='VALUE', max_digits=18, decimal_places=8)
    unity = models.CharField(db_column='UNITY', max_length=4)
    rate_apportionment = models.DecimalField(db_column='RATE_APPORTIONMENT', max_digits=18, decimal_places=8)
    associated_company = models.CharField(db_column='ASSOCIATED_COMPANY', max_length=250, null=False)

    class Meta:
        managed = False
        db_table = 'STATISTICAL_INDEX'

class CostType(Enum):
    OPTION_1 = '1'
    OPTION_2 = '2'

    @classmethod
    def choices(cls):
        return [(key.value, key.name) for key in cls]
    
    @classmethod
    def values(cls):
        return [key.value for key in cls]


class CompanyReference(models.Model):
    id = models.AutoField(db_column='ID_REFERENCE', primary_key=True)
    id_company = models.ForeignKey(Company, on_delete=models.CASCADE, db_column='ID_COMPANY', null=True)
    transaction_type = models.CharField(db_column='TRANSACTION_TYPE', max_length=8)
    index_name = models.CharField(db_column='INDEX_NAME', max_length=50)
    creation_date = models.DateTimeField(db_column='CREATION_DATE')
    month = models.DecimalField(db_column='MONTH', max_digits=2, decimal_places=0)
    year = models.DecimalField(db_column='YEAR', max_digits=4, decimal_places=0)
    sap_document_number = models.CharField(db_column='SAP_DOCUMENT_NUMBER', max_length=15, null=True)
    cost_type = models.CharField(db_column='COST_TYPE', max_length=1, choices=CostType.choices(), 
        default=CostType.OPTION_1, null=True)
    total_cost = models.DecimalField(db_column='TOTAL_COST', max_digits=18, decimal_places=8, null=True)
    status = models.CharField(db_column='STATUS', max_length=1)

    class Meta:
        managed = False
        db_table = 'COMPANY_REFERENCE'