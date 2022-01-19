from ..notifiable_modules import Modules
from ..notifiable_modules_abstract import AbstractClassNotifiableModule
from contract_dispatch.models import ContractDispatch

from django.db.models.signals import post_save
from django.dispatch import receiver
import notifications.business.signal_business as signal_business


class CceeContractDispatchNotifiableModule(AbstractClassNotifiableModule):
    main_model = ContractDispatch
    module_name = Modules.CCEE_CONTRACT_DISPATCH

    def get_specified_fields(self):
        return [
            "dispatch_date",
            "dispatch_username",
            "supply_date",
            "last_status_update_date",
            "contractdispatchcliqcontract__volume_on_dispatch",
            "contractdispatchcliqcontract__contract_status_on_dispatch"
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
        kwargs["notifiable_module"] = CceeContractDispatchNotifiableModule()
        signal_business.NotificationSignalBusiness.dispatch_signal(
            sender, instance, **kwargs
        )
