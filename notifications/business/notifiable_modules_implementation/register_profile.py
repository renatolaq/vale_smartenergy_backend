from ..notifiable_modules import Modules
from ..notifiable_modules_abstract import AbstractClassNotifiableModule
from profiles.models import Profile

from django.db.models.signals import post_save
from django.dispatch import receiver
import notifications.business.signal_business as signal_business


class RegisterProfileNotifiableModule(AbstractClassNotifiableModule):
    main_model = Profile
    module_name = Modules.REGISTER_PROFILE

    def get_specified_fields(self):
        return [
            "name_profile",
            'alpha',
            'encouraged_energy',
            "id_ccee__code_ccee",
            "id_agents__vale_name_agent",
            "id_ccee__name_ccee",
        ]

    def get_fields(self):
        non_related_fields, related_fields = super().get_fields()

        self.add_field_options(non_related_fields, related_fields)

        specified_fields = self.get_specified_fields()

        non_related_fields = [
        field for field in non_related_fields if field["name"] in specified_fields
        ]
        related_fields = [
        field for field in related_fields if field["name"] in specified_fields
        ]
        return non_related_fields, related_fields

    def add_field_options(self, non_related_fields, related_fields):
        for field in non_related_fields + related_fields:
            field_name = field.get("name")

            if field_name == "alpha":
                field["options"] = ["S", "N"]

            if field_name == "encouraged_energy":
                field["options"] = ["S", "N"]

    @staticmethod
    @receiver(post_save, sender=main_model)
    def post_save_signal_handler(sender, instance, **kwargs):
        kwargs["notifiable_module"] = RegisterProfileNotifiableModule()
        signal_business.NotificationSignalBusiness.dispatch_signal(
            sender, instance, **kwargs
        )
