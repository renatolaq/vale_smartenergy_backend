from organization.models import ElectricalGrouping
from ..notifiable_modules import Modules
from ..notifiable_modules_abstract import AbstractClassNotifiableModule
from gauge_point.models import GaugePoint, GaugeType, SourcePme, MeterType

from django.db.models.signals import post_save
from django.dispatch import receiver
import notifications.business.signal_business as signal_business


class RegisterGaugePointNotifiableModule(AbstractClassNotifiableModule):
    main_model = GaugePoint
    module_name = Modules.REGISTER_GAUGE_POINT

    def get_specified_fields(self):
        return [
            "id_source__id_meter_type__description",
            "id_source__display_name",
            "id_gauge_type__description",
            "connection_point",
            "id_company__company_name",
            'id_ccee__code_ccee',
            "id_electrical_grouping__description",
            'participation_sepp',
        ]


    def get_fields(self):
        non_related_fields, related_fields = super().get_fields()
        additional_fields_source_pme = []
        try:
            additional_fields_source_pme = super().get_fields(
                specific_model=SourcePme, source_path="id_source"
            )
            additional_fields_source_pme = [
                k
                for k in additional_fields_source_pme[1]
                if k["name"] == "id_source__id_meter_type__description"
            ]
        except IndexError:
            pass

        related_fields += additional_fields_source_pme

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
            if field_name == "participation_sepp":
                field["options"] = ["S", "N"]

            if field_name == "gauge_type":
                field["options"] = ["fronteira", "principal", "setorial", "carga"]

            if field_name == "id_gauge_type__description":
                gauge_types = GaugeType.objects.all().values("description")
                field["options"] = [value["description"] for value in gauge_types]

            if field_name == "id_source__id_meter_type__description":
                meter_type = MeterType.objects.all().values("description")
                field["options"] = [value["description"] for value in meter_type]

            if field_name == "id_electrical_grouping__description":
                electrical_grouping = ElectricalGrouping.objects.all().values(
                    "description"
                )
                field["options"] = [
                    value["description"] for value in electrical_grouping
                ]

    @staticmethod
    @receiver(post_save, sender=main_model)
    def post_save_signal_handler(sender, instance, **kwargs):
        kwargs["notifiable_module"] = RegisterGaugePointNotifiableModule()
        signal_business.NotificationSignalBusiness.dispatch_signal(
            sender, instance, **kwargs
        )
