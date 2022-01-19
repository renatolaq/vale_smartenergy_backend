from django.db import models
from enumchoicefield import ChoiceEnum, EnumChoiceField

from .Revision import Revision
from company.models import Company
from cliq_contract.models import CliqContract

class SourceType(ChoiceEnum):
    contract = "contract"
    generation = "generation"

class Source(models.Model):
    id = models.BigAutoField(db_column='ID_CONTR_ALLOC_REP_SOURCE', primary_key=True)  # Field name made lowercase.
    revision = models.ForeignKey(Revision, models.DO_NOTHING, db_column='ID_CONTR_ALLOC_REP_REVISION')  # Field name made lowercase.
    unit = models.ForeignKey(Company, models.DO_NOTHING, db_column='ID_COMPANY')  # Field name made lowercase.
    contract = models.ForeignKey(CliqContract, models.DO_NOTHING, db_column='ID_CONTRACT_CLIQ')  # Field name made lowercase.
    type = EnumChoiceField(SourceType, db_column='TYPE', max_length=50)  # Field name made lowercase.    
    available_power = models.FloatField(db_column='AVAILABLE_POWER')
    available_for_sale = models.FloatField(db_column='AVAILABLE_FOR_SALE')
    cost = models.FloatField(db_column='COST')
    balance_id_origin = models.BigIntegerField(db_column='ID_BALANCE_ORIGIN')

    class Meta:
        managed = False
        db_table = 'CONTR_ALLOC_REP_SOURCE'