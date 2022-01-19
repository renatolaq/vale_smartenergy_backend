from django.db import models
from agents.models import Agents
from core.models import CceeDescription


# Create your models here.
class Profile(models.Model):
    id_profile = models.AutoField(db_column='ID_PROFILE', primary_key=True)  # Field name made lowercase.
    id_agents = models.ForeignKey(Agents, models.DO_NOTHING, db_column='ID_AGENTS', blank=True,
                                  null=True, related_name='profile_agent')  # Field name made lowercase.
    id_ccee = models.OneToOneField(CceeDescription, models.DO_NOTHING, db_column='ID_CCEE',
                                   unique=True, related_name='profile_ccee')  # Field name made lowercase.
    name_profile = models.CharField(db_column='NAME_PROFILE', max_length=40)  # Field name made lowercase.
    alpha = models.CharField(db_column='ALPHA', max_length=1)  # Field name made lowercase.
    encouraged_energy = models.BooleanField(db_column='ENCOURAGED_ENERGY')  # Field name made lowercase.    
    status = models.CharField(db_column='STATUS', max_length=1)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'PROFILE'


