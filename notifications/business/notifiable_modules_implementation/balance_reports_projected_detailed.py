from ..notifiable_modules import Modules
from ..notifiable_modules_abstract import AbstractClassNotifiableModule
from consumption_metering_reports.models import Report

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
import notifications.business.signal_business as signal_business


class BalanceReportsProjectedDetailedNotifiableModule(AbstractClassNotifiableModule):
    main_model = Report
    module_name = Modules.BALANCE_REPORTS_PROJECT_DETAILED

    def get_specified_fields(self):
        return super().get_specified_fields()

    def get_fields(self):
        specified_fields = ('creation_date', 'report_name', 'status', 'month', 'year', 'id_reference__report_name', 'report_type__initials')

        non_related_fields, related_fields = super().get_fields()

        non_related_fields = [field for field in non_related_fields if field["name"] in specified_fields]
        related_fields = [field for field in related_fields if field["name"] in specified_fields]

        return non_related_fields, related_fields

    @staticmethod
    @receiver(post_save, sender=main_model)
    def post_save_signal_handler(sender, instance, **kwargs):
        # for this module when the user searchs for data a row is created in the database
        # ignore first creation on search
        if instance.status == 'T':
            return
        elif instance.status == 'S':
            kwargs["notifiable_module"] = BalanceReportsProjectedDetailedNotifiableModule()
            kwargs["created"] = True
            signal_business.NotificationSignalBusiness.dispatch_signal(
                sender, instance, **kwargs
            )
        else:
            kwargs["notifiable_module"] = BalanceReportsProjectedDetailedNotifiableModule()
            signal_business.NotificationSignalBusiness.dispatch_signal(
                sender, instance, **kwargs
            )
