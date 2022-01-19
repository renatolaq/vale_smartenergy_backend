# Generated by Django 2.1.11 on 2020-02-11 13:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AssetsComposition',
            fields=[
                ('id_assets_composition', models.AutoField(db_column='ID_ASSETS_COMPOSITION', primary_key=True, serialize=False)),
                ('status', models.CharField(blank=True, db_column='STATUS', max_length=1, null=True)),
            ],
            options={
                'db_table': 'ASSETS_COMPOSITION',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='NominalTension',
            fields=[
                ('id_rated_voltage', models.AutoField(db_column='ID_RATED_VOLTAGE', primary_key=True, serialize=False)),
                ('tension', models.DecimalField(db_column='TENSION', decimal_places=9, max_digits=18)),
            ],
            options={
                'db_table': 'nominal_tension',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='SeasonalityProinfa',
            fields=[
                ('id_seasonality_proinfa', models.AutoField(db_column='ID_SEASONALITY_PROINFA', primary_key=True, serialize=False)),
            ],
            options={
                'db_table': 'SEASONALITY_PROINFA',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='TypePermissionContract',
            fields=[
                ('id_use_contract_type', models.AutoField(db_column='ID_USE_CONTRACT_TYPE', primary_key=True, serialize=False)),
                ('description', models.CharField(db_column='DESCRIPTION', max_length=50)),
            ],
            options={
                'db_table': 'type_permission_contract',
                'managed': False,
            },
        ),
        migrations.AlterModelTable(
            name='assets',
            table='assets',
        ),
    ]
