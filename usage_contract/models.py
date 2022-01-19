from django.db import models
from django.utils import timezone
from company.models import Company


class Cct(models.Model):

    id_cct = models.AutoField(db_column='ID_CCT', primary_key=True)
    id_usage_contract = models.ForeignKey('EnergyTransmitter',
                                          models.DO_NOTHING,
                                          db_column='ID_USAGE_CONTRACT',
                                          related_name='cct')
    
    begin_date = models.DateField(db_column='BEGIN_DATE')
    end_date = models.DateField(db_column='END_DATE', blank=True, null=True)
    contract_value = models.DecimalField(db_column='CONTRACT_VALUE', max_digits=18, decimal_places=2)
    cct_number = models.DecimalField(db_column='CCT_NUMBER', max_digits=20, decimal_places=0, blank=True, null=True)
    length = models.DecimalField(db_column='LENGTH', max_digits=18, decimal_places=2, blank=True, null=True)
    destination = models.CharField(db_column='DESTINATION', max_length=512, blank=True, null=True)

    class Meta:
        db_table = 'CCT'


class ContractCycles(models.Model):

    id_contract_cycles = models.AutoField(db_column='ID_CONTRACT_CYCLES', primary_key=True)
    id_usage_contract = models.ForeignKey('EnergyTransmitter',
                                          models.DO_NOTHING,
                                          db_column='ID_USAGE_CONTRACT',
                                          related_name='contract_cycles')

    begin_date = models.DateField(db_column='BEGIN_DATE')
    end_date = models.DateField(db_column='END_DATE')
    peak_must = models.DecimalField(db_column='PEAK_MUST', max_digits=18, decimal_places=2)
    off_peak_must = models.DecimalField(db_column='OFF_PEAK_MUST', max_digits=18, decimal_places=2)
    peak_tax = models.DecimalField(db_column='PEAK_TAX', max_digits=18, decimal_places=2)
    off_peak_tax = models.DecimalField(db_column='OFF_PEAK_TAX', max_digits=18, decimal_places=2)

    class Meta:
        db_table = 'CONTRACT_CYCLES'


class EnergyTransmitter(models.Model):
    id_usage_contract = models.OneToOneField('UsageContract',
                                             models.DO_NOTHING,
                                             db_column='ID_USAGE_CONTRACT',
                                             primary_key=True,
                                             related_name='energy_transmitter')
    ons_code = models.CharField(db_column='ONS_CODE', max_length=20)
    aneel_resolution = models.CharField(db_column='ANEEL_RESOLUTION', max_length=30, blank=True, null=True)
    aneel_publication = models.DateField(db_column='ANEEL_PUBLICATION', blank=True, null=True)
    audit_renovation = models.CharField(db_column='AUDIT_RENOVATION', max_length=1, blank=True, null=True)
    renovation_period = models.DecimalField(db_column='RENOVATION_PERIOD',
                                            max_digits=18,
                                            decimal_places=0,
                                            blank=True,
                                            null=True)

    class Meta:
        db_table = 'ENERGY_TRANSMITTER'


class TaxModality(models.Model):
    id_tax_modality = models.AutoField(db_column='ID_TAX_MODALITY', primary_key=True)
    id_usage_contract = models.ForeignKey('EnergyDistributor',
                                          models.DO_NOTHING,
                                          db_column='ID_USAGE_CONTRACT',
                                          related_name='tax_modality')

    begin_date = models.DateField(db_column='BEGIN_DATE')
    end_date = models.DateField(db_column='END_DATE')
    peak_musd = models.DecimalField(db_column='PEAK_MUSD', max_digits=18, decimal_places=2, blank=True, null=True)
    off_peak_musd = models.DecimalField(db_column='OFF_PEAK_MUSD', max_digits=18, decimal_places=2, blank=True, null=True)
    peak_tax = models.DecimalField(db_column='PEAK_TAX', max_digits=18, decimal_places=2, blank=True, null=True)
    off_peak_tax = models.DecimalField(db_column='OFF_PEAK_TAX', max_digits=18, decimal_places=2, blank=True, null=True)
    unique_musd = models.DecimalField(db_column='UNIQUE_MUSD', max_digits=18, decimal_places=2, blank=True, null=True)
    unique_tax = models.DecimalField(db_column='UNIQUE_TAX', max_digits=18, decimal_places=2, blank=True, null=True)

    class Meta:
        db_table = 'TAX_MODALITY'


class EnergyDistributor(models.Model):

    id_usage_contract = models.OneToOneField('UsageContract',
                                             models.DO_NOTHING,
                                             db_column='ID_USAGE_CONTRACT',
                                             primary_key=True,
                                             related_name='energy_distributor')

    pn = models.DecimalField(db_column='PN', max_digits=18, decimal_places=0)
    installation = models.CharField(db_column='INSTALLATION', max_length=30)
    hourly_tax_modality = models.CharField(db_column='HOURLY_TAX_MODALITY', max_length=30)    
    audit_renovation = models.CharField(db_column='AUDIT_RENOVATION', max_length=1, blank=True, null=True)
    aneel_resolution = models.CharField(db_column='ANEEL_RESOLUTION', max_length=30, blank=True, null=True)
    aneel_publication = models.DateField(db_column='ANEEL_PUBLICATION', blank=True, null=True)
    renovation_period = models.DecimalField(db_column='RENOVATION_PERIOD', max_digits=18, decimal_places=0, blank=True, null=True)

    class Meta:
        db_table = 'ENERGY_DISTRIBUTOR'


