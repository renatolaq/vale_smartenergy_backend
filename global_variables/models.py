from django.db import models
import json

class Country(models.Model):
    id = models.AutoField(db_column='ID_COUNTRY', primary_key=True)
    name = models.CharField(db_column='NAME', max_length=30)
    initials = models.CharField(db_column='INITIALS', max_length=4, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'COUNTRY'


class State(models.Model):
    id = models.AutoField(db_column='ID_STATE', primary_key=True)
    country = models.ForeignKey(Country, on_delete=models.DO_NOTHING, db_column='ID_COUNTRY')
    name = models.CharField(db_column='NAME', max_length=100)
    initials = models.CharField(db_column='INITIALS', max_length=4, blank=True, null=True)
    
    def __str__(self):
        """A string representation of the model."""
        return self.name
    
    class Meta:
        managed = False
        db_table = 'STATE'


class VariableType(models.Model):
    id = models.AutoField(db_column='ID_VARIABLE', primary_key=True)
    name = models.CharField(db_column='NAME', max_length=30)

    class Meta:
        managed = False
        db_table = 'VARIABLE_TYPE'


class Variable(models.Model):
    id = models.AutoField(db_column='ID_VARIABLE', primary_key=True)
    type = models.ForeignKey('VariableType', on_delete=models.DO_NOTHING, db_column='TYPE_ID_VARIABLE')
    name = models.CharField(db_column='NAME', max_length=40)

    def __str__(self):
        """A string representation of the model."""
        return self.name

    class Meta:
        managed = False
        db_table = 'VARIABLE'


class Unity(models.Model):
    id = models.AutoField(db_column='ID_UNITY', primary_key=True)
    name = models.CharField(db_column='NAME', max_length=30)
    description = models.CharField(db_column='DESCRIPTION', max_length=100)

    def __str__(self):
        """A string representation of the model."""
        return self.name

    class Meta:
        managed = False
        db_table = 'UNITY_TABLE'


class GlobalVariable(models.Model):
    id = models.AutoField(db_column='ID_GLOBAL_VARIABLE', primary_key=True)
    variable = models.ForeignKey('Variable', on_delete=models.DO_NOTHING, db_column='ID_VARIABLE', null=True)
    unity = models.ForeignKey('Unity', db_column='ID_UNITY', on_delete=models.DO_NOTHING, null=True)
    state = models.ForeignKey('State', related_name='global_variable', on_delete=models.DO_NOTHING, db_column='ID_STATE', null=True)
    value = models.DecimalField(db_column='VALUE', max_digits=18, decimal_places=9, blank=True, null=True)  # Field name made lowercase.
    month = models.DecimalField(db_column='MONTH', max_digits=2, decimal_places=0, blank=True, null=True)  # Field name made lowercase.
    year = models.DecimalField(db_column='YEAR', max_digits=4, decimal_places=0, blank=True, null=True)  # Field name made lowercase.
    marketing = models.BooleanField(db_column='MARKETING_FLAG', default=False)
    status = models.BooleanField(db_column='STATUS', default=True)
    
    class Meta:
        managed = False
        db_table = 'GLOBAL_VARIABLE'

class Log(models.Model):
    id = models.AutoField(db_column='ID_LOG', primary_key=True)
    field_pk = models.DecimalField(db_column='FIELD_PK', max_digits=9, decimal_places=0, null=True)
    table_name = models.CharField(db_column='TABLE_NAME', max_length=30, blank=True, null=True)
    action_type = models.CharField(db_column='ACTION_TYPE', max_length=30, blank=True, null=True)
    old_value = models.TextField(db_column='OLD_VALUE', blank=True, null=True)
    new_value = models.TextField(db_column='NEW_VALUE', blank=True, null=True)
    observation = models.TextField(db_column='OBSERVATION', blank=True, null=True)
    date = models.DateTimeField(db_column='DATE', auto_now_add=True, blank=True, null=True)
    user = models.TextField(db_column='USER', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'LOG'

class LogEntity:
    def __init__(self, field_pk, table_name, action_type, new_value, old_value, observation, date, user):
        self.field_pk = field_pk
        self.table_name = table_name
        self.action_type = action_type
        self.new_value = new_value
        self.old_value = old_value
        self.observation = observation
        self.date = date
        self.user = user

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, 
            sort_keys=True, indent=4)




