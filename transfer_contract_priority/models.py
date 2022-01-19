from django.db import models
from cliq_contract.models import CliqContract

# Create your models here.
class TransferContractPriority(models.Model):
    id_transfer = models.AutoField(db_column='ID_TRANSFER', primary_key=True)  # Field name made lowercase.
    id_contract_cliq = models.ForeignKey(CliqContract, models.DO_NOTHING, db_column='ID_CONTRACT_CLIQ', blank=True,
                                         null=True, related_name='cliq_priority')  # Field name made lowercase.
    priority_number = models.DecimalField(db_column='PRIORITY_NUMBER', max_digits=4, decimal_places=0, blank=True,
                                          null=True)  # Field name made lowercase.
    status = models.CharField(db_column='STATUS', max_length=1, blank=True, null=True)  # Field name made lowercase.
    
    class Meta:
        managed = False
        db_table = 'TRANSFER_CONTRACT_PRIORITY'
