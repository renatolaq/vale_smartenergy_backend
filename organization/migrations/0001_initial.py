# Generated by Django 2.1.11 on 2019-09-22 14:33

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AccountantArea',
            fields=[
                ('id_accountant', models.AutoField(db_column='ID_ACCOUNTANT', primary_key=True, serialize=False)),
                ('description', models.CharField(blank=True, db_column='DESCRIPTION', max_length=40, null=True)),
                ('status', models.CharField(blank=True, db_column='STATUS', max_length=1, null=True)),
            ],
            options={
                'db_table': 'ACCOUNTANT_AREA',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Business',
            fields=[
                ('id_business', models.AutoField(db_column='ID_BUSINESS', primary_key=True, serialize=False)),
                ('description', models.CharField(blank=True, db_column='DESCRIPTION', max_length=40, null=True)),
                ('status', models.CharField(blank=True, db_column='STATUS', max_length=1, null=True)),
            ],
            options={
                'db_table': 'BUSINESS',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='DirectorBoard',
            fields=[
                ('id_director', models.AutoField(db_column='ID_DIRECTOR', primary_key=True, serialize=False)),
                ('initials', models.CharField(blank=True, db_column='INITIALS', max_length=40, null=True)),
                ('description', models.CharField(blank=True, db_column='DESCRIPTION', max_length=40, null=True)),
                ('status', models.CharField(blank=True, db_column='STATUS', max_length=1, null=True)),
            ],
            options={
                'db_table': 'DIRECTOR_BOARD',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Segment',
            fields=[
                ('id_segment', models.AutoField(db_column='ID_SEGMENT', primary_key=True, serialize=False)),
                ('description', models.CharField(blank=True, db_column='DESCRIPTION', max_length=30, null=True)),
                ('status', models.CharField(blank=True, db_column='STATUS', max_length=1, null=True)),
            ],
            options={
                'db_table': 'SEGMENT',
                'managed': False,
            },
        ),
    ]
