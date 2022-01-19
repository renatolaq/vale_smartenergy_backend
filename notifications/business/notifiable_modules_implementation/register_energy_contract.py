from ..notifiable_modules import Modules
from ..notifiable_modules_abstract import AbstractClassNotifiableModule
from energy_contract.models import (
    EnergyContract,
    FlexibilizationType,
    Seasonal,
    Precification,
    Flexibilization
)
from cliq_contract.models import CliqContract
from profiles.models import Profile
from core.models import CceeDescription

from django.db.models.signals import post_save
from django.dispatch import receiver
import notifications.business.signal_business as signal_business


class RegisterEnergyContractNotifiableModule(AbstractClassNotifiableModule):
    main_model = EnergyContract
    module_name = Modules.REGISTER_ENERGY_CONTRACT

    def get_specified_fields(self):
        return [
            'modality',
            'sap_contract',
            'type',
            'id_seller_agents__vale_name_agent',
            'id_buyer_agents__vale_name_agent',
            'id_seller_profile__name_profile',
            'id_buyer_profile__name_profile',
            'start_supply',
            'end_supply',
            'volume_mwm',
            'volume_mwh',
            'id_energy_product__description',
            'contract_name',
            'contract_status',
            'signing_data',
            'market',
            'precif_energy_contract__base_price_mwh',
            'precif_energy_contract__base_price_date',
            'precif_energy_contract__birthday_date',
            'precif_energy_contract__active_price_mwh',
            'precif_energy_contract__retusd',
            'precif_energy_contract__id_variable__name',
            'flexib_energy_contract__flexibility_type',
            'flexib_energy_contract__id_flexibilization_type__id_flexibilization_type__flexibilization',
            'flexib_energy_contract__min_flexibility_pu_peak',
            'flexib_energy_contract__max_flexibility_pu_peak',
            'flexib_energy_contract__min_flexibility_pu_offpeak',
            'flexib_energy_contract__max_flexibility_pu_offpeak',
            'flexib_energy_contract__proinfa_flexibility',
            'modul_energy_contract__modulation_type',
            'modul_energy_contract__min_modulation_pu',
            'modul_energy_contract__max_modulation_pu',
            'season_energy_contract__type_seasonality',
            'season_energy_contract__season_min_pu',
            'season_energy_contract__season_max_pu',
            'guaran_energy_contract__month_hour',
            'guaran_energy_contract__guaranteed_value',
            'guaran_energy_contract__emission_date',
            'guaran_energy_contract__effective_date',
            'contractattachment__name',
            'contractattachment__revision',
            'contractattachment__comments',
            'contractattachment__path',
            'cliq_contract__id_ccee__id_ccee__code_ccee',
            'cliq_contract__ccee_type_contract',
            'cliq_contract__transaction_type',
            'cliq_contract__flexibility',
            'cliq_contract__id_buyer_profile__id_buyer_profile__name_profile',
            'cliq_contract__id_vendor_profile__id_vendor_profile__name_profile',
            'cliq_contract__mwm_volume_peak',
            'cliq_contract__mwm_volume_offpeak',
            'cliq_contract__contractual_loss',
            'cliq_contract__submarket',
        ]

    def get_fields(self):
        non_related_fields, related_fields = super().get_fields()
        additional_precification_fields = []
        additional_flexibilization_fields = []
        cliq_contract_id_ccee_fields = []
        cliq_contract_id_buyer_profile_fields = []
        cliq_contract_id_vendor_profile_fields = []

        try:
            additional_precification_fields = super().get_fields(
                specific_model=Precification, source_path="precif_energy_contract"
            )
            additional_precification_fields = [
                k
                for k in additional_precification_fields[1]
                if k["name"] == "precif_energy_contract__id_variable__name"
            ]

            additional_flexibilization_fields = super().get_fields(
                specific_model=FlexibilizationType, source_path='flexib_energy_contract__id_flexibilization_type'
            )
            additional_flexibilization_fields = [
                k
                for k in additional_flexibilization_fields[1]
                if k["name"] == 'flexib_energy_contract__id_flexibilization_type__id_flexibilization_type__flexibilization'
            ]

            cliq_contract_id_ccee_fields = super().get_fields(
                specific_model=CceeDescription, source_path="cliq_contract__id_ccee"
            )
            cliq_contract_id_ccee_fields = [
                k
                for k in cliq_contract_id_ccee_fields[1]
                if k["name"] == 'cliq_contract__id_ccee__id_ccee__code_ccee'
            ]

            cliq_contract_id_buyer_profile_fields = super().get_fields(
                specific_model=Profile, source_path="cliq_contract__id_buyer_profile"
            )
            cliq_contract_id_buyer_profile_fields = [
                k
                for k in cliq_contract_id_buyer_profile_fields[1]
                if k['name'] == 'cliq_contract__id_buyer_profile__id_buyer_profile__name_profile'
            ]

            cliq_contract_id_vendor_profile_fields = super().get_fields(
                specific_model=Profile, source_path="cliq_contract__id_vendor_profile"
            )
            cliq_contract_id_vendor_profile_fields = [
                k
                for k in cliq_contract_id_vendor_profile_fields[1]
                if k['name'] == 'cliq_contract__id_vendor_profile__id_vendor_profile__name_profile'
            ]

        except IndexError:
            pass

        related_fields += additional_precification_fields + additional_flexibilization_fields + cliq_contract_id_ccee_fields + cliq_contract_id_buyer_profile_fields + cliq_contract_id_vendor_profile_fields

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
            if field_name == "type":
                field["options"] = ["V", "C"]

            if field_name == "market":
                field["options"] = [0, 1]

            if field_name == "modality":
                field["options"] = ["Longo prazo", "Curto prazo", "Transferência"]

            if field_name == "contract_status":
                field["options"] = ["AS", "EA", "NE"]

            if field_name == "flexib_energy_contract__flexibility_type":
                flex_type = FlexibilizationType.objects.all().values("flexibilization")
                field["options"] = [value["flexibilization"] for value in flex_type]

            if field_name == "flexib_energy_contract__proinfa_flexibility":
                field["options"] = [0, 1]

            if field_name == "season_energy_contract__type_seasonality":
                field["options"] = ["Flat", "Sazonalizado"]

            if field_name == "modul_energy_contract__modulation_type":
                field["options"] = ["Flat", "Modulado Declarado", "Modulação por Carga"]
            if field_name == "precif_energy_contract__id_variable__name":
                field["options"] = ["IGP-M", "IPCA"]

    @staticmethod
    @receiver(post_save, sender=main_model)
    def post_save_signal_handler(sender, instance, **kwargs):
        kwargs["notifiable_module"] = RegisterEnergyContractNotifiableModule()
        signal_business.NotificationSignalBusiness.dispatch_signal(
            sender, instance, **kwargs
        )
