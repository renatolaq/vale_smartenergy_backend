from django.db import models
from enumchoicefield import ChoiceEnum, EnumChoiceField


class ContractAllocationReportType(ChoiceEnum):
    draft = "Draft"
    consolidated = "Consolidated"

class ContractAllocationReport(models.Model):
    id = models.BigAutoField(db_column='ID_CONTR_ALLOC_REP', primary_key=True)  # Field name made lowercase.    
    reference_month = models.DateField(db_column='REFERENCE_MONTH')  # Field name made lowercase.
    
    class Meta:
        managed = False
        db_table = 'CONTR_ALLOC_REP'