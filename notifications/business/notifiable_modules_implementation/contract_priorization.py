from ..notifiable_modules import Modules
from ..notifiable_modules_abstract import AbstractClassNotifiableModule
from contract_allocation_parameters.models.EnergyContractPrioritization import (
    EnergyContractPrioritization,
    EnergyContractPrioritizationType,
    EnergyContractPrioritizationSubtype
)

from django.db.models.signals import post_save
from django.dispatch import receiver
import notifications.business.signal_business as signal_business


class ContractPriorizationNotifiableModule(AbstractClassNotifiableModule):
    main_model = EnergyContractPrioritization
    module_name = Modules.CONTRACT_PRIORIZATION

    def get_specified_fields(self):
        return [
            "name",
            "type",
            "subtype",
            "revision__revision",
            "revision__active",
            "revision__change_at",
            "revision__user",
            "revision__order",
            "revision__contracts_edited",
            "revision__generators_edited",
            "revision__consumers_edited",
            "revision__parameters_edited",
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

        self.add_field_options(non_related_fields, related_fields)
        return non_related_fields, related_fields

    def add_field_options(self, non_related_fields, related_fields):
        for field in non_related_fields + related_fields:
            field_name = field.get("name")
            if field_name == "type":
                field["options"] = [
                    str(prioritization_type)
                    for prioritization_type in EnergyContractPrioritizationType
                ]
            if field_name == "subtype":
                field["options"] = [
                    str(prioritization_subtype)
                    for prioritization_subtype in EnergyContractPrioritizationSubtype
                ]

    @staticmethod
    @receiver(post_save, sender=main_model)
    def post_save_signal_handler(sender, instance, **kwargs):
        kwargs["notifiable_module"] = ContractPriorizationNotifiableModule()
        signal_business.NotificationSignalBusiness.dispatch_signal(
            sender, instance, **kwargs
        )
