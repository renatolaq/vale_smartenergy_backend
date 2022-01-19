from datetime import date
import json
import logging
from django.conf import settings

import notifications.business.email_service as email_service
import notifications.language.parser.parser as language_parser
from notifications.models import NotificationType, Notification

from notifications.language.parser.parser import (
    get_dict_tree
)

import notifications.business.notifications_business as notifications_business
from notifications.business.notifiable_modules import Modules

from SmartEnergy.handler_logging import HandlerLog

logger = HandlerLog()


class NotificationSignalBusiness:
    @staticmethod
    def get_notification_type(notification_type):
        # That's necessary because we don't guarantee in DB level that will exists only one type registered per event
        return NotificationType.objects.filter(
            notification_type=notification_type
        ).all()

    @staticmethod
    def get_active_notifications_by_type(notification_type, module_name):
        notifications = Notification.objects.filter(
            notification_type__in=NotificationSignalBusiness.get_notification_type(
                notification_type
            ),
            status=True,
            start_date__lte=date.today(),
            entity=module_name,
        )
        # inject extra query rules for reports module
        notifications_modified = list(map(notifications_business.NotificationBusiness.inject_reports_rules, notifications))

        return notifications_modified

    @staticmethod
    def dispatch_signal(sender, instance, **kwargs):
        try:
            if kwargs.get("created"):  # object already exists
                NotificationSignalBusiness.create_signal(sender, instance, **kwargs)
            else:
                NotificationSignalBusiness.update_signal(sender, instance, **kwargs)
        except Exception as e:
            logger.error(f"[NOTIFICATIONS]::Error dispatching notification {instance}: {e}",)

    @staticmethod
    def create_signal(sender, instance, **kwargs):
        available_notifications = NotificationSignalBusiness.get_active_notifications_by_type(
            NotificationType.CREATION,
            module_name=kwargs["notifiable_module"].module_name.value,
        )
        NotificationSignalBusiness.process_notification(
            instance, available_notifications, **kwargs
        )

    @staticmethod
    def update_signal(sender, instance, **kwargs):
        available_notifications = NotificationSignalBusiness.get_active_notifications_by_type(
            NotificationType.MODIFICATION,
            module_name=kwargs["notifiable_module"].module_name.value,
        )
        NotificationSignalBusiness.process_notification(
            instance, available_notifications, **kwargs
        )

    @staticmethod
    def process_notification(instance, available_notifications, **kwargs):

        for notification in available_notifications:
            result = []
            try:
                if notification.notification_rule_processed:
                    result = language_parser.get_entity_result(
                        dict_query=json.loads(notification.notification_rule_processed),
                        module=kwargs["notifiable_module"],
                        pk=instance.pk,
                    )
                if result or not notification.notification_rule_processed:
                    email_service.send_simple_mail_by_notification(
                        notification, instance
                    )
            except Exception as e:
                logger.error(f"[NOTIFICATIONS]::Error processing signal id {instance}: {e}",)  
