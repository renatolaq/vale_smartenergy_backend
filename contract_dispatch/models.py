from django.db import models

from agents.models import Agents
from assets.models import Submarket
from cliq_contract.models import CliqContract
from enumchoicefield import ChoiceEnum, EnumChoiceField
from enum import Enum

from profiles.models import Profile


class ContractDispatchOperation(Enum):
    REGISTER = "register"
    VALIDATE_REGISTER = "validate_register"
    ADJUSTMENT = "adjustment"
    VALIDATE_ADJUSTMENT = "validate_adjustment"


class ContractDispatchCategory(Enum):
    TRANSFER = "transfer"
    PURCHASE = "purchase"
    SALE = "sale"


class CliqContractStatus(ChoiceEnum):
    NOT_SENT = "Not Sent"
    WAITING_CCEE = "Waiting CCEE"
    REGISTERED_NOT_VALIDATED = "Registered not validated"
    REGISTERED_VALIDATED = "Registered validated"
    ADJUSTED_NOT_VALIDATED = "Adjusted not validated"
    ADJUSTED_VALIDATED = "Adjusted validated"
    CANCELED = "Canceled"
    ERROR = "Error"


class ContractDispatch(models.Model):

    id = models.AutoField(db_column='ID_CONTRACT_DISPATCH', primary_key=True)
    dispatch_date = models.DateTimeField(db_column='DISPATCH_DATE', blank=False, null=False)
    contracts = models.ManyToManyField(
            CliqContract,
            through='ContractDispatchCliqContract',
            through_fields=('contract_dispatch', 'cliq_contract'),
    )
    dispatch_username = models.CharField(db_column='DISPATCH_USERNAME', max_length=50, blank=False, null=False)
    supply_date = models.DateTimeField(db_column='SUPPLY_DATE', blank=False, null=False)
    last_status_update_date = models.DateTimeField(db_column='LAST_STATUS_UPDATE_DATE', blank=False, null=False)

    class Meta:
        managed = False
        db_table = 'CONTRACT_DISPATCH'


class CliqCceeProcessment(models.Model):
    id_cliq_ccee_processment = models.AutoField(db_column='ID_CLIQ_CCEE_PROCESSMENT', primary_key=True)
    id_processment = models.DecimalField(
        db_column="ID_PROCESSMENT",
        max_digits=9,
        decimal_places=0
    )
    cliq_contract = models.ForeignKey(
        CliqContract,
        db_column='ID_CLIQ_CONTRACT',
        on_delete=models.CASCADE
    )
    code_transaction = models.CharField(db_column='CODE_TRANSACTION', max_length=150, null=True)
    created_at = models.DateTimeField(db_column='DATE_CREATION')
    updated_at = models.DateTimeField(db_column='DATE_UPDATE', null=True)
    processed = models.CharField(db_column='PROCESSED', max_length=1)
    type = models.CharField(db_column='TYPE_PROCESSMENT', max_length=150)

    class Meta:
        managed = False
        db_table = 'CLIQ_CCEE_PROCESSMENT'


class CliqCceeProcessmentResult(models.Model):
    id_cliq_ccee_processment_result = models.AutoField(db_column='ID_CLIQ_CCEE_PROCESSMENT_RESULT', primary_key=True)
    id_cliq_ccee_processment = models.ForeignKey(
        CliqCceeProcessment,
        db_column='ID_CLIQ_CCEE_PROCESSMENT',
        on_delete=models.CASCADE,
        related_name="processment_result"
    )
    cliq_code = models.CharField(db_column='CODE_CLIQ', max_length=50, null=True)
    status = models.CharField(db_column='STATUS', max_length=50)
    description = models.CharField(db_column='DESCRIPTION', max_length=150)
    created_at = models.DateTimeField(db_column='DATE_CREATION')

    class Meta:
        managed = False
        db_table = 'CLIQ_CCEE_PROCESSMENT_RESULT'


