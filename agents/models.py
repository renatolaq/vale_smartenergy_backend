from django.db import models
from company.models import Company
from core.models import CceeDescription


# Create your models here.
class Agents(models.Model):
    id_agents = models.AutoField(db_column='ID_AGENTS', primary_key=True)  # Field name made lowercase.
    id_company = models.ForeignKey(Company, models.DO_NOTHING, db_column='ID_COMPANY', related_name='agents_company')  # Field name made lowercase.
    id_ccee = models.OneToOneField(CceeDescription, models.DO_NOTHING,
                                   db_column='ID_CCEE', related_name='ccee_agent')  # Field name made lowercase.
    vale_name_agent = models.CharField(db_column='VALE_NAME_AGENT', max_length=40)  # Field name made lowercase.
    status = models.CharField(db_column='STATUS', max_length=1)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'AGENTS'
