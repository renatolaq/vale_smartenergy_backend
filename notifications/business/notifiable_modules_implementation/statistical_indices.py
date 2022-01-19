from ..notifiable_modules import Modules
from ..notifiable_modules_abstract import AbstractClassNotifiableModule
from statistical_indexes.models import StatisticalIndex, CostType
from statistical_indexes.views import CompaniesViewSet

from django.db.models.signals import post_save
from django.dispatch import receiver
import notifications.business.signal_business as signal_business


class StatisticalIndices(AbstractClassNotifiableModule):
    main_model = StatisticalIndex
    module_name = Modules.STATISTICAL_INDICES

    def get_specified_fields(self):
        return [
            "id_reference__month",
            "id_reference__year",
            "associated_company",
            "id_reference__transaction_type",
            "id_reference__cost_type",
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
            if field_name == "associated_company":
                field["options"] = [
                    value.get("company_name")
                    for value in CompaniesViewSet.queryset.values()
                ]
            if field_name == "id_reference__cost_type":
                field["options"] = [
                    value[0]
                    for value in CostType.choices()
                ]

    @staticmethod
    @receiver(post_save, sender=main_model)
    def post_save_signal_handler(sender, instance, **kwargs):
        kwargs["notifiable_module"] = StatisticalIndices()
        signal_business.NotificationSignalBusiness.dispatch_signal(
            sender, instance, **kwargs
        )
