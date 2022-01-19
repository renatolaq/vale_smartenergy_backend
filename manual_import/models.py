from django.db import models


class UploadFile(models.Model):

    FILE_TYPE = (
        ('KSB1', 'KSB1'),
        ('FBL3N', 'FBL3N'),
        ('CCEE', 'CCEE'),
        ('PDCT', 'PDCT'),
        ('DSHB', 'DSHB'),
    )

    id = models.AutoField(db_column='ID', primary_key=True)
    user_name = models.CharField(u'User', db_column='USER_NAME',  max_length=50, default='no_user')
    date_upload = models.DateTimeField('Data upload', db_column='DATE_UPLOAD', auto_now_add=True)
    file_name = models.CharField('Nome Arquivo', max_length=150, db_column='FILE_NAME', default='')
    file_path = models.FileField(upload_to='need_process/', db_column='FILE_PATH')
    file_type = models.CharField(max_length=256, choices=FILE_TYPE, db_column='FILE_TYPE')
    send_status = models.SmallIntegerField('Status', db_column='SEND_STATUS', default=0)
    msg = models.TextField('Erro', db_column='MSG', blank=True, null=True, default='')

    class Meta:
        verbose_name = 'Upload'
        verbose_name_plural = 'Uploads'
        ordering = ['id']
        db_table = 'UPLOAD_FILE'


