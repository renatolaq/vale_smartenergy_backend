from ..notifiable_modules import Modules
from ..notifiable_modules_abstract import AbstractClassNotifiableModule
from cliq_contract.models import CliqContract

from django.db.models.signals import post_save
from django.dispatch import receiver
import notifications.business.signal_business as signal_business


class CceeContractsNotifiableModule(AbstractClassNotifiableModule):
    main_model = CliqContract
    module_name = Modules.CCEE_CONTRACTS

    def get_specified_fields(self):
        return [
            "id_ccee__code_ccee",
            "ccee_type_contract",
            "transaction_type",
            "flexibility",
            "id_vendor_profile__name_profile",
            "id_buyer_profile__name_profile",
            "mwm_volume",
            "mwm_volume_offpeak",
            "contractual_loss",
            "id_submarket__description",
            "submarket"
        ]

    def get_fields(self):
        non_related_fields, related_fields = super().get_fields()

        specified_fields = self.get_specified_fields()

        try:
            non_related_fields = [
                field
                for field in non_related_fields
                if field["name"] in specified_fields
            ]
            related_fields = [
                field
                for field in related_fields
                if field["name"] in specified_fields
            ]
        except IndexError:
            pass

        return non_related_fields, related_fields

    @staticmethod
    @receiver(post_save, sender=main_model)
    def post_save_signal_handler(sender, instance, **kwargs):
        kwargs["notifiable_module"] = CceeContractsNotifiableModule()
        signal_business.NotificationSignalBusiness.dispatch_signal(
            sender, instance, **kwargs
        )
