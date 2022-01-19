from django.db import transaction
from .notifiable_modules_abstract import AbstractClassNotifiableModule
from notifications.business.notifiable_modules import Modules
from notifications.language.parser.parser import (
    get_dict_tree,
    get_result,
    get_string_validation,
    get_lexical_result,
)
from notifications.utils.list import find
from notifications.models import (
    NotificationTargetEmail,
    Notification,
    NotificationEmailField,
    NotificationFrequency,
    NotificationType,
)
import json
from django.shortcuts import get_object_or_404
from .notifiable_modules_implementation import *
from rest_framework import serializers

from ..generators.pdf_generator import generate_pdf
from ..generators.xlsx_generator import generate_xls

IMPLEMENTED_MODULES = {
    x.module_name: x for x in AbstractClassNotifiableModule.__subclasses__()
}


class NotifiableModulesFactory:
    @staticmethod
    def create_notifiable_module(module_name):
        """Create a notifiable module object. Returns None if the module is not yet notifiable."""
        notifiable_module = IMPLEMENTED_MODULES.get(module_name)

        return notifiable_module() if notifiable_module else None


class NotificationBusiness:
    fields_to_export = (
        "name",
        "notification_type",
        "notification_frequency",
        "notification_username",
        "start_date",
        "status",
    )

    @staticmethod
    def retrieve_modules_fields():
        modules_fields_result = []

        for module in Modules:
            notifiable_module = NotifiableModulesFactory.create_notifiable_module(
                module
            )
            if notifiable_module is not None:
                module_dict = {"text": module.value, "fields": []}
                non_related_fields, related_fields = notifiable_module.get_fields()

                ordered_fields = NotificationBusiness.module_sort_fields(notifiable_module, non_related_fields + related_fields)

                for field in ordered_fields:
                    # normally fields should be filtered on the get_fields but BALANCE_REPORTS require a field that should exist and not be listed for the frontend
                    if((module.value == 'BALANCE_REPORTS_GROSS' or module.value == 'BALANCE_REPORTS' or module.value == 'BALANCE_REPORTS_PROJECT_DETAILED') and field.get("name") == 'report_type__initials'):
                        pass
                    else:
                        module_dict["fields"].append(
                            {"name": field.get("name"), "options": field.get("options", [])}
                        )
                
                modules_fields_result.append(module_dict)

        return modules_fields_result

    @staticmethod
    def module_sort_fields(module, fields):
        sort_dict = {}
        specified_fields = module.get_specified_fields()
  
        def sort_func(field):
            return sort_dict[field['name']]

        if(specified_fields):
            for index, field in enumerate(specified_fields):
                sort_dict[field] = index

            return sorted(fields, key=sort_func)
        else:
            return fields

    @staticmethod
    def get_module_with_fields_by_name(module_name):
        modules = NotificationBusiness.retrieve_modules_fields()
        module = find(modules, "text", module_name)

        if not module:
            raise Exception("Module not found!")

        return module

    @staticmethod
    def execute_string(string, module_name):
        module = NotifiableModulesFactory.create_notifiable_module(Modules[module_name])

        # get syntatic tree
        dict_tree = get_dict_tree(string, module)

        # running script to guarantee it's runnable
        result = NotificationBusiness.run_query(dict_tree, module)

        return result

    @staticmethod
    def analyze_string(string, module_name):
        module = NotifiableModulesFactory.create_notifiable_module(Modules[module_name])

        return get_string_validation(string, module)

    @staticmethod
    def run_query(dict_tree, module):
        result = get_result(dict_tree, module)

        return result

    @staticmethod
    def process_create_request(data):
        notification_type = (
            NotificationType.objects.filter(notification_type=data["notification_type"])
            .values("pk")
            .first()
        )
        notification_frequency = (
            NotificationFrequency.objects.filter(
                notification_frequency=data["notification_frequency"]
            )
            .values("pk")
            .first()
        )

        if notification_type == None:
            raise serializers.ValidationError(
                {"notification_type": "Choice not found."}
            )
        if notification_frequency == None:
            raise serializers.ValidationError(
                {"notification_frequency": "Choice not found."}
            )

        data["notification_type"] = notification_type["pk"]
        data["notification_frequency"] = notification_frequency["pk"]

        string = data.get("notification_rule", None)
        if string is None:
            return data

        module_name = data["entity"]

        module = NotifiableModulesFactory.create_notifiable_module(Modules[module_name])

        # get syntatic tree
        dict_tree = get_dict_tree(string, module)

        # running script to guarantee it's runnable
        NotificationBusiness.run_query(dict_tree, module)

        notification_rule_processed = json.dumps(dict_tree)

        # add necessary entities
        data["notification_rule_processed"] = notification_rule_processed

        return data

    @staticmethod
    @transaction.atomic
    def update_notification(notification, data, log_strategy):
        """
        :param notification: old notification state
        :param data: new notification dict
        :param log_strategy: any class that implement save_log()
        """
        emails_data = data.pop("emails")
        email_fields_data = data.pop("email_fields", None)

        for field in data:
            setattr(
                notification, field, data.get(field, getattr(notification, field)),
            )

        NotificationBusiness.delete_notification_emails(notification)
        NotificationBusiness.create_notification_emails(notification, emails_data)

        NotificationBusiness.delete_notification_email_fields(notification)
        if (
            data["notification_frequency"].notification_frequency
            != NotificationFrequency.ON_EVENT
        ):
            NotificationBusiness.create_notification_email_fields(
                notification, email_fields_data
            )

        notification.save()
        log_strategy.update_log(updated_model_object=notification)
        return notification

    @staticmethod
    def delete_notification_emails(notification):
        NotificationTargetEmail.objects.filter(notification=notification).delete()

    @staticmethod
    def delete_notification_email_fields(notification):
        NotificationEmailField.objects.filter(notification=notification).delete()

    @staticmethod
    @transaction.atomic
    def create_notification(data, log_strategy):
        """
        :param data: notification dict
        :param log_strategy: any class that implement save_log()
        """
        emails_data = data.pop("emails")
        email_fields_data = data.pop("email_fields", None)

        notification = Notification.objects.create(**data)

        NotificationBusiness.prepopulate_notification_history(notification)

        NotificationBusiness.create_notification_emails(notification, emails_data)
        if email_fields_data:
            NotificationBusiness.create_notification_email_fields(
                notification, email_fields_data
            )

        log_strategy.save_log(model_object=notification)
        return notification

    @staticmethod
    def prepopulate_notification_history(notification):
        if (
            notification.notification_type.notification_type
            == NotificationType.VERIFICATION
            and notification.notification_frequency.notification_frequency
            == NotificationFrequency.ON_EVENT
        ):
            notifiable_module = NotifiableModulesFactory.create_notifiable_module(
                Modules(notification.entity)
            )
            notifiable_module.prepopulate_notification_history(notification)

    @staticmethod
    def create_notification_emails(notification, emails_data):
        for email in emails_data:
            NotificationTargetEmail.objects.create(notification=notification, **email)

    @staticmethod
    def create_notification_email_fields(notification, email_fields_data):
        for email_field in email_fields_data:
            NotificationEmailField.objects.create(
                notification=notification, **email_field
            )

    def check_available_name(name, notification_id):
        if name:
            name = str(name).replace(" ", "").lower()

        notification_qs = Notification.objects.extra(
            where=[f"LOWER(REPLACE(name,' ','')) = '{name}'"]
        )

        if notification_id is not None:
            get_object_or_404(Notification, pk=notification_id)
            notification_qs = notification_qs.exclude(id=notification_id)

        if not notification_qs:
            return {"name_exist": False}
        else:
            notification = notification_qs.first()
            if notification.status:
                return {"name_exist": True, "active": True}
            else:
                return {"name_exist": True, "active": False}

    @staticmethod
    def change_status(id, status):
        notification = Notification.objects.get(pk=id)
        notification.status = status
        notification.save()

        return {"id": notification.pk, "status": notification.status}

    @staticmethod
    def get_lexemes(string):
        result = get_lexical_result(string)

        return result.lexemes_dict

    @staticmethod
    def export(notifications, type, language="pt_BR"):
        data = {
            "fields": NotificationBusiness.fields_to_export,
            "notifications": notifications,
        }
        if type == "pdf":
            return generate_pdf(data, "Notifications", language)
        if type == "xlsx":
            return generate_xls(data, "Notifications", language)

    @staticmethod
    def concat_report_type(notification, report_type):
        rule = notification.notification_rule
        if not rule:
            rule = f"${{report_type__initials}}==\"{report_type}\""
            module_name = notification.entity
            module = NotifiableModulesFactory.create_notifiable_module(Modules[module_name])
            # get syntatic tree notification rule processed
            dict_tree = get_dict_tree(rule, module)
            notification.notification_rule_processed = json.dumps(dict_tree)
        else:
            rule = rule + f"&&${{report_type__initials}}==\"{report_type}\""
            module_name = notification.entity
            module = NotifiableModulesFactory.create_notifiable_module(Modules[module_name])
            # get syntatic tree notification rule processed
            dict_tree = get_dict_tree(rule, module)
            notification.notification_rule_processed = json.dumps(dict_tree)

        return notification

    @staticmethod
    def inject_reports_rules(notification):
        if(notification.entity == 'BALANCE_REPORTS_GROSS'):
            return NotificationBusiness.concat_report_type(notification, 'RCB')
        elif(notification.entity == 'BALANCE_REPORTS_PROJECT_DETAILED'):
            return NotificationBusiness.concat_report_type(notification, 'RPD')
        elif(notification.entity == 'BALANCE_REPORTS'):
            return NotificationBusiness.concat_report_type(notification, 'BDE')
        else:
            return notification
