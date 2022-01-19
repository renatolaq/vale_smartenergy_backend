from ..notifiable_modules import Modules
from ..notifiable_modules_abstract import AbstractClassNotifiableModule
from agents.models import Agents
from balance_report_market_settlement.models import Profile

from django.db.models.signals import post_save
from django.dispatch import receiver
import notifications.business.signal_business as signal_business


class RegisterAgentNotifiableModule(AbstractClassNotifiableModule):
    main_model = Agents
    module_name = Modules.REGISTER_AGENT

    def get_specified_fields(self):
        return [
            'id_ccee__code_ccee',
            'id_ccee__name_ccee',
            "vale_name_agent",
            "id_company__company_name",
            'profile_agent__name_profile',
            'profile_agent__alpha',
            'profile_agent__status',
        ]

    def get_fields(self):
        non_related_fields, related_fields = super().get_fields()

        specified_fields = self.get_specified_fields()

        non_related_fields = [
            field for field in non_related_fields if field["name"] in specified_fields
        ]
        related_fields = [
            field for field in related_fields if field["name"] in specified_fields
        ]
        
        return non_related_fields, related_fields

    @staticmethod
    @receiver(post_save, sender=main_model)
    def post_save_signal_handler(sender, instance, **kwargs):
        kwargs["notifiable_module"] = RegisterAgentNotifiableModule()
        signal_business.NotificationSignalBusiness.dispatch_signal(
            sender, instance, **kwargs
        )