class Ksb1(models.Model):
    id_ksb1 = models.AutoField(db_column='ID_KSB1', primary_key=True)
    id_import_source = models.DecimalField(db_column='ID_IMPORT_SOURCE', max_digits=9, decimal_places=0)
    utc_creation = models.DateTimeField(db_column='UTC_CREATION')
    cost_center = models.CharField(db_column='COST_CENTER', max_length=50)
    cost_element_description = models.CharField(db_column='COST_ELEMENT_DESCRIPTION', max_length=50)
    incoming_date = models.DateTimeField(db_column='INCOMING_DATE')
    incoming_time = models.TimeField(db_column='INCOMING_TIME')
    release_date = models.DateTimeField(db_column='RELEASE_DATE')
    document_number = models.CharField(db_column='DOCUMENT_NUMBER', max_length=50)
    time_period = models.DecimalField(db_column='TIME_PERIOD', max_digits=8, decimal_places=0)
    exercise = models.DecimalField(db_column='EXERCISE', max_digits=8, decimal_places=0)
    company = models.CharField(db_column='COMPANY', max_length=50)
    mr_value = models.DecimalField(db_column='MR_VALUE', max_digits=18, decimal_places=9)
    business_partner = models.CharField(db_column='BUSINESS_PARTNER', max_length=50, blank=True, null=True)
    cost_element = models.CharField(db_column='COST_ELEMENT', max_length=50, blank=True, null=True)
    title = models.CharField(db_column='TITLE', max_length=50, blank=True, null=True)
    order_text = models.CharField(db_column='ORDER_TEXT', max_length=50, blank=True, null=True)
    objects_currency_value = models.DecimalField(db_column='OBJECTS_CURRENCY_VALUE', max_digits=18, decimal_places=9, blank=True, null=True)
    total_incoming_quantity = models.DecimalField(db_column='TOTAL_INCOMING_QUANTITY', max_digits=18, decimal_places=9, blank=True, null=True)
    username = models.CharField(db_column='USERNAME', max_length=50, blank=True, null=True)
    purchasing_document = models.CharField(db_column='PURCHASING_DOCUMENT', max_length=50, blank=True, null=True)
    referenced_document_number = models.CharField(db_column='REFERENCED_DOCUMENT_NUMBER', max_length=50, blank=True, null=True)
    document_type = models.CharField(db_column='DOCUMENT_TYPE', max_length=50, blank=True, null=True)
    material = models.CharField(db_column='MATERIAL', max_length=50, blank=True, null=True)
    offset_account_description = models.CharField(db_column='OFFSET_ACCOUNT_DESCRIPTION', max_length=50, blank=True, null=True)
    partner_object = models.CharField(db_column='PARTNER_OBJECT', max_length=50, blank=True, null=True)
    posting_line = models.DecimalField(db_column='POSTING_LINE', max_digits=8, decimal_places=0, blank=True, null=True)
    value_category = models.CharField(db_column='VALUE_CATEGORY', max_length=50, blank=True, null=True)
    debit_or_credit_indicator = models.CharField(db_column='DEBIT_OR_CREDIT_INDICATOR', max_length=50, blank=True, null=True)
    reference_document_category = models.CharField(db_column='REFERENCE_DOCUMENT_CATEGORY', max_length=50, blank=True, null=True)
    exchange_rate_category = models.CharField(db_column='EXCHANGE_RATE_CATEGORY', max_length=50, blank=True, null=True)
    document_date = models.DateTimeField(db_column='DOCUMENT_DATE', blank=True, null=True)
    effective_date = models.DateTimeField(db_column='EFFECTIVE_DATE', blank=True, null=True)
    cost_element_title = models.CharField(db_column='COST_ELEMENT_TITLE', max_length=50, blank=True, null=True)
    object_title = models.CharField(db_column='OBJECT_TITLE', max_length=50, blank=True, null=True)
    source_object_title = models.CharField(db_column='SOURCE_OBJECT_TITLE', max_length=50, blank=True, null=True)
    partner_object_title = models.CharField(db_column='PARTNER_OBJECT_TITLE', max_length=50, blank=True, null=True)
    partner_company = models.CharField(db_column='PARTNER_COMPANY', max_length=50, blank=True, null=True)
    recording_time = models.TimeField(db_column='RECORDING_TIME', blank=True, null=True)
    ledger = models.CharField(db_column='LEDGER', max_length=50, blank=True, null=True)
    operative_version_row = models.DecimalField(db_column='OPERATIVE_VERSION_ROW', max_digits=8, decimal_places=0, blank=True, null=True)
    acc_currency = models.CharField(db_column='ACC_CURRENCY', max_length=50, blank=True, null=True)
    transaction_currency = models.CharField(db_column='TRANSACTION_CURRENCY', max_length=50, blank=True, null=True)
    object_currency = models.CharField(db_column='OBJECT_CURRENCY', max_length=50, blank=True, null=True)
    report_currency = models.CharField(db_column='REPORT_CURRENCY', max_length=50, blank=True, null=True)
    creation_time = models.DateTimeField(db_column='CREATION_TIME', blank=True, null=True)
    personal_number = models.DecimalField(db_column='PERSONAL_NUMBER', max_digits=8, decimal_places=0, blank=True, null=True)
    objectname = models.CharField(db_column='OBJECTNAME', max_length=50, blank=True, null=True)
    source_object = models.CharField(db_column='SOURCE_OBJECT', max_length=50, blank=True, null=True)
    transaction_name = models.CharField(db_column='TRANSACTION_NAME', max_length=50, blank=True, null=True)
    original_transaction = models.CharField(db_column='ORIGINAL_TRANSACTION', max_length=50, blank=True, null=True)
    reference_transaction = models.CharField(db_column='REFERENCE_TRANSACTION', max_length=50, blank=True, null=True)
    partner_order = models.CharField(db_column='PARTNER_ORDER', max_length=50, blank=True, null=True)
    partner_object_class = models.CharField(db_column='PARTNER_OBJECT_CLASS', max_length=50, blank=True, null=True)
    period_to = models.DecimalField(db_column='PERIOD_TO', max_digits=8, decimal_places=0, blank=True, null=True)
    period_from = models.DecimalField(db_column='PERIOD_FROM', max_digits=8, decimal_places=0, blank=True, null=True)
    segment = models.CharField(db_column='SEGMENT', max_length=50, blank=True, null=True)
    partner_segment = models.CharField(db_column='PARTNER_SEGMENT', max_length=50, blank=True, null=True)
    source_object_type = models.CharField(db_column='SOURCE_OBJECT_TYPE', max_length=50, blank=True, null=True)
    debt_type = models.CharField(db_column='DEBT_TYPE', max_length=50, blank=True, null=True)
    partner_object_type_1 = models.CharField(db_column='PARTNER_OBJECT_TYPE_1', max_length=50, blank=True, null=True)
    object_type_1 = models.CharField(db_column='OBJECT_TYPE_1', max_length=50, blank=True, null=True)
    object_type_2 = models.CharField(db_column='OBJECT_TYPE_2', max_length=50, blank=True, null=True)
    partner_object_type_2 = models.CharField(db_column='PARTNER_OBJECT_TYPE_2', max_length=50, blank=True, null=True)
    tp_source_object = models.CharField(db_column='TP_SOURCE_OBJECT', max_length=50, blank=True, null=True)
    posted_unit_measure = models.CharField(db_column='POSTED_UNIT_MEASURE', max_length=50, blank=True, null=True)
    referred_organizational_unit = models.CharField(db_column='REFERRED_ORGANIZATIONAL_UNIT', max_length=50, blank=True, null=True)
    currency_variable_value = models.DecimalField(db_column='CURRENCY_VARIABLE_VALUE', max_digits=18, decimal_places=9, blank=True, null=True)
    mtransac_variable_value = models.DecimalField(db_column='MTRANSAC_VARIABLE_VALUE', max_digits=18, decimal_places=9, blank=True, null=True)
    mobj_variable_value = models.DecimalField(db_column='MOBJ_VARIABLE_VALUE', max_digits=18, decimal_places=9, blank=True, null=True)
    transaction_currency_value = models.DecimalField(db_column='TRANSACTION_CURRENCY_VALUE', max_digits=18, decimal_places=9, blank=True, null=True)
    acc_currency_value = models.DecimalField(db_column='ACC_CURRENCY_VALUE', max_digits=18, decimal_places=9, blank=True, null=True)
    version_value = models.CharField(db_column='VERSION_VALUE', max_length=50, blank=True, null=True)
    acc_fixed_currency_value = models.DecimalField(db_column='ACC_FIXED_CURRENCY_VALUE', max_digits=18, decimal_places=9, blank=True, null=True)
    tr_fixed_currency_value = models.DecimalField(db_column='TR_FIXED_CURRENCY_VALUE', max_digits=18, decimal_places=9, blank=True, null=True)
    obj_fixed_currency_value = models.DecimalField(db_column='OBJ_FIXED_CURRENCY_VALUE', max_digits=18, decimal_places=9, blank=True, null=True)
    relat_fixed_currency_value = models.DecimalField(db_column='RELAT_FIXED_CURRENCY_VALUE', max_digits=18, decimal_places=9, blank=True, null=True)
    activity_type = models.CharField(db_column='ACTIVITY_TYPE', max_length=50, blank=True, null=True)
    measurement_unit = models.CharField(db_column='MEASUREMENT_UNIT', max_length=50, blank=True, null=True)
    total_amount = models.DecimalField(db_column='TOTAL_AMOUNT', max_digits=18, decimal_places=9, blank=True, null=True)
    partner_operation = models.CharField(db_column='PARTNER_OPERATION', max_length=50, blank=True, null=True)
    upload_file = models.ForeignKey(UploadFile, models.DO_NOTHING, db_column='ID_UPLOAD_FILE')

    class Meta:
        managed = False
        db_table = 'KSB1'


