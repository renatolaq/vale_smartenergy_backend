from ..notifiable_modules import Modules
from ..notifiable_modules_abstract import AbstractClassNotifiableModule
from occurrence_record.models import Occurrence, EventType
from organization.models import Product
from gauge_point.models import GaugePoint, SourcePme

from django.db.models.signals import post_save
from django.dispatch import receiver
import notifications.business.signal_business as signal_business


class OccurrenceRecordNotifiableModule(AbstractClassNotifiableModule):
    main_model = Occurrence
    module_name = Modules.OCCURRENCE_RECORD

    def get_specified_fields(self):
        return [
            "status",
            "events__gauge_point__id_source__display_name",
            "events__utc_events_begin",
            "events__event_type__name_event_type",
            "events__events_duration",
            "events__events_magnitude",
            "company__company_name",
            "occurrence_date",
            "electrical_grouping__description",
            "responsible",
            "phone",
            "cellphone",
            "carrier",
            "events__gauge_point__connection_point",
            "key_circuit_breaker_identifier",
            "applied_protection__description",
            "occurrence_type__description",
            "occurrence_duration",
            "occurrence_cause__description",
            "total_stop_time",
            "occurrence_product__product__description",
            "occurrence_product__lost_production",
            "occurrence_product__financial_loss",
            "description",
            "occurrenceattachment__attachment_revision",
            "occurrenceattachment__attachment_comments",
            "occurrenceattachment__attachment_path",
        ]

    def get_fields(self):
        non_related_fields, related_fields = super().get_fields()
        additional_deeper_fields = []

        deeper_fields = super().get_fields(
            specific_model=EventType,
            source_path="events__event_type"
        )
        additional_deeper_fields += deeper_fields[0]
        additional_deeper_fields += deeper_fields[1]

        deeper_fields = super().get_fields(
            specific_model=GaugePoint,
            source_path="events__gauge_point"
        )
        additional_deeper_fields += deeper_fields[0]
        additional_deeper_fields += deeper_fields[1]

        deeper_fields = super().get_fields(
            specific_model=Product,
            source_path="occurrence_product__product"
        )
        additional_deeper_fields += deeper_fields[0]
        additional_deeper_fields += deeper_fields[1]

        related_fields += additional_deeper_fields

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
            if field_name == "id_event__id_event_type__name_event_type":
                field["options"] = [
                    "Communication",
                    "Demand",
                    "Energy",
                    "Interruption",
                    "Sag",
                    "Swell",
                    "Transient",
                    "Voltage"
                ]

    @staticmethod
    @receiver(post_save, sender=main_model)
    def post_save_signal_handler(sender, instance, **kwargs):
        kwargs["notifiable_module"] = OccurrenceRecordNotifiableModule()
        signal_business.NotificationSignalBusiness.dispatch_signal(
            sender, instance, **kwargs
        )
