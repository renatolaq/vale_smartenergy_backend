# Generated by Django 2.1.11 on 2019-09-17 19:53

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Address',
            fields=[
                ('id_address', models.AutoField(db_column='ID_ADDRESS', primary_key=True, serialize=False)),
                ('street', models.CharField(blank=True, db_column='STREET', max_length=100, null=True)),
                ('neighborhood', models.CharField(blank=True, db_column='NEIGHBORHOOD', max_length=100, null=True)),
                ('number', models.DecimalField(blank=True, db_column='NUMBER', decimal_places=0, max_digits=9, null=True)),
                ('zip_code', models.CharField(blank=True, db_column='ZIP_CODE', max_length=40, null=True)),
                ('complement', models.CharField(blank=True, db_column='COMPLEMENT', max_length=30, null=True)),
            ],
            options={
                'db_table': 'ADDRESS',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='BankAccount',
            fields=[
                ('id_bank', models.AutoField(db_column='ID_BANK', primary_key=True, serialize=False)),
                ('bank', models.CharField(db_column='BANK', max_length=12)),
                ('account_type', models.CharField(db_column='ACCOUNT_TYPE', max_length=12)),
                ('account_number', models.CharField(db_column='ACCOUNT_NUMBER', max_length=12)),
                ('bank_agency', models.CharField(db_column='BANK_AGENCY', max_length=12)),
                ('other', models.CharField(blank=True, db_column='OTHER', max_length=12, null=True)),
                ('main_account', models.CharField(db_column='MAIN_ACCOUNT', max_length=1)),
                ('status', models.CharField(db_column='STATUS', max_length=1)),
            ],
            options={
                'db_table': 'BANK_ACCOUNT',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='City',
            fields=[
                ('id_city', models.AutoField(db_column='ID_CITY', primary_key=True, serialize=False)),
                ('city_name', models.CharField(blank=True, db_column='CITY_NAME', max_length=40, null=True)),
                ('initials', models.CharField(blank=True, db_column='INITIALS', max_length=40, null=True)),
            ],
            options={
                'db_table': 'CITY',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Company',
            fields=[
                ('id_company', models.AutoField(db_column='ID_COMPANY', primary_key=True, serialize=False)),
                ('company_name', models.CharField(db_column='COMPANY_NAME', max_length=40)),
                ('registered_number', models.CharField(db_column='REGISTERED_NUMBER', max_length=12)),
                ('type', models.CharField(db_column='TYPE', max_length=5)),
                ('state_number', models.CharField(db_column='STATE_NUMBER', max_length=18)),
                ('nationality', models.CharField(db_column='NATIONALITY', max_length=3)),
                ('id_sap', models.CharField(db_column='ID_SAP', max_length=18, unique=True)),
                ('characteristics', models.CharField(db_column='CHARACTERISTICS', max_length=30)),
                ('status', models.CharField(db_column='STATUS', max_length=1)),
                ('create_date', models.DateTimeField(blank=True, db_column='CREATE_DATE', null=True)),
            ],
            options={
                'db_table': 'COMPANY',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='CompanyContacts',
            fields=[
                ('id_contacts', models.AutoField(db_column='ID_CONTACTS', primary_key=True, serialize=False)),
                ('type', models.CharField(db_column='TYPE', max_length=15)),
                ('responsible', models.CharField(db_column='RESPONSIBLE', max_length=30)),
                ('email', models.CharField(db_column='EMAIL', max_length=30)),
                ('cellphone', models.CharField(db_column='CELLPHONE', max_length=13)),
                ('phone', models.CharField(db_column='PHONE', max_length=30)),
                ('status', models.CharField(db_column='STATUS', max_length=1)),
            ],
            options={
                'db_table': 'COMPANY_CONTACTS',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Country',
            fields=[
                ('id_country', models.AutoField(db_column='ID_COUNTRY', primary_key=True, serialize=False)),
                ('name', models.CharField(db_column='NAME', max_length=30)),
                ('initials', models.CharField(blank=True, db_column='INITIALS', max_length=4, null=True)),
            ],
            options={
                'db_table': 'COUNTRY',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='EletricUtilityCompany',
            fields=[
                ('id_eletric_utility_company', models.AutoField(db_column='ID_ELETRIC_UTILITY_COMPANY', primary_key=True, serialize=False)),
                ('instaled_capacity', models.DecimalField(blank=True, db_column='INSTALED_CAPACITY', decimal_places=9, max_digits=18, null=True)),
                ('guaranteed_power', models.DecimalField(blank=True, db_column='GUARANTEED_POWER', decimal_places=9, max_digits=18, null=True)),
                ('regulatory_act', models.CharField(blank=True, db_column='REGULATORY_ACT', max_length=30, null=True)),
                ('internal_loss', models.DecimalField(blank=True, db_column='INTERNAL_LOSS', decimal_places=9, max_digits=18, null=True)),
                ('transmission_loss', models.DecimalField(blank=True, db_column='TRANSMISSION_LOSS', decimal_places=9, max_digits=18, null=True)),
            ],
            options={
                'db_table': 'ELETRIC_UTILITY_COMPANY',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Neighborhood',
            fields=[
                ('id_neighborhood', models.AutoField(db_column='ID_NEIGHBORHOOD', primary_key=True, serialize=False)),
                ('neigborhood_name', models.CharField(blank=True, db_column='NEIGBORHOOD_NAME', max_length=80, null=True)),
            ],
            options={
                'db_table': 'NEIGHBORHOOD',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Region',
            fields=[
                ('id_region', models.AutoField(db_column='ID_REGION', primary_key=True, serialize=False)),
                ('name', models.CharField(blank=True, db_column='NAME', max_length=30, null=True)),
                ('type', models.CharField(blank=True, db_column='TYPE', max_length=30, null=True)),
            ],
            options={
                'db_table': 'REGION',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='State',
            fields=[
                ('id_state', models.AutoField(db_column='ID_STATE', primary_key=True, serialize=False)),
                ('name', models.CharField(blank=True, db_column='NAME', max_length=100, null=True)),
                ('initials', models.CharField(blank=True, db_column='INITIALS', max_length=4, null=True)),
            ],
            options={
                'db_table': 'STATE',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='TypeAddess',
            fields=[
                ('id_type', models.AutoField(db_column='ID_TYPE', primary_key=True, serialize=False)),
                ('public_place_type', models.CharField(blank=True, db_column='PUBLIC_PLACE_TYPE', max_length=40, null=True)),
            ],
            options={
                'db_table': 'TYPE_ADDESS',
                'managed': False,
            },
        ),
    ]