class Fbl34N(models.Model):

    id_fbl34n = models.AutoField(db_column='ID_FBL34N', primary_key=True)
    id_import_source = models.DecimalField(db_column='ID_IMPORT_SOURCE', max_digits=9, decimal_places=0)
    utc_creation = models.DateTimeField(db_column='UTC_CREATION')
    open_start_comp_symbol = models.CharField(db_column='OPEN_START_COMP_SYMBOL', max_length=40, blank=True, null=True)
    account = models.CharField(db_column='ACCOUNT', max_length=40, blank=True, null=True)
    credit_debit_code = models.CharField(db_column='CREDIT_DEBIT_CODE', max_length=40, blank=True, null=True)
    document_number = models.CharField(db_column='DOCUMENT_NUMBER', max_length=40, blank=True, null=True)
    company = models.CharField(db_column='COMPANY', max_length=40)
    profit_center = models.CharField(db_column='PROFIT_CENTER', max_length=40, blank=True, null=True)
    release_date = models.DateTimeField(db_column='RELEASE_DATE')
    document_type = models.CharField(db_column='DOCUMENT_TYPE', max_length=40, blank=True, null=True)
    document_date = models.CharField(db_column='DOCUMENT_DATE', max_length=40, blank=True, null=True)
    amount_domestic_currency = models.DecimalField(db_column='AMOUNT_DOMESTIC_CURRENCY', max_digits=18, decimal_places=9, blank=True, null=True)
    internal_currency = models.CharField(db_column='INTERNAL_CURRENCY', max_length=40)
    amount_document_currency = models.DecimalField(db_column='AMOUNT_DOCUMENT_CURRENCY', max_digits=18, decimal_places=9, blank=True, null=True)
    business_partner = models.CharField(db_column='BUSINESS_PARTNER', max_length=40, blank=True, null=True)
    document_currency = models.CharField(db_column='DOCUMENT_CURRENCY', max_length=40, blank=True, null=True)
    text = models.CharField(db_column='TEXT_FIELD', max_length=40, blank=True, null=True)
    reference = models.CharField(db_column='REFERENCE', max_length=40, blank=True, null=True)
    incoming_date = models.DateTimeField(db_column='INCOMING_DATE')
    incoming_time = models.TimeField(db_column='INCOMING_TIME')
    exercise = models.DecimalField(db_column='EXERCISE', max_digits=18, decimal_places=9)
    accounting_period = models.CharField(db_column='ACCOUNTING_PERIOD', max_length=40)
    username = models.CharField(db_column='USERNAME', max_length=40, blank=True, null=True)
    amount_inmi2 = models.DecimalField(db_column='AMOUNT_INMI2', max_digits=18, decimal_places=9, blank=True, null=True)
    internal_currency_2 = models.CharField(db_column='INTERNAL_CURRENCY_2', max_length=40, blank=True, null=True)
    account_type = models.CharField(db_column='ACCOUNT_TYPE', max_length=40, blank=True, null=True)
    invoice_reference = models.CharField(db_column='INVOICE_REFERENCE', max_length=40, blank=True, null=True)
    center = models.CharField(db_column='CENTER', max_length=40, blank=True, null=True)
    payment_reference = models.CharField(db_column='PAYMENT_REFERENCE', max_length=40, blank=True, null=True)
    type_cta_contrapart = models.CharField(db_column='TYPE_CTA_CONTRAPART', max_length=40, blank=True, null=True)
    user_name_complet = models.CharField(db_column='USER_NAME_COMPLET', max_length=40, blank=True, null=True)
    operation_reference = models.CharField(db_column='OPERATION_REFERENCE', max_length=40, blank=True, null=True)
    document_header_text = models.CharField(db_column='DOCUMENT_HEADER_TEXT', max_length=40, blank=True, null=True)
    transaction_code = models.CharField(db_column='TRANSACTION_CODE', max_length=40, blank=True, null=True)
    purchasing_document = models.CharField(db_column='PURCHASING_DOCUMENT', max_length=40, blank=True, null=True)
    material = models.CharField(db_column='MATERIAL', max_length=40, blank=True, null=True)
    basic_measurement_unit = models.CharField(db_column='BASIC_MEASUREMENT_UNIT', max_length=40, blank=True, null=True)
    amount = models.DecimalField(db_column='AMOUNT', max_digits=18, decimal_places=9, blank=True, null=True)
    tax_domicile = models.CharField(db_column='TAX_DOMICILE', max_length=40, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'FBL34N'


class AggregationType(models.Model):
    id_aggregation = models.AutoField(db_column='ID_AGGREGATION', primary_key=True)  # Field name made lowercase.
    aggregation_type = models.CharField(db_column='AGGREGATION_TYPE', max_length=15, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'AGGREGATION_TYPE'


class Measurements(models.Model):

    id_measurements = models.AutoField(db_column='ID_MEASUREMENTS', primary_key=True)
    measure_name = models.CharField(db_column='MEASUREMENT_NAME', max_length=400)
    unity = models.CharField(db_column='UNITY', max_length=8, blank=True, null=True)
    frequency = models.CharField(db_column='FREQUENCY', max_length=30)

    class Meta:
        managed = False
        db_table = 'MEASUREMENTS'


class GaugeDataTemp(models.Model):

    id_measurements = models.DecimalField(db_column='ID_MEASUREMENTS', max_digits=9, decimal_places=0)
    id_import_source = models.DecimalField(db_column='ID_IMPORT_SOURCE', max_digits=9, decimal_places=0)
    id_gauge = models.DecimalField(db_column='ID_GAUGE', max_digits=9, decimal_places=0)
    utc_creation = models.DateTimeField(db_column='UTC_CREATION')
    utc_gauge = models.DateTimeField(db_column='UTC_GAUGE', blank=True, null=True)
    value = models.DecimalField(db_column='VALUE', max_digits=18, decimal_places=9, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'GAUGE_DATA_TEMP'

