from abc import ABC, abstractmethod

from notifications.models import NotificationEventHistory
from notifications.utils.list import (
    remove_primary_key_from_field_list,
    remove_keys_and_relations_from_field_list, remove_time_fields_from_field_list,
)


class AbstractClassNotifiableModule(ABC):
    @property
    @abstractmethod
    def main_model(self):
        pass

    @property
    @abstractmethod
    def module_name(self):
        pass

    @abstractmethod
    def get_fields(self, specific_model=None, source_path=None):
        """
        Get fields and related fields by depth 1 from any NotifiableModule.main_model
        Example: company -> usage_contract will return all company fields and all concrete fields from usage_contract (not relations)

        You can specify which module and in that case add a source_path
        It's used in cases that you want to get fields with depth 2.
        Exemple:
        You want to get module1->module2->module3
                1. call module1 get_fields
                2. in module1 notifiable module implementation call get_fields(specific_model=module2, source_path='module2')
                and then you'll do the depth 2 starting from module1 to module3

                You'll have as return something like
                module2__field
                module2__module3__field

        :return: Returns a dict with the field name formatted or not by related name and the django model field object itself

        :Examples:
        >>> any_notifiable_module.get_fields()
        {'name': 'id_company', 'object': <django.db.models.fields.AutoField: id_company>}
        {'name': 'id_company_bank__main_account', 'object': <django.db.models.fields.CharField: main_account>}
        """

        non_related_fields = []
        related_fields = []
        model = self.main_model if not specific_model else specific_model
        source = f"{source_path}__" if source_path else ""
        for module_field in list(
            filter(remove_primary_key_from_field_list, model._meta.concrete_fields,)
        ):
            if module_field.is_relation:
                self.add_related_values(module_field, related_fields, source)
            else:
                non_related_fields.append(
                    {"name": source + module_field.name, "object": module_field}
                )

        for module_field in model._meta.related_objects:
            self.add_related_values(module_field, related_fields, source)


        # remove time fields
        non_related_fields = list(filter(remove_time_fields_from_field_list, non_related_fields))
        related_fields = list(filter(remove_time_fields_from_field_list, related_fields))

        return non_related_fields, related_fields

    def add_related_values(self, module_field, related_fields_list, source_path=""):
        related_model_fields = list(
            filter(
                remove_keys_and_relations_from_field_list,
                module_field.related_model._meta.concrete_fields,
            )
        )
        for relate_model_field in related_model_fields:
            related_fields_list.append(
                {
                    "name": f"{source_path}{module_field.name}__{relate_model_field.name}",
                    "object": relate_model_field,
                }
            )

    def prepopulate_notification_history(self, notification):
        old_objects = self.main_model.objects.all()
        event_history_list = []
        for obj in old_objects:
            event_history = NotificationEventHistory(
                notification=notification, notification_entity_pk=obj.pk
            )
            event_history_list.append(event_history)

        # stay sharp that bulk_create is fast but doesn't trigger signals and other stuff
        NotificationEventHistory.objects.bulk_create(event_history_list)
        return event_history_list

    @staticmethod
    @abstractmethod
    def post_save_signal_handler(sender, instance, **kwargs):
        pass

    @abstractmethod
    def get_specified_fields(self):
        return None
