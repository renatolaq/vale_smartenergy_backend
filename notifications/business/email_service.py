from django.core.mail import EmailMultiAlternatives

from notifications.business.email_constructor import EmailConstructor
from notifications.utils.db import get_field_list_by_data
from django.conf import settings


def send_mail_with_table_by_notification(notification, data):
    message = notification.message
    fields = get_field_list_by_data(notification.email_fields.all(), "email_field")
    email_template = EmailConstructor.create_email_with_table_template(
        message, notification.entity, fields, data
    )

    subject = notification.subject
    emails = notification.emails.all()

    send_mail(subject, email_template, emails)


def send_simple_mail_by_notification(notification, data):
    message = notification.message
    email_template = EmailConstructor.create_simple_email_template(message, data)

    subject = notification.subject
    emails = notification.emails.all()

    send_mail(subject, email_template, emails)


def send_mail(subject, message, emails):
    target_emails = []
    for email in emails:
        target_emails.append(email.target_email)

    msg = EmailMultiAlternatives(subject, subject, settings.EMAIL_SENDER, target_emails)
    msg.attach_alternative(message, "text/html")
    msg.send()
    print("Mail sent to: ", target_emails)
