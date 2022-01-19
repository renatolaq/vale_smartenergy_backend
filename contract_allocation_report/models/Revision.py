from django.db import models
from enumchoicefield import ChoiceEnum, EnumChoiceField

from .ContractAllocationReport import ContractAllocationReport, ContractAllocationReportType
from balance_report_market_settlement.models import Report

class Revision(models.Model):
    id = models.BigAutoField(db_column='ID_CONTR_ALLOC_REP_REVISION', primary_key=True)  # Field name made lowercase.
    contract_allocation_report = models.ForeignKey(ContractAllocationReport, models.DO_NOTHING, db_column='ID_CONTR_ALLOC_REP')  # Field name made lowercase.
    change_justification = models.CharField(db_column='CHANGE_JUSTIFICATION', max_length=1500)  # Field name made lowercase.
    type = EnumChoiceField(ContractAllocationReportType, db_column='TYPE', max_length=50)  # Field name made lowercase.    
    revision = models.IntegerField(db_column='REVISION')  # Field name made lowercase.
    change_at = models.DateTimeField(db_column='CHANGE_AT')  # Field name made lowercase.
    user = models.CharField(db_column='USER', max_length=50)  # Field name made lowercase.
    active = models.BooleanField(db_column='ACTIVE')  # Field name made lowercase.
    balance = models.ForeignKey(Report, models.DO_NOTHING, db_column='ID_BALANCE')
    icms_cost = models.FloatField(db_column='ICMS_COST')
    icms_cost_not_creditable = models.FloatField(db_column='ICMS_COST_NOT_CREDITABLE')
    manual = models.BooleanField(db_column='MANUAL')
        
    class Meta:
        managed = False
        db_table = 'CONTR_ALLOC_REP_REVISION'