from transfer_contract_priority.models import TransferContractPriority
from cliq_contract.models import CliqContract
from energy_contract.models import EnergyContract
from profiles.models import Profile
from core.models import CceeDescription
from core.serializers import log, generic_update
from rest_framework import serializers


class TransferContractPrioritySerializer(serializers.ModelSerializer):

    class Meta:
        model = TransferContractPriority
        fields = ('id_transfer', 'id_contract_cliq', 'priority_number', 'status')
        depth = 0

    def __init__(self, *args, **kwargs):
        if 'context' in kwargs:
            self.user = kwargs['context']['request'].user
            self.observation_log = kwargs['context']['observation_log']
        else:
            self.user = ''
            self.observation_log = ''
        super(TransferContractPrioritySerializer, self).__init__(*args, **kwargs)

    def create(self, validated_data):
        cntrct_priority = TransferContractPriority.objects.create(**validated_data)
        log(TransferContractPriority, cntrct_priority.id_transfer, {}, cntrct_priority, self.user, self.observation_log, action="INSERT")
        return cntrct_priority

    def update(self, instance, validated_data):
        obj = generic_update(TransferContractPriority, instance.id_transfer, dict(validated_data), self.user, self.observation_log)
        return obj


class CliqContractSerializer(serializers.ModelSerializer):

    transaction_type = serializers.CharField(required=False, default='')
    flexibility = serializers.CharField(required=False, default='')
    mwm_volume = serializers.DecimalField(required=False, default=0, decimal_places=9, max_digits=18)
    contractual_loss = serializers.DecimalField(required=False, default=0, decimal_places=9, max_digits=18)

    class Meta:
        model = CliqContract
        fields = ('id_contract_cliq', 'id_vendor_profile', 'id_buyer_profile', 'id_contract',
                  'id_ccee', 'id_buyer_assets', 'id_buyer_asset_items','id_submarket',
                  'transaction_type', 'flexibility', 'mwm_volume', 'contractual_loss',
                  'status'
                  )
        depth = 1


class CliqContractPrioritySerializer(serializers.ModelSerializer):

    cliq_contract = CliqContractSerializer(many=False, source='id_contract_cliq', read_only=True)

    class Meta:
        model = TransferContractPriority

        fields = ('id_transfer', 'id_contract_cliq', 'priority_number', 'status', 'cliq_contract')

        depth = 0