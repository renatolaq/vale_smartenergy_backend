from modulefinder import Module
from os import path
from unittest import mock
# mock transaction.atomic decorators before import modules
mock.patch("django.db.transaction.atomic", lambda func: func).start()


from SmartEnergy.settings import BASE_DIR
from notifications.business.notifiable_modules import Modules
from notifications.business.notification_processor import NotificationProcessor
from notifications.models import Notification, NotificationType, NotificationFrequency

from django.test import SimpleTestCase
from notifications import models as notificaton_models
from notifications.business.notifications_business import NotificationBusiness


class TestNotifiableModule(SimpleTestCase):
    @mock.patch(
        "notifications.business.notifications_business.NotificationBusiness.prepopulate_notification_history",
        mock.Mock(),
    )
    @mock.patch.object(notificaton_models.Notification, "save", mock.Mock())
    @mock.patch("notifications.utils.log.LogUtils")
    @mock.patch(
        "notifications.business.notifications_business.NotificationBusiness.create_notification_emails"
    )
    @mock.patch(
        "notifications.business.notifications_business.NotificationBusiness.create_notification_email_fields"
    )
    def test_create_method_should_call_create_notification_emails_and_create_notification_email_field(
        self,
        create_notification_emails_mock,
        create_notification_email_fields_mock,
        log_utils_mock,
    ):
        NotificationBusiness.create_notification(
            {
                "notification_frequency": notificaton_models.NotificationFrequency("1"),
                "emails": [{"target_email": "testing@test.com"}],
                "email_fields": [{"email_field": "dorime"}],
            },
            log_utils_mock,
        )
        self.assertTrue(create_notification_emails_mock.called)
        self.assertTrue(create_notification_email_fields_mock.called)

    @mock.patch.object(notificaton_models.NotificationTargetEmail, "save")
    def test_create_notification_emails_should_receive_dict_and_create_emails(
        self, notification_target_email_mock
    ):
        NotificationBusiness.create_notification_emails(
            notificaton_models.Notification(),
            [
                {"target_email": "testing1@test.com"},
                {"target_email": "testing2@test.com"},
            ],
        )
        self.assertEqual(notification_target_email_mock.call_count, 2)

    @mock.patch.object(notificaton_models.NotificationEmailField, "save")
    def test_create_notification_email_fields_should_receive_dict_and_create_email_fields(
        self, notification_email_field_mock
    ):
        NotificationBusiness.create_notification_email_fields(
            notificaton_models.Notification(),
            [{"email_field": "dorime"}, {"email_field": "ameno"},],
        )
        self.assertEqual(notification_email_field_mock.call_count, 2)

    @mock.patch.object(notificaton_models.Notification, "save")
    @mock.patch(
        "notifications.business.notifications_business.NotificationBusiness.create_notification_emails"
    )
    @mock.patch(
        "notifications.business.notifications_business.NotificationBusiness.create_notification_email_fields"
    )
    @mock.patch(
        "notifications.business.notifications_business.NotificationBusiness.delete_notification_emails"
    )
    @mock.patch(
        "notifications.business.notifications_business.NotificationBusiness.delete_notification_email_fields"
    )
    @mock.patch("notifications.utils.log.LogUtils")
    def test_update_notifications_should_delete_and_create_again_notifications_emails_and_email_fields(
        self,
        log_mock,
        delete_notification_emails_mock,
        delete_notification_email_fields_mock,
        create_notifications_email_mock,
        create_notifications_email_fields_mock,
        save_notification_mock,
    ):
        NotificationBusiness.update_notification(
            notificaton_models.Notification,
            {
                "notification_frequency": notificaton_models.NotificationFrequency("1"),
                "emails": [
                    {"target_email": "testing@test.com"},
                    {"target_email": "testing2@test.com"},
                ],
                "email_fields": [{"email_field": "dorime"}],
            },
            log_mock,
        )
        self.assertTrue(delete_notification_emails_mock.called)
        self.assertTrue(create_notifications_email_mock.called)
        self.assertTrue(delete_notification_email_fields_mock.called)
        self.assertTrue(create_notifications_email_fields_mock.called)
        self.assertTrue(save_notification_mock.called)

    @mock.patch.object(notificaton_models.Notification, "save", mock.Mock())
    @mock.patch("notifications.utils.log.LogUtils")
    @mock.patch(
        "notifications.business.notifications_business.NotificationBusiness.create_notification_emails",
        mock.Mock(),
    )
    @mock.patch(
        "notifications.business.notifications_business.NotificationBusiness.create_notification_email_fields",
        mock.Mock(),
    )
    @mock.patch(
        "notifications.business.notifications_business.NotificationBusiness.prepopulate_notification_history",
        mock.Mock(),
    )
    def test_create_notifications_should_call_log(self, log_mock):
        NotificationBusiness.create_notification(
            {
                "notification_frequency": notificaton_models.NotificationFrequency("1"),
                "emails": [
                    {"target_email": "testing@test.com"},
                    {"target_email": "testing2@test.com"},
                ],
                "email_fields": [{"email_field": "dorime"}],
            },
            log_mock,
        )
        self.assertTrue(log_mock.save_log.called)

    @mock.patch.object(notificaton_models.Notification, "save", mock.Mock())
    @mock.patch("notifications.utils.log.LogUtils")
    @mock.patch(
        "notifications.business.notifications_business.NotificationBusiness.create_notification_emails",
        mock.Mock(),
    )
    @mock.patch(
        "notifications.business.notifications_business.NotificationBusiness.delete_notification_emails",
        mock.Mock(),
    )
    @mock.patch(
        "notifications.business.notifications_business.NotificationBusiness.create_notification_email_fields",
        mock.Mock(),
    )
    @mock.patch(
        "notifications.business.notifications_business.NotificationBusiness.delete_notification_email_fields",
        mock.Mock(),
    )
    def test_update_notifications_should_call_log(self, log_mock):
        NotificationBusiness.update_notification(
            notificaton_models.Notification,
            {
                "notification_frequency": notificaton_models.NotificationFrequency("1"),
                "emails": [
                    {"target_email": "testing@test.com"},
                    {"target_email": "testing2@test.com"},
                ],
                "email_fields": [{"email_field": "dorime"}],
            },
            log_mock,
        )
        self.assertTrue(log_mock.update_log.called)

    @mock.patch.object(notificaton_models.Notification, "save")
    @mock.patch(
        "notifications.models.Notification.objects.get",
        return_value=notificaton_models.Notification(id=1),
    )
    def test_notification_change_status_should_change_notification_status(
        self, notification_get_mock, notification_save_mock
    ):
        notification = notification_get_mock()
        return_value = NotificationBusiness.change_status(id="any", status=False)

        self.assertEqual(notification_save_mock.call_count, 1)
        self.assertEqual(notification.status, False)
        self.assertSequenceEqual(return_value, {"id": 1, "status": False})

    @mock.patch(
        "notifications.business.notifications_business.NotificationBusiness.create_notification_email_fields",
        mock.Mock(),
    )
    @mock.patch.object(notificaton_models.Notification, "save", mock.Mock())
    @mock.patch(
        "notifications.business.notifications_business.NotificationBusiness.create_notification_emails",
        mock.Mock(),
    )
    @mock.patch("notifications.utils.log.LogUtils")
    @mock.patch(
        "notifications.business.notifications_business.NotificationBusiness.prepopulate_notification_history"
    )
    def test_create_method_should_call_create_notification_should_call_prepopulate_notification_history(
        self, prepopulate_notification_history_mock, log_utils_mock
    ):
        NotificationBusiness.create_notification(
            {
                "notification_frequency": notificaton_models.NotificationFrequency("1"),
                "emails": [{"target_email": "testing@test.com"}],
                "email_fields": [{"email_field": "dorime"}],
            },
            log_utils_mock,
        )
        self.assertTrue(prepopulate_notification_history_mock.called)

    @mock.patch(
        "notifications.business.notifications_business.NotifiableModulesFactory.create_notifiable_module"
    )
    def test_prepopulate_history_should_call_notifiable_module_method_if_is_on_event(
        self, create_notifiable_module_mock
    ):
        notification = Notification(1)
        notification_type = NotificationType(
            notification_type=NotificationType.VERIFICATION
        )
        notification_frequency = NotificationFrequency(
            notification_frequency=NotificationFrequency.ON_EVENT
        )
        notification.notification_type = notification_type
        notification.notification_frequency = notification_frequency
        # could be any notifiable module
        notification.entity = "USAGE_CONTRACT"

        notifiable_module = mock.Mock()
        notifiable_module.prepopulate_notification_history = mock.Mock()

        create_notifiable_module_mock.return_value = notifiable_module
        NotificationBusiness.prepopulate_notification_history(notification)

        self.assertTrue(notifiable_module.prepopulate_notification_history.called)

    @mock.patch(
        "notifications.business.notifications_business.NotifiableModulesFactory.create_notifiable_module"
    )
    def test_prepopulate_history_shouldnt_call_notifiable_module_method_if_is_not_on_event(
        self, create_notifiable_module_mock
    ):
        notification = Notification(1)
        notification_type = NotificationType(
            notification_type=NotificationType.VERIFICATION
        )
        notification_frequency = NotificationFrequency(
            notification_frequency=NotificationFrequency.DAILY
        )
        notification.notification_type = notification_type
        notification.notification_frequency = notification_frequency
        # could be any notifiable module
        notification.entity = "USAGE_CONTRACT"

        notifiable_module = mock.Mock()
        notifiable_module.prepopulate_notification_history = mock.Mock()

        create_notifiable_module_mock.return_value = notifiable_module
        NotificationBusiness.prepopulate_notification_history(notification)

        self.assertFalse(notifiable_module.prepopulate_notification_history.called)

    @mock.patch(
        "notifications.business.notifications_business.NotifiableModulesFactory.create_notifiable_module"
    )
    def test_prepopulate_history_shouldnt_call_notifiable_module_method_if_is_modification_type(
        self, create_notifiable_module_mock
    ):
        notification = Notification(1)
        notification_type = NotificationType(
            notification_type=NotificationType.MODIFICATION
        )
        notification_frequency = NotificationFrequency(
            notification_frequency=NotificationFrequency.ON_EVENT
        )
        notification.notification_type = notification_type
        notification.notification_frequency = notification_frequency
        # could be any notifiable module
        notification.entity = "USAGE_CONTRACT"

        notifiable_module = mock.Mock()
        notifiable_module.prepopulate_notification_history = mock.Mock()

        create_notifiable_module_mock.return_value = notifiable_module
        NotificationBusiness.prepopulate_notification_history(notification)

        self.assertFalse(notifiable_module.prepopulate_notification_history.called)

    @mock.patch(
        "notifications.business.notifications_business.NotifiableModulesFactory.create_notifiable_module"
    )
    def test_prepopulate_history_shouldnt_call_notifiable_module_method_if_is_creation_type(
        self, create_notifiable_module_mock
    ):
        notification = Notification(1)
        notification_type = NotificationType(
            notification_type=NotificationType.CREATION
        )
        notification_frequency = NotificationFrequency(
            notification_frequency=NotificationFrequency.ON_EVENT
        )
        notification.notification_type = notification_type
        notification.notification_frequency = notification_frequency
        # could be any notifiable module
        notification.entity = "USAGE_CONTRACT"

        notifiable_module = mock.Mock()
        notifiable_module.prepopulate_notification_history = mock.Mock()

        create_notifiable_module_mock.return_value = notifiable_module
        NotificationBusiness.prepopulate_notification_history(notification)

        self.assertFalse(notifiable_module.prepopulate_notification_history.called)

    def test_if_vale_log_exists_in_main_app(self):
        self.assertTrue(path.exists(f"{BASE_DIR}/SmartEnergy/static/vale-logo.png"))

    @mock.patch(
        "notifications.business.notification_processor.NotificationProcessor.execute_notifications"
    )
    @mock.patch(
        "notifications.business.notification_processor.NotificationProcessor.execute_event_notifications"
    )
    def test_execute_pme_notifications_should_send_alarm_pme_entity_value(
        self, execute_event_notifications_mock, execute_notifications_mock
    ):
        NotificationProcessor.execute_pme_notifications()
        execute_event_notifications_mock.assert_called_with(
            entity=Modules.ALARM_PME.value
        )
        execute_notifications_mock.assert_called_with(entity=Modules.ALARM_PME.value)

    @mock.patch(
        "notifications.business.notification_processor.NotificationProcessor.get_possible_non_event_notifications_by_date",
        mock.Mock(return_value=[{"result": {}, "notification": mock.Mock()}]),
    )
    @mock.patch(
        "notifications.business.notification_processor.NotificationProcessor.check_if_notification_was_sent",
        mock.Mock(return_value=True),
    )
    @mock.patch(
        "notifications.business.notification_processor.send_mail_with_table_by_notification"
    )
    def test_non_event_notifications_should_not_send_email_if_was_already_sent(
        self, send_email_mock
    ):
        NotificationProcessor.execute_notifications()
        self.assertFalse(send_email_mock.called)

    @mock.patch(
        "notifications.business.notification_processor.NotificationProcessor.get_possible_non_event_notifications_by_date",
        mock.Mock(return_value=[{"result": {}, "notification": mock.Mock()}]),
    )
    @mock.patch(
        "notifications.business.notification_processor.NotificationProcessor.check_if_notification_was_sent",
        mock.Mock(return_value=False),
    )
    @mock.patch(
        "notifications.business.notification_processor.NotificationProcessor.register_notification_non_event_history"
    )
    @mock.patch(
        "notifications.business.notification_processor.send_mail_with_table_by_notification"
    )
    def test_non_event_notifications_should_send_email_and_register_history_if_wasnt_already_sent(
        self, send_email_mock, register_history_mock
    ):
        NotificationProcessor.execute_notifications()
        self.assertTrue(send_email_mock.called)
        self.assertTrue(register_history_mock.called)
