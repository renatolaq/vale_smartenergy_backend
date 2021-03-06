# Generated by Django 2.1.11 on 2020-02-11 13:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('organization', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id_product', models.AutoField(db_column='ID_PRODUCT', primary_key=True, serialize=False)),
                ('description', models.CharField(blank=True, db_column='DESCRIPTION', max_length=30, null=True)),
                ('status', models.CharField(blank=True, db_column='STATUS', max_length=1, null=True)),
            ],
            options={
                'db_table': 'PRODUCT',
                'managed': False,
            },
        ),
    ]
