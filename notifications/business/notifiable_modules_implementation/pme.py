from ..notifiable_modules import Modules
from ..notifiable_modules_abstract import AbstractClassNotifiableModule

from ...models import AlarmPME, EventTypePME, AlarmTypePME


class PMENotifiableModule(AbstractClassNotifiableModule):
    main_model = AlarmPME
    module_name = Modules.ALARM_PME

    def get_specified_fields(self):
        return [
            "status",
            "utc_creation",
            "utc_alarm_date",
            "alarm_type__name_alarms_type",
            "event_type__name_event_type",
            "gauge_point__status",
            "gauge_point__participation_sepp",
            "gauge_point__gauge_type",
            "gauge_point__connection_point",
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
            if field_name == "alarm_type__name_alarms_type":
                field["options"] = [
                    type_tuple[1] for type_tuple in AlarmTypePME.TYPE_CHOICES
                ]
            elif field_name == "event_type__name_event_type":
                field["options"] = [
                    type_tuple[1] for type_tuple in EventTypePME.TYPE_CHOICES
                ]

    @staticmethod
    def post_save_signal_handler(sender, instance, **kwargs):
        pass
