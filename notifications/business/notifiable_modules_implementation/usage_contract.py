from django.db.models.signals import post_save
from django.dispatch import receiver

from ..notifiable_modules import Modules
from ..notifiable_modules_abstract import AbstractClassNotifiableModule
from usage_contract.models import UsageContract, TypeUsageContract, ContractCycles, Cct, EnergyTransmitter
import notifications.business.signal_business as signal_business


class UsageContractNotifiableModule(AbstractClassNotifiableModule):
    main_model = UsageContract
    module_name = Modules.USAGE_CONTRACT

    def get_specified_fields(self):
        return [
            'create_date',
            'usage_contract_type__description',
            'company__company_name',
            'energy_dealer__company_name',
            'connection_point',
            'contract_number',
            'rated_voltage__voltages',
            'bought_voltage',
            'rated_voltage__group',
            'rated_voltage__subgroup',
            'power_factor',
            'tolerance_range',
            'start_date',
            'end_date',
            'observation',
            'contract_value',
            'energy_transmitter__ons_code',
            'energy_transmitter__renovation_period',
            'energy_transmitter__audit_renovation',
            'energy_transmitter__aneel_resolution',
            'energy_transmitter__aneel_publication',
            'energy_transmitter__contract_cycles__begin_date', 
            'energy_transmitter__contract_cycles__end_date', 
            'energy_transmitter__contract_cycles__peak_must', 
            'energy_transmitter__contract_cycles__peak_tax',
            'energy_transmitter__contract_cycles__off_peak_must', 
            'energy_transmitter__contract_cycles__off_peak_tax',
            'energy_transmitter__cct__cct_number',
            'energy_transmitter__cct__length',
            'energy_transmitter__cct__begin_date',
            'energy_transmitter__cct__end_date',
            'energy_transmitter__cct__destination',
            'energy_transmitter__cct__contract_value',
            'upload_file__file_name',
            'upload_file__file_path',
            'upload_file__file_version',
            'upload_file__observation',
            'upload_file__date_upload',
        ]

    def get_fields(self):
        non_related_fields, related_fields = super().get_fields()
        contract_cycle_fields = []
        cct_fields = []
        additional_usage_contract_fields = []

        try:
            additional_usage_contract_fields=super().get_fields(
                specific_model=UsageContract, source_path="id_usage_contract"
            )

            contract_cycle_fields=super().get_fields(
                specific_model=ContractCycles, source_path="energy_transmitter__contract_cycles"
            )
            contract_cycle_fields_specified_fields=[
                'energy_transmitter__contract_cycles__begin_date', 
                'energy_transmitter__contract_cycles__end_date', 
                'energy_transmitter__contract_cycles__peak_must', 
                'energy_transmitter__contract_cycles__off_peak_must', 
                'energy_transmitter__contract_cycles__peak_tax', 
                'energy_transmitter__contract_cycles__off_peak_tax'
            ]
            contract_cycle_fields = [
                k
                for k in contract_cycle_fields[0]
                if k["name"] in contract_cycle_fields_specified_fields
            ]

            cct_fields=super().get_fields(
                specific_model=Cct, source_path="energy_transmitter__cct"
            )
            cct_fields_specified_fields=[
                'energy_transmitter__cct__cct_number',
                'energy_transmitter__cct__length',
                'energy_transmitter__cct__begin_date',
                'energy_transmitter__cct__end_date',
                'energy_transmitter__cct__destination',
                'energy_transmitter__cct__contract_value',
            ]
            cct_fields = [
                k
                for k in cct_fields[0]
                if k["name"] in cct_fields_specified_fields
            ]

        except IndexError:
            pass

        related_fields += contract_cycle_fields + cct_fields

        specified_fields = self.get_specified_fields()

        non_related_fields = [
            field for field in non_related_fields if field["name"] in specified_fields
        ]
        related_fields = [
            field for field in related_fields if field["name"] in specified_fields
        ]

        self.add_field_options(non_related_fields, related_fields)

        return non_related_fields, related_fields

    def add_field_options(self, non_related_fields, related_fields):
        for field in non_related_fields + related_fields:
            field_name = field.get("name")
            if field_name == "usage_contract_type__description":
                usage_contract_types_description = TypeUsageContract.objects.all().values(
                    "description"
                )
                field["options"] = [
                    value["description"] for value in usage_contract_types_description
                ]

    @staticmethod
    @receiver(post_save, sender=main_model)
    def post_save_signal_handler(sender, instance, **kwargs):
        kwargs["notifiable_module"] = UsageContractNotifiableModule()
        signal_business.NotificationSignalBusiness.dispatch_signal(
            sender, instance, **kwargs
        )
