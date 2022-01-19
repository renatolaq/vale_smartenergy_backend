from notifications.business.notifiable_modules import Modules
from notifications.models import (
    Notification,
    NotificationFrequency,
    NotificationType,
    NotificationEventHistory,
    NotificationHistory,
)
from notifications.language.parser.parser import get_entity_result
from notifications.business.notifications_business import NotifiableModulesFactory, NotificationBusiness
from notifications.utils.date import check_pass_date_condition
from datetime import date
from django.db.models import Q
from dateutil.rrule import WEEKLY, MONTHLY, YEARLY
from notifications.business.email_service import (
    send_mail_with_table_by_notification,
    send_simple_mail_by_notification,
)
import json
from SmartEnergy.handler_logging import HandlerLog

logger = HandlerLog()

class NotificationProcessor:
    @staticmethod
    def execute_notifications(**kwargs):
        current_date = date.today()

        notifications_to_send = NotificationProcessor.get_possible_non_event_notifications_by_date(
            current_date, **kwargs
        )

        for notification_to_send in notifications_to_send:
            try:
                notification = notification_to_send["notification"]
                notification_already_sent = NotificationProcessor.check_if_notification_was_sent(
                    notification, current_date
                )
                if not notification_already_sent:
                    data = notification_to_send["result"]
                    NotificationProcessor.register_notification_non_event_history(
                        notification
                    )
                    send_mail_with_table_by_notification(notification, data)
            except Exception as e:
                logger.error(f"[NOTIFICATIONS]::Error executing notification id {notification}: {e}",)

    @staticmethod
    def execute_event_notifications(**kwargs):
        current_date = date.today()

        possible_notifications = NotificationProcessor.get_possible_event_notifications_by_date(
            current_date, **kwargs
        )

        for notification in possible_notifications:
            notification_test = NotificationProcessor.get_notification_test(
                notification
            )
            try:
                if notification_test["has_result"]:
                    results_to_send_mail = NotificationProcessor.filter_event_results_to_send_mail(
                        notification_test["result"], notification
                    )
                    if len(results_to_send_mail) > 0:
                        NotificationProcessor.run_event_notification(
                            results_to_send_mail, notification
                        )
            except Exception as e:
                logger.error(
                    f"[NOTIFICATIONS]::Error executing event notification id {notification}: {e}",
                )

    @staticmethod
    def execute_pme_notifications():
        NotificationProcessor.execute_event_notifications(
            entity=Modules.ALARM_PME.value
        )
        NotificationProcessor.execute_notifications(entity=Modules.ALARM_PME.value)

    @staticmethod
    def register_notification_non_event_history(notification):
        notification_history = NotificationHistory()
        notification_history.notification = notification
        notification_history.save()

    @staticmethod
    def check_if_notification_was_sent(notification_to_send, current_date):
        return NotificationHistory.objects.filter(
            notification=notification_to_send.id, created_at__date=current_date
        ).exists()

    @staticmethod
    def filter_event_results_to_send_mail(notification_results, notification):
        # check entities pks and notification pk on db
        # return those who doesn't match
        result_ids = []
        for result in notification_results:
            result_ids.append(result.pk)

        current_history = NotificationEventHistory.objects.filter(
            notification=notification, notification_entity_pk__in=result_ids
        )

        history_pks = []
        for history in current_history:
            history_pks.append(history.notification_entity_pk)

        result = notification_results.exclude(pk__in=history_pks)

        return result

    @staticmethod
    def run_event_notification(notification_results, notification):
        for result in notification_results:
            send_simple_mail_by_notification(notification, result)

            # saves on history
            NotificationProcessor.save_notification_event_history(
                result.pk, notification
            )

    @staticmethod
    def save_notification_event_history(entity_pk, notification):
        new_history = NotificationEventHistory(
            **{"notification": notification, "notification_entity_pk": entity_pk}
        )
        new_history.save()

    @staticmethod
    def get_possible_non_event_notifications_by_date(date, **kwargs):
        date_and_frequency_condition = Q(
            Q(start_date__lte=date)
            & ~Q(
                notification_frequency__notification_frequency=NotificationFrequency.ON_EVENT
            )
        )

        active_condition = Q(date_and_frequency_condition & Q(status=True))

        possible_notifications = Notification.objects.filter(active_condition, **kwargs)

        notifications_modified = list(map(NotificationBusiness.inject_reports_rules, possible_notifications))

        filtered_possible_notifications = NotificationProcessor.filter_notifications_by_event_and_validating_string(
            list(notifications_modified), date
        )

        return filtered_possible_notifications

    @staticmethod
    def get_possible_event_notifications_by_date(date, **kwargs):
        date_and_frequency_condition = Q(
            Q(start_date__lte=date)
            & Q(
                notification_frequency__notification_frequency=NotificationFrequency.ON_EVENT
            )
        )

        notification_type_condition = Q(
            date_and_frequency_condition
            & Q(notification_type__notification_type=NotificationType.VERIFICATION)
        )

        active_condition = Q(notification_type_condition & Q(status=True))

        possible_notifications = Notification.objects.filter(active_condition, **kwargs)

        return possible_notifications

    """
    Filter if notification should run by its frequency condition
    """

    @staticmethod
    def filter_notifications_by_event_and_validating_string(
        possible_notifications, current_date
    ):
        result = []
        for notification in possible_notifications:
            if NotificationProcessor.check_if_is_notifiable(
                notification.notification_frequency.notification_frequency,
                notification.start_date,
                current_date,
            ):
                try:
                    notification_test = NotificationProcessor.get_notification_test(
                        notification
                    )
                    if notification_test["has_result"]:
                        result.append(notification_test)
                except Exception as e:
                    logger.error(
                        f"[NOTIFICATIONS]::Error executing notification id {notification}: {e}",
                    )
        return result

    @staticmethod
    def get_notification_test(notification):
        try:
            dict_query = json.loads(notification.notification_rule_processed)
            module_name = notification.entity
            module = NotifiableModulesFactory.create_notifiable_module(
                Modules[module_name]
            )

            result = get_entity_result(dict_query, module)
            if len(result) == 0:
                return {"has_result": False}

            return {"has_result": True, "result": result, "notification": notification}
        except Exception as e:
            logger.error(f"[NOTIFICATIONS]::Error executing notification id {notification}: {e}",)

    @staticmethod
    def check_if_is_notifiable(frequency, start_date, current_date):
        return (
            frequency == NotificationFrequency.DAILY
            or (
                frequency == NotificationFrequency.WEEKLY
                and check_pass_date_condition(WEEKLY, start_date, current_date)
            )
            or (
                frequency == NotificationFrequency.FORTNIGHTLY
                and check_pass_date_condition(WEEKLY, start_date, current_date, 2)
            )
            or (
                frequency == NotificationFrequency.MONTHLY
                and check_pass_date_condition(MONTHLY, start_date, current_date)
            )
            or (
                frequency == NotificationFrequency.QUARTERLY
                and check_pass_date_condition(MONTHLY, start_date, current_date, 3)
            )
            or (
                frequency == NotificationFrequency.SEMIANNUALLY
                and check_pass_date_condition(MONTHLY, start_date, current_date, 6)
            )
            or (
                frequency == NotificationFrequency.ANNUALLY
                and check_pass_date_condition(YEARLY, start_date, current_date)
            )
        )