class ContractDispatchCliqContract(models.Model):
    id_contract_dispatch_cliq_contract = models.AutoField(db_column='ID_CONTRACT_DISPATCH_CLIQ_CONTRACT', primary_key=True)
    cliq_ccee_processment = models.ForeignKey(
        CliqCceeProcessment,
        db_column='ID_CLIQ_CCEE_PROCESSMENT',
        on_delete=models.DO_NOTHING,
        null=True,
        default=None
        )
    cliq_contract = models.ForeignKey(
        CliqContract,
        db_column='ID_CLIQ_CONTRACT',
        on_delete=models.CASCADE,
        related_name='contract_dispatches'
        )
    contract_dispatch = models.ForeignKey(ContractDispatch, db_column='ID_CONTRACT_DISPATCH', on_delete=models.CASCADE)
    volume_on_dispatch = models.DecimalField(db_column='VOLUME_ON_DISPATCH', max_digits=18,
                                            decimal_places=9)
    contract_status_on_dispatch = EnumChoiceField(CliqContractStatus, db_column='CONTRACT_STATUS', max_length=50, blank=False, null=False)

    class Meta:
        managed = False
        db_table = 'CONTRACT_DISPATCH_CLIQ_CONTRACT'
        unique_together = ('contract_dispatch', 'cliq_contract')


class CliqContractCurrentStatus(models.Model):
    id_cliq_contract_current_status = models.AutoField(db_column='ID_CLIQ_CONTRACT_CURRENT_STATUS', primary_key=True)
    cliq_contract = models.ForeignKey(
        CliqContract,
        db_column='ID_CLIQ_CONTRACT',
        on_delete=models.CASCADE,
        related_name='contract_dispatch_status'
        )
    status = EnumChoiceField(CliqContractStatus, db_column='CONTRACT_STATUS', max_length=50, blank=False, null=False)
    status_date = models.DateField(db_column='STATUS_DATE', blank=False, null=False)
    updated_at = models.DateTimeField(db_column='UPDATED_AT', auto_now=True)
    
    class Meta:
        managed = False
        db_table = 'CLIQ_CONTRACT_CURRENT_STATUS'
        unique_together = ('cliq_contract','status_date')


class CliqContractCCEEState(models.Model):
    id_cliq_contract_ccee_state = models.AutoField(db_column='ID_CLIQ_CONTRACT_CCEE_STATE', primary_key=True)
    id_contract_cliq = models.ForeignKey(
        CliqContract,
        db_column='ID_CONTRACT_CLIQ',
        on_delete=models.DO_NOTHING
    )
    submarket = models.ForeignKey(
        Submarket,
        db_column='ID_SUBMARKET',
        on_delete=models.DO_NOTHING
    )
    buyer_agent = models.ForeignKey(Agents, models.DO_NOTHING, db_column='ID_BUYER_AGENT', null=True, related_name="buyer_agent_ccee_state")
    seller_agent = models.ForeignKey(Agents, models.DO_NOTHING, db_column='ID_SELLER_AGENT', null=True, related_name="seller_agent_ccee_state")
    created_at = models.DateTimeField(db_column='CREATED_AT', auto_now_add=True)
    updated_at = models.DateTimeField(db_column='UPDATED_AT', auto_now=True)

    class Meta:
        managed = True
        db_table = 'CLIQ_CONTRACT_CCEE_STATE'


class CliqContractCCEEPeriodInfo(models.Model):
    id_cliq_contract_ccee_state_period = models.AutoField(db_column='ID_CLIQ_CONTRACT_CCEE_STATE_PERIOD', primary_key=True)
    cliq_contract_ccee_state = models.ForeignKey(
        CliqContractCCEEState,
        db_column='ID_CLIQ_CONTRACT_CCEE_STATE',
        on_delete=models.CASCADE,
    )
    volume = models.DecimalField(db_column='AMOUNT', max_digits=18, decimal_places=2)
    date = models.DateField(db_column="DATE")

    created_at = models.DateTimeField(db_column='CREATED_AT', auto_now_add=True)
    updated_at = models.DateTimeField(db_column='UPDATED_AT', auto_now=True)

    class Meta:
        managed = True
        db_table = 'CLIQ_CONTRACT_CCEE_STATE_PERIOD_INFO'
        unique_together = ('cliq_contract_ccee_state', 'date')