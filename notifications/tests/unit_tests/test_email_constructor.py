from unittest import mock

from django.test import SimpleTestCase
from notifications import models as notificaton_models
from notifications.business.email_constructor import EmailConstructor
from notifications.business.notification_processor import NotificationProcessor

from notifications.business import email_service
from usage_contract.models import UsageContract

from datetime import date

from notifications.tests.lib import (
    MockQuerySet,
    MockNotificationMail,
    MockMail,
)


class TestEmailConstructor(SimpleTestCase):
    def setUp(self):
        self.usage_contract_list = [
            UsageContract(
                **{
                    "contract_number": "0212005",
                    "bought_voltage": "230.00",
                    "end_date": "2023-12-31",
                }
            ),
            UsageContract(
                **{
                    "contract_number": "0312004",
                    "bought_voltage": "230.00",
                    "end_date": "2023-12-31",
                }
            ),
        ]
        self.usage_contract_dict_list = [
            {
                "contract_number": "0212005",
                "bought_voltage": "230.00",
                "end_date": "2023-12-31",
            },
            {
                "contract_number": "0312004",
                "bought_voltage": "230.00",
                "end_date": "2023-12-31",
            },
        ]
        self.notification_mock = notificaton_models.Notification(
            **{
                "pk": 1,
                "entity": "USAGE_CONTRACT",
                "notification_rule_processed": '{"type": "logical_comparison", "field": {"value": "end_date", "type": "Database Attribute"}, "operation": "__lte", "value": {"type": "aritimetical_operation", "operator_left": {"value": "currentDate", "type": "Variable"}, "operation": "+", "operator_right": {"value": "10", "type": "Number"}}}',
            }
        )
        self.notification_mail_mock = MockNotificationMail(
            **{
                "pk": 1,
                "entity": "USAGE_CONTRACT",
                "notification_rule_processed": '{"type": "logical_comparison", "field": {"value": "end_date", "type": "Database Attribute"}, "operation": "__lte", "value": {"type": "aritimetical_operation", "operator_left": {"value": "currentDate", "type": "Variable"}, "operation": "+", "operator_right": {"value": "10", "type": "Number"}}}',
                "message": "test",
                "subject": "test",
            }
        )

        verification_notification_type = notificaton_models.NotificationType(
            **{"id": 3, "notification_type": "VERIFICATION",}
        )
        weekly_notification_frequency = notificaton_models.NotificationFrequency(
            **{"id": 2, "notification_frequency": "WEEKLY",}
        )
        self.notifications_mock = [
            notificaton_models.Notification(
                **{
                    "pk": 1,
                    "entity": "USAGE_CONTRACT",
                    "notification_rule_processed": '{"type": "logical_comparison", "field": {"value": "end_date", "type": "Database Attribute"}, "operation": "__lte", "value": {"type": "aritimetical_operation", "operator_left": {"value": "currentDate", "type": "Variable"}, "operation": "+", "operator_right": {"value": "10", "type": "Number"}}}',
                    "start_date": date(2020, 1, 1),
                    "notification_type": verification_notification_type,
                    "notification_frequency": weekly_notification_frequency,
                },
            )
        ]

    # Email constructor tests
    def test_get_email_table_data_should_return_a_list(self):
        fields = [
            "bought_voltage",
            "contract_number",
            "end_date",
        ]
        data = self.usage_contract_list

        correct_result = [
            ["230.00", "0212005", "2023-12-31"],
            ["230.00", "0312004", "2023-12-31"],
        ]

        email_table = EmailConstructor.get_email_table_data(fields, data)

        self.assertSequenceEqual(email_table, correct_result)

    def test_create_email_with_table_template_should_return_email_string(self):
        message = "Just an email test"
        fields = [
            "bought_voltage",
            "contract_number",
            "end_date",
        ]
        data = self.usage_contract_list

        email = EmailConstructor.create_email_with_table_template(
            message, "usage_contract", fields, data
        )

        self.assertIsInstance(email, str)
        self.assertIsNot(email, "")
        self.assertIsNotNone(email)

    def test_get_parsed_email_message_should_return_treated_string(self):
        message = "${bought_voltage}, ${contract_number}, ${end_date}"
        data = self.usage_contract_list[0]

        email_message = EmailConstructor.get_parsed_email_message(message, data)

        self.assertIsInstance(email_message, str)
        self.assertEqual(
            email_message, "<b>230.00</b>, <b>0212005</b>, <b>2023-12-31</b>"
        )

    def test_create_simple_email_template_should_return_email_template(self):
        message = "${bought_voltage}, ${contract_number}, ${end_date}"
        data = self.usage_contract_list[0]

        email = EmailConstructor.create_simple_email_template(message, data)

        self.assertIsInstance(email, str)
        self.assertIsNot(email, "")
        self.assertIsNotNone(email)

    # notification processor tests
    @mock.patch("notifications.language.parser.parser.get_result")
    @mock.patch(
        "usage_contract.models.TypeUsageContract.objects.all", mock.MagicMock(),
    )
    @mock.patch(
        "usage_contract.models.UsageContract.objects.filter", return_value=[],
    )
    def test_get_notification_test_should_call_get_result(
        self, get_result, usage_contract_get_mock
    ):
        result = NotificationProcessor.get_notification_test(self.notification_mock)

        self.assertEqual(result, {"has_result": False})
        self.assertTrue(get_result.called)

    @mock.patch(
        "notifications.business.notification_processor.NotificationProcessor.get_notification_test"
    )
    def test_filter_notifications_by_event_and_validating_string_should_run_get_notification_test(
        self, get_notification_test_mock
    ):
        result = NotificationProcessor.filter_notifications_by_event_and_validating_string(
            self.notifications_mock, date(2020, 1, 8)
        )
        self.assertTrue(get_notification_test_mock.called)

    @mock.patch(
        "notifications.business.notification_processor.NotificationProcessor.filter_notifications_by_event_and_validating_string",
        return_value=[],
    )
    @mock.patch(
        "notifications.models.Notification.objects.filter", return_value=[],
    )
    def test_get_possible_non_event_notifications_by_date_should_call_filter_notifications_by_event_and_validating_string(
        self,
        filter_notifications_by_event_and_validating_string_mock,
        notification_query_mock,
    ):
        result = NotificationProcessor.get_possible_non_event_notifications_by_date(
            date(2020, 1, 8)
        )

        self.assertTrue(filter_notifications_by_event_and_validating_string_mock.called)

    @mock.patch(
        "notifications.business.notification_processor.NotificationProcessor.get_possible_non_event_notifications_by_date",
        return_value=[],
    )
    def test_execute_notifications_should_call_necessary_methods(
        self, get_possible_non_event_notifications_by_date_mock
    ):
        result = NotificationProcessor.execute_notifications()
        self.assertTrue(get_possible_non_event_notifications_by_date_mock.called)

    def test_check_if_is_notifiable_should_run(self):
        result_daily = NotificationProcessor.check_if_is_notifiable(
            notificaton_models.NotificationFrequency.DAILY,
            date(2019, 12, 31),
            date(2020, 1, 1),
        )
        self.assertTrue(result_daily)
        result_weekly = NotificationProcessor.check_if_is_notifiable(
            notificaton_models.NotificationFrequency.WEEKLY,
            date(2020, 12, 24),
            date(2020, 12, 31),
        )
        self.assertTrue(result_weekly)
        result_fortnightly = NotificationProcessor.check_if_is_notifiable(
            notificaton_models.NotificationFrequency.FORTNIGHTLY,
            date(2020, 12, 17),
            date(2020, 12, 31),
        )
        self.assertTrue(result_fortnightly)
        result_monthly = NotificationProcessor.check_if_is_notifiable(
            notificaton_models.NotificationFrequency.MONTHLY,
            date(2020, 1, 31),
            date(2020, 12, 31),
        )
        self.assertTrue(result_monthly)
        result_quarterly = NotificationProcessor.check_if_is_notifiable(
            notificaton_models.NotificationFrequency.QUARTERLY,
            date(2020, 9, 30),
            date(2020, 12, 30),
        )
        self.assertTrue(result_quarterly)
        result_semiannually = NotificationProcessor.check_if_is_notifiable(
            notificaton_models.NotificationFrequency.SEMIANNUALLY,
            date(2020, 6, 30),
            date(2020, 12, 30),
        )
        self.assertTrue(result_semiannually)
        result_annually = NotificationProcessor.check_if_is_notifiable(
            notificaton_models.NotificationFrequency.ANNUALLY,
            date(2000, 12, 31),
            date(2020, 12, 31),
        )
        self.assertTrue(result_annually)
        result_annually_bissest = NotificationProcessor.check_if_is_notifiable(
            notificaton_models.NotificationFrequency.ANNUALLY,
            date(2008, 2, 29),
            date(2016, 2, 29),
        )
        self.assertTrue(result_annually_bissest)

    @mock.patch(
        "notifications.models.Notification.objects.filter", return_value=[],
    )
    def test_get_possible_event_notifications_by_date_should_filter_notifications(
        self, filter_notification_mock
    ):
        result = NotificationProcessor.get_possible_event_notifications_by_date(
            date(2020, 1, 1)
        )

        self.assertTrue(filter_notification_mock.called)

    @mock.patch(
        "notifications.models.NotificationEventHistory.objects.filter", return_value=[],
    )
    def test_filter_event_results_to_send_mail_should_filter(
        self, notification_event_history_mock
    ):
        mocked_usage_contracts = MockQuerySet(self.usage_contract_list)

        result = NotificationProcessor.filter_event_results_to_send_mail(
            mocked_usage_contracts, self.notification_mock
        )

        self.assertTrue(notification_event_history_mock.called)

    @mock.patch(
        "notifications.business.notification_processor.NotificationProcessor.save_notification_event_history"
    )
    @mock.patch("django.core.mail.EmailMultiAlternatives.send")
    @mock.patch("notifications.models.NotificationEventHistory.save")
    def test_run_event_notification_should_send_emails(
        self, save_event, send_mail, save_notification_event_history_mock
    ):
        mocked_usage_contracts = MockQuerySet(self.usage_contract_list)

        result = NotificationProcessor.run_event_notification(
            mocked_usage_contracts, self.notification_mail_mock
        )

        self.assertTrue(save_notification_event_history_mock.called)
        self.assertTrue(send_mail.called)

    @mock.patch(
        "notifications.business.notification_processor.NotificationProcessor.get_possible_event_notifications_by_date",
        return_value=[notificaton_models.Notification(**{"id": 1})],
    )
    @mock.patch(
        "notifications.business.notification_processor.NotificationProcessor.get_notification_test",
        return_value={"has_result": True, "result": []},
    )
    @mock.patch(
        "notifications.business.notification_processor.NotificationProcessor.filter_event_results_to_send_mail",
        return_value=[UsageContract(1)],
    )
    @mock.patch(
        "notifications.business.notification_processor.NotificationProcessor.run_event_notification",
        return_value=[],
    )
    def test_execute_event_notification_should_call_methods(
        self,
        get_possible_event_notifications_by_date,
        get_notification_test,
        filter_event_results_to_send_mail,
        run_event_notification,
    ):
        result = NotificationProcessor.execute_event_notifications()

        self.assertTrue(get_possible_event_notifications_by_date.called)
        self.assertTrue(get_notification_test.called)
        self.assertTrue(filter_event_results_to_send_mail.called)
        self.assertTrue(run_event_notification.called)

    @mock.patch("django.core.mail.EmailMultiAlternatives.send")
    def test_send_mail_should_call_send(self, msg_send):
        mock_mail = MockMail()
        email_service.send_mail("Dorime", "Ameno", mock_mail.all())
        self.assertTrue(msg_send.called)

    @mock.patch("django.core.mail.EmailMultiAlternatives.send")
    def test_send_simple_mail_by_notification_should_call_send_mail(self, msg_send):
        email_service.send_simple_mail_by_notification(
            self.notification_mail_mock, self.usage_contract_list
        )
        self.assertTrue(msg_send.called)

    @mock.patch("django.core.mail.EmailMultiAlternatives.send")
    def test_send_mail_with_table_by_notification_should_call_send_mail(self, msg_send):
        email_service.send_mail_with_table_by_notification(
            self.notification_mail_mock, self.usage_contract_list
        )
        self.assertTrue(msg_send.called)
