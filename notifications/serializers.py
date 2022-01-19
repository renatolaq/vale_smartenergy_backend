from rest_framework import serializers

from core.models import Log
from .models import (
    Notification,
    NotificationType,
    NotificationFrequency,
    NotificationTargetEmail,
    NotificationEmailField,
)

from notifications.business.notifications_business import NotificationBusiness
from .utils.log import LogUtils
from .utils.date import check_if_is_29_february

import json


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = (
            "id",
            "name",
            "description",
            "start_date",
            "notification_rule",
            "notification_rule_processed",
            "notification_type",
            "notification_frequency",
            "subject",
            "message",
            "entity",
            "notification_username",
            "status",
        )


class NotificationListSerializer(serializers.ModelSerializer):
    notification_type = serializers.CharField(
        source="notification_type.notification_type"
    )
    notification_frequency = serializers.CharField(
        source="notification_frequency.notification_frequency"
    )

    class Meta:
        model = Notification
        fields = (
            "id",
            "name",
            "description",
            "notification_type",
            "notification_frequency",
            "notification_username",
            "start_date",
            "status",
        )


class NotificationTargetEmailSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationTargetEmail
        fields = ("target_email",)


class NotificationEmailFieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationEmailField
        fields = ("email_field",)


class NotificationDetailsSerializer(serializers.ModelSerializer):
    notification_type = serializers.CharField(
        source="notification_type.notification_type"
    )
    notification_frequency = serializers.CharField(
        source="notification_frequency.notification_frequency"
    )
    emails = NotificationTargetEmailSerializer(many=True)

    class Meta:
        model = Notification
        fields = (
            "id",
            "name",
            "description",
            "start_date",
            "notification_rule",
            "notification_rule_processed",
            "entity",
            "notification_type",
            "notification_frequency",
            "subject",
            "message",
            "notification_username",
            "emails",
            "status",
        )


class NotificationWriteSerializer(serializers.ModelSerializer):
    emails = NotificationTargetEmailSerializer(many=True)
    email_fields = NotificationEmailFieldSerializer(many=True, required=False)
    notification_rule = serializers.CharField(required=False, default='')

    def __init__(self, instance=None, *args, **kwargs):
        super(NotificationWriteSerializer, self).__init__(instance, *args, **kwargs)
        self._log = LogUtils(
            serializer=NotificationLogSerializer,
            username=self._context["request"].auth.get("UserFullName", "Anonymous"),
        )

    class Meta:
        model = Notification
        fields = (
            "id",
            "name",
            "description",
            "start_date",
            "notification_rule",
            "notification_rule_processed",
            "entity",
            "notification_type",
            "notification_frequency",
            "subject",
            "message",
            "notification_username",
            "emails",
            "email_fields",
        )

    def validate(self, data):
        notification_type = data["notification_type"]
        notification_frequency = data["notification_frequency"]

        if (
            notification_type
            in [NotificationType.CREATION, NotificationType.MODIFICATION]
            and notification_frequency != NotificationFrequency.ON_EVENT
        ):
            raise serializers.ValidationError(
                {
                    f"notification_frequency": "must be ({NotificationFrequency.ON_EVENT})"
                }
            )

        if (
            notification_frequency != NotificationFrequency.ON_EVENT
            and data.get("notification_rule", None) == None
        ):
            raise serializers.ValidationError({"notification_rule": "required"})

        if check_if_is_29_february(data["start_date"]):
            raise serializers.ValidationError({"start_date": "invalid"})

        return data

    def to_internal_value(self, data):
        request = self.context["request"]
        updated_data = NotificationBusiness.process_create_request(data)
        updated_data["notification_username"] = request.auth["UserFullName"]

        return super(NotificationWriteSerializer, self).to_internal_value(updated_data)

    def create(self, validated_data):
        return NotificationBusiness.create_notification(
            data=validated_data, log_strategy=self._log
        )

    def update(self, notification, validated_data):
        if notification.status == False:
            raise serializers.ValidationError(
                {"status": "You can't update an inactive notification."}
            )

        return NotificationBusiness.update_notification(
            notification=notification, data=validated_data, log_strategy=self._log
        )


class NotificationLogSerializer(serializers.ModelSerializer):
    notification_type = serializers.CharField(
        source="notification_type.notification_type"
    )
    notification_frequency = serializers.CharField(
        source="notification_frequency.notification_frequency"
    )
    emails = NotificationTargetEmailSerializer(many=True)

    class Meta:
        model = Notification
        fields = (
            "id",
            "name",
            "description",
            "start_date",
            "notification_rule",
            "notification_rule_processed",
            "entity",
            "notification_type",
            "notification_frequency",
            "subject",
            "message",
            "notification_username",
            "emails",
            "status",
        )


class LogSerializer(serializers.ModelSerializer):
    old_value = serializers.SerializerMethodField()
    new_value = serializers.SerializerMethodField()

    class Meta:
        fields = (
            "id_log",
            "field_pk",
            "table_name",
            "action_type",
            "old_value",
            "new_value",
            "observation",
            "date",
            "user",
        )
        model = Log

    def get_old_value(self, obj):
        return json.loads(obj.old_value.replace("'", '"'))

    def get_new_value(self, obj):
        return json.loads(obj.new_value.replace("'", '"'))


class NotificationPDFSerializer(serializers.ModelSerializer):
    notification_type = serializers.SerializerMethodField()
    notification_frequency = serializers.SerializerMethodField()
    start_date = serializers.DateField(format="%d/%m/%Y")
    status = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = NotificationBusiness.fields_to_export

    def get_notification_type(self, obj):
        return obj.notification_type.notification_type

    def get_notification_frequency(self, obj):
        return obj.notification_frequency.notification_frequency

    def get_status(self, obj):
        return "enabled" if obj.status else "disabled"
