from unittest import mock

from django.test import SimpleTestCase

from notifications.business.signal_business import NotificationSignalBusiness


class TestSignalBusiness(SimpleTestCase):
    @mock.patch(
        "notifications.business.signal_business.NotificationSignalBusiness.get_active_notifications_by_type",
        mock.Mock(return_value=["any", "any"]),
    )
    @mock.patch(
        "notifications.business.signal_business.NotificationSignalBusiness.process_notification"
    )
    def test_create_signal_method_should_call_proccess_notification(
        self, process_notification_mock
    ):
        NotificationSignalBusiness.create_signal(
            "any", "any", notifiable_module=mock.Mock()
        )
        self.assertEqual(process_notification_mock.call_count, 1)

    @mock.patch(
        "notifications.business.signal_business.NotificationSignalBusiness.get_active_notifications_by_type",
        mock.Mock(return_value=["any", "any"]),
    )
    @mock.patch(
        "notifications.business.signal_business.NotificationSignalBusiness.process_notification"
    )
    def test_update_signal_method_should_call_proccess_notification(
        self, process_notification_mock
    ):
        NotificationSignalBusiness.update_signal(
            "any", "any", notifiable_module=mock.Mock()
        )
        self.assertEqual(process_notification_mock.call_count, 1)

    @mock.patch(
        "notifications.business.signal_business.NotificationSignalBusiness.create_signal"
    )
    def test_dispatch_signal_should_call_create_signal_if_create_attr_exist(
        self, create_signal_mock
    ):
        NotificationSignalBusiness.dispatch_signal("any", "any", created="any")
        self.assertEqual(create_signal_mock.call_count, 1)

    @mock.patch(
        "notifications.business.signal_business.NotificationSignalBusiness.update_signal"
    )
    def test_dispatch_signal_should_call_update_signal_if_create_doesnt_exist(
        self, update_signal_mock
    ):
        NotificationSignalBusiness.dispatch_signal("any", "any")
        self.assertEqual(update_signal_mock.call_count, 1)

    @mock.patch("notifications.business.email_service.send_simple_mail_by_notification")
    @mock.patch("notifications.models.Notification")
    def test_proccess_notification_should_call_send_email_if_notification_doesnt_have_rules(
        self, mock_notification, send_simple_mail_mock
    ):
        mock_notification.notification_rule_processed = None
        instance = mock.Mock()

        NotificationSignalBusiness.process_notification(instance, [mock_notification])
        self.assertTrue(send_simple_mail_mock.called)

    @mock.patch("notifications.business.email_service.send_simple_mail_by_notification")
    @mock.patch(
        "notifications.language.parser.parser.get_entity_result", return_value=[]
    )
    @mock.patch("notifications.models.Notification")
    def test_proccess_notification_shouldnt_call_send_email_if_notification_has_rule_and_instance_is_not_compatible(
        self, mock_notification, get_entity_result_mock, send_simple_mail_mock
    ):
        instance = mock.Mock()
        mock_notification.notification_rule_processed = '{"blablabla": "blablabl"}'
        NotificationSignalBusiness.process_notification(
            instance, [mock_notification], notifiable_module=mock.Mock()
        )
        self.assertTrue(get_entity_result_mock.called)
        self.assertFalse(send_simple_mail_mock.called)

    @mock.patch("notifications.business.email_service.send_simple_mail_by_notification")
    @mock.patch(
        "notifications.language.parser.parser.get_entity_result", return_value=["yaayy"]
    )
    @mock.patch("notifications.models.Notification")
    def test_proccess_notification_should_call_send_email_if_notification_has_and_instance_is_compatible(
        self, mock_notification, get_entity_result_mock, send_simple_mail_mock
    ):
        instance = mock.Mock()
        mock_notification.notification_rule_processed = '{"blablabla": "blablabl"}'
        NotificationSignalBusiness.process_notification(
            instance, [mock_notification], notifiable_module=mock.Mock()
        )
        self.assertTrue(get_entity_result_mock.called)
        self.assertTrue(send_simple_mail_mock.called)