class RatedVoltage(models.Model):
    id_rated_voltage = models.AutoField(db_column='ID_RATED_VOLTAGE', primary_key=True)
    voltages = models.DecimalField(db_column='VOLTAGE', max_digits=18, decimal_places=2)
    group = models.CharField(db_column='GROUP', max_length=6)
    subgroup = models.CharField(db_column='SUBGROUP', max_length=7)

    class Meta:
        db_table = 'RATED_VOLTAGE'


class RatePostException(models.Model):
    id_rate_post_exception = models.AutoField(db_column='ID_RATE_POST_EXCEPTION', primary_key=True)
    id_usage_contract = models.ForeignKey('UsageContract',
                                          models.DO_NOTHING,
                                          db_column='ID_USAGE_CONTRACT',
                                          related_name='rate_post_exception')

    begin_hour_clock = models.TimeField(db_column='BEGIN_HOUR_CLOCK', blank=True, null=True)
    end_hour_clock = models.TimeField(db_column='END_HOUR_CLOCK', blank=True, null=True)
    begin_date = models.DateField(db_column='BEGIN_DATE', blank=True, null=True)
    end_date = models.DateField(db_column='END_DATE', blank=True, null=True)

    class Meta:
        db_table = 'RATE_POST_EXCEPTION'


class TypeUsageContract(models.Model):
    id_usage_contract_type = models.AutoField(db_column='ID_USAGE_CONTRACT_TYPE', primary_key=True)
    description = models.CharField(db_column='DESCRIPTION', max_length=50)

    def __str__(self):
        return self.description

    class Meta:
        db_table = 'TYPE_USAGE_CONTRACT'


class UsageContract(models.Model):

    id_usage_contract = models.AutoField(db_column='ID_USAGE_CONTRACT', primary_key=True)
    usage_contract_type = models.ForeignKey(TypeUsageContract, models.DO_NOTHING, db_column='ID_USE_CONTRACT_TYPE')
    connection_point = models.CharField(db_column='CONNECTION_POINT', max_length=150)
    company = models.ForeignKey(Company, models.DO_NOTHING, db_column='ID_COMPANY', related_name='company')
    energy_dealer = models.ForeignKey(Company, models.DO_NOTHING, db_column='ID_ENERGY_DEALER', related_name='energy_dealer')

    peak_begin_time = models.TimeField(db_column='PEAK_BEGIN_TIME', blank=True, null=True)
    peak_end_time = models.TimeField(db_column='PEAK_END_TIME', blank=True, null=True)

    contract_number = models.CharField(db_column='CONTRACT_NUMBER', max_length=40)
    rated_voltage = models.ForeignKey(RatedVoltage, models.DO_NOTHING, db_column='ID_RATED_VOLTAGE')
    bought_voltage = models.DecimalField(db_column='BOUGHT_VOLTAGE', max_digits=18, decimal_places=2)
    power_factor = models.DecimalField(db_column='POWER_FACTOR', max_digits=18, decimal_places=2)
    tolerance_range = models.DecimalField(db_column='TOLERANCE_RANGE', max_digits=8, decimal_places=2)
    contract_value = models.DecimalField(db_column='CONTRACT_VALUE', max_digits=18, decimal_places=2)

    start_date = models.DateField(db_column='START_DATE')
    end_date = models.DateField(db_column='END_DATE')

    observation = models.CharField(max_length=512, db_column='OBSERVATION', default='', blank=True)

    create_date = models.DateTimeField(db_column='CREATE_DATE', default=timezone.now)
    status = models.CharField(db_column='STATUS', max_length=1)

    class Meta:
        db_table = 'USAGE_CONTRACT'

    def __str__(self):
        return str(self.id_usage_contract)


class UploadFileUsageContract(models.Model):

    id_upload_file_usage_contract = models.AutoField(db_column='ID_UPLOAD_FILE_USAGE_CONTRACT', primary_key=True)
    id_usage_contract = models.ForeignKey(UsageContract,
                                          models.DO_NOTHING,
                                          db_column='ID_USAGE_CONTRACT',
                                          related_name='upload_file',
                                          blank=True,
                                          null=True)

    file_name = models.CharField(max_length=256, db_column='FILE_NAME')
    file_path = models.FileField(upload_to='usage_contracts/', db_column='FILE_PATH')
    file_version = models.CharField(max_length=256, db_column='FILE_VERSION')
    observation = models.CharField(max_length=256, db_column='OBSERVATION', blank=True, default='')
    date_upload = models.DateTimeField(db_column='DATE_UPLOAD', default=timezone.now)

    class Meta:
        db_table = 'UPLOAD_FILE_USAGE_CONTRACT'

    def __str__(self):
        return self.file_name
