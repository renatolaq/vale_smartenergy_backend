# Generated by Django 2.1.11 on 2019-09-17 19:53

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Agents',
            fields=[
                ('id_agents', models.AutoField(db_column='ID_AGENTS', primary_key=True, serialize=False)),
                ('vale_name_agent', models.CharField(db_column='VALE_NAME_AGENT', max_length=40)),
                ('status', models.CharField(db_column='STATUS', max_length=1)),
            ],
            options={
                'db_table': 'AGENTS',
                'managed': False,
            },
        ),
    ]
