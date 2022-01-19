from ..notifiable_modules import Modules
from ..notifiable_modules_abstract import AbstractClassNotifiableModule
from global_variables.models import GlobalVariable, Variable, Unity, State

from django.db.models.signals import post_save
from django.dispatch import receiver
import notifications.business.signal_business as signal_business


class RegisterGlobalVariableNotifiableModule(AbstractClassNotifiableModule):
    main_model = GlobalVariable
    module_name = Modules.REGISTER_GLOBAL_VARIABLE

    def get_specified_fields(self):
        return [
            "status",
            "month",
            "year",
            "variable__name",
            "value",
            "state__name",
            "marketing",
            "unity__name"
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
            if field_name == "variable__name":
                variable_options = Variable.objects.all().values("name")
                field["options"] = [value["name"] for value in variable_options]

            if field_name == "unity__name":
                variable_options = Unity.objects.all().values("name")
                field["options"] = [value["name"] for value in variable_options]

            if field_name == "state__name":
                variable_options = State.objects.all().values("name")
                field["options"] = [value["name"] for value in variable_options]

    @staticmethod
    @receiver(post_save, sender=main_model)
    def post_save_signal_handler(sender, instance, **kwargs):
        kwargs["notifiable_module"] = RegisterGlobalVariableNotifiableModule()
        signal_business.NotificationSignalBusiness.dispatch_signal(
            sender, instance, **kwargs
        )
