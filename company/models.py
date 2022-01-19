from django.db import models


# Create your models here.
class Address(models.Model):

    id_address = models.AutoField(db_column='ID_ADDRESS', primary_key=True)  # Field name made lowercase.
    id_city = models.ForeignKey('City', models.DO_NOTHING, db_column='ID_CITY', blank=True, null=True, related_name='city')  # Field name made lowercase.
    street = models.CharField(db_column='STREET', max_length=100, blank=True, null=True)  # Field name made lowercase.
    neighborhood = models.CharField(db_column='NEIGHBORHOOD', max_length=100, blank=True,
                                    null=True)  # Field name made lowercase.
    number = models.DecimalField(db_column='NUMBER', max_digits=9, decimal_places=0, blank=True,
                                 null=True)  # Field name made lowercase.

    zip_code = models.CharField(db_column='ZIP_CODE', max_length=40, blank=True,
                                null=True)  # Field name made lowercase.
    complement = models.CharField(db_column='COMPLEMENT', max_length=30, blank=True,
                                  null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'ADDRESS'

class AccountType(models.Model):
    id_account_type = models.AutoField(db_column='ID_ACCOUNT_TYPE', primary_key=True)  # Field name made lowercase.
    description = models.CharField(db_column='DESCRIPTION', max_length=12)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'ACCOUNT_TYPE'


class BankAccount(models.Model):
    id_bank = models.AutoField(db_column='ID_BANK', primary_key=True)  # Field name made lowercase.
    id_company = models.ForeignKey('Company', models.DO_NOTHING, db_column='ID_COMPANY',
                                   related_name="id_company_bank")  # Field name made lowercase.
    bank = models.CharField(db_column='BANK', max_length=150)  # Field name made lowercase.
    account_type = models.ForeignKey('AccountType', models.DO_NOTHING, db_column='ID_ACCOUNT_TYPE')  # Field name made lowercase.
    account_number = models.CharField(db_column='ACCOUNT_NUMBER', max_length=12)  # Field name made lowercase.
    bank_agency = models.CharField(db_column='BANK_AGENCY', max_length=12)  # Field name made lowercase.
    other = models.CharField(db_column='OTHER', max_length=150, blank=True, null=True)  # Field name made lowercase.
    main_account = models.CharField(db_column='MAIN_ACCOUNT', max_length=1)  # Field name made lowercase.
    status = models.CharField(db_column='STATUS', max_length=1)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'BANK_ACCOUNT'


class City(models.Model):
    id_city = models.AutoField(db_column='ID_CITY', primary_key=True)  # Field name made lowercase.
    id_state = models.ForeignKey('State', models.DO_NOTHING, db_column='ID_STATE', blank=True,
                                 null=True)  # Field name made lowercase.
    city_name = models.CharField(db_column='CITY_NAME', max_length=40, blank=True,
                                 null=True)  # Field name made lowercase.
    initials = models.CharField(db_column='INITIALS', max_length=40, blank=True,
                                null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'CITY'


class Company(models.Model):
    id_company = models.AutoField(db_column='ID_COMPANY', primary_key=True)  # Field name made lowercase.
    id_address = models.ForeignKey(Address, models.DO_NOTHING, db_column='ID_ADDRESS', blank=True, null=True, related_name="address_company")  # Field name made lowercase.
    company_name = models.CharField(db_column='COMPANY_NAME', max_length=250)  # Field name made lowercase.
    legal_name = models.CharField(db_column='LEGAL_NAME', max_length=250)  # Field name made lowercase.
    registered_number = models.CharField(db_column='REGISTERED_NUMBER', max_length=12, blank=True, null=True)  # Field name made lowercase.
    type = models.CharField(db_column='TYPE', max_length=5)  # Field name made lowercase.
    state_number = models.CharField(db_column='STATE_NUMBER', max_length=18)  # Field name made lowercase.
    nationality = models.CharField(db_column='NATIONALITY', max_length=3)  # Field name made lowercase.
    id_sap = models.CharField(db_column='ID_SAP', unique=True, max_length=18)  # Field name made lowercase.
    characteristics = models.CharField(db_column='CHARACTERISTICS', max_length=30, blank=True, null=True)  # Field name made lowercase.
    status = models.CharField(db_column='STATUS', max_length=1)  # Field name made lowercase.
    create_date = models.DateTimeField(db_column='CREATE_DATE', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'COMPANY'


class CompanyContacts(models.Model):
    id_contacts = models.AutoField(db_column='ID_CONTACTS', primary_key=True)  # Field name made lowercase.
    id_company = models.ForeignKey(Company, models.DO_NOTHING, db_column='ID_COMPANY', related_name="id_company_contacts")  # Field name made lowercase.
    type = models.CharField(db_column='TYPE', max_length=15)  # Field name made lowercase.
    responsible = models.CharField(db_column='RESPONSIBLE', max_length=150)  # Field name made lowercase.
    email = models.CharField(db_column='EMAIL', max_length=150)  # Field name made lowercase.
    cellphone = models.CharField(db_column='CELLPHONE', max_length=30, blank=True, null=True)  # Field name made lowercase.
    phone = models.CharField(db_column='PHONE', max_length=30)  # Field name made lowercase.
    status = models.CharField(db_column='STATUS', max_length=1)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'COMPANY_CONTACTS'


class Country(models.Model):
    id_country = models.AutoField(db_column='ID_COUNTRY', primary_key=True)  # Field name made lowercase.
    name = models.CharField(db_column='NAME', max_length=30)  # Field name made lowercase.
    initials = models.CharField(db_column='INITIALS', max_length=4, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'COUNTRY'


class EletricUtilityCompany(models.Model):
    id_eletric_utility_company = models.AutoField(db_column='ID_ELETRIC_UTILITY_COMPANY',
                                                  primary_key=True)  # Field name made lowercase.
    id_company = models.OneToOneField(Company, models.DO_NOTHING, db_column='ID_COMPANY',
                                   related_name="id_company_eletric")  # Field name made lowercase.
    instaled_capacity = models.DecimalField(db_column='INSTALED_CAPACITY', max_digits=18, decimal_places=9, blank=True,
                                            null=True)  # Field name made lowercase.
    guaranteed_power = models.DecimalField(db_column='GUARANTEED_POWER', max_digits=18, decimal_places=9, blank=True,
                                           null=True)  # Field name made lowercase.
    regulatory_act = models.CharField(db_column='REGULATORY_ACT', max_length=30, blank=True,
                                      null=True)  # Field name made lowercase.
    internal_loss = models.DecimalField(db_column='INTERNAL_LOSS', max_digits=18, decimal_places=9, blank=True,
                                        null=True)  # Field name made lowercase.
    transmission_loss = models.DecimalField(db_column='TRANSMISSION_LOSS', max_digits=18, decimal_places=9, blank=True,
                                            null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'ELETRIC_UTILITY_COMPANY'
        unique_together = (('id_eletric_utility_company', 'id_company'),)


class Neighborhood(models.Model):
    id_neighborhood = models.AutoField(db_column='ID_NEIGHBORHOOD', primary_key=True)  # Field name made lowercase.
    id_city = models.ForeignKey(City, models.DO_NOTHING, db_column='ID_CITY', blank=True,
                                null=True)  # Field name made lowercase.
    neigborhood_name = models.CharField(db_column='NEIGBORHOOD_NAME', max_length=80, blank=True,
                                        null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'NEIGHBORHOOD'


class State(models.Model):
    id_state = models.AutoField(db_column='ID_STATE', primary_key=True)  # Field name made lowercase.
    id_country = models.ForeignKey(Country, models.DO_NOTHING, db_column='ID_COUNTRY', blank=True,
                                   null=True)  # Field name made lowercase.
    name = models.CharField(db_column='NAME', max_length=100, blank=True, null=True)  # Field name made lowercase.
    initials = models.CharField(db_column='INITIALS', max_length=4, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'STATE'