from django.db import models
from django.utils.translation import gettext as _


class NotificationType(models.Model):
    CREATION = "CREATION"
    MODIFICATION = "MODIFICATION"
    VERIFICATION = "VERIFICATION"
    TYPE_CHOICES = (
        (CREATION, "Creation"),
        (MODIFICATION, "Modification"),
        (VERIFICATION, "Verification"),
    )
    id = models.AutoField(db_column="ID_NOTIFICATION_TYPE", primary_key=True)
    notification_type = models.CharField(
        db_column="NOTIFICATION_TYPE",
        choices=TYPE_CHOICES,
        max_length=50,
        blank=False,
        null=False,
    )

    class Meta:
        db_table = "NOTIFICATION_TYPE"
        managed = False


class NotificationFrequency(models.Model):
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    FORTNIGHTLY = "FORTNIGHTLY"
    MONTHLY = "MONTHLY"
    QUARTERLY = "QUARTERLY"
    SEMIANNUALLY = "SEMIANNUALLY"
    ANNUALLY = "ANNUALLY"
    ON_EVENT = "ON_EVENT"
    FREQUENCY_CHOICES = (
        (DAILY, "Daily"),
        (WEEKLY, "Weekly"),
        (FORTNIGHTLY, "Fortnightly"),
        (MONTHLY, "Monthly"),
        (QUARTERLY, "Quartely"),
        (SEMIANNUALLY, "Semiannually"),
        (ANNUALLY, "Annually"),
        (ON_EVENT, "On Event"),
    )
    id = models.AutoField(db_column="ID_NOTIFICATION_FREQUENCY", primary_key=True)
    notification_frequency = models.CharField(
        db_column="NOTIFICATION_FREQUENCY",
        choices=FREQUENCY_CHOICES,
        max_length=50,
        blank=False,
        null=False,
    )

    class Meta:
        db_table = "NOTIFICATION_FREQUENCY"
        managed = False


class Notification(models.Model):
    id = models.AutoField(db_column="ID_NOTIFICATION", primary_key=True)
    name = models.CharField(
        db_column="NAME",
        max_length=500,
        blank=False,
        null=False,
        verbose_name=_("name"),
    )
    description = models.CharField(
        db_column="DESCRIPTION",
        max_length=1000,
        blank=True,
        null=False,
        verbose_name=_("description"),
    )
    start_date = models.DateField(
        db_column="START_DATE", blank=False, null=False, verbose_name=_("start_date")
    )
    notification_rule = models.CharField(
        db_column="NOTIFICATION_RULE",
        max_length=1000,
        blank=True,
        null=False,
        verbose_name=_("notification_rule"),
    )
    notification_rule_processed = models.CharField(
        db_column="NOTIFICATION_RULE_PROCESSED",
        max_length=1000,
        blank=True,
        null=True,
        verbose_name=_("notification_rule_processed"),
    )
    notification_type = models.ForeignKey(
        NotificationType,
        models.DO_NOTHING,
        db_column="ID_NOTIFICATION_TYPE",
        verbose_name=_("notification_type"),
    )
    notification_frequency = models.ForeignKey(
        NotificationFrequency,
        models.DO_NOTHING,
        db_column="ID_NOTIFICATION_FREQUENCY",
        verbose_name=_("notification_frequency"),
    )
    subject = models.CharField(
        db_column="SUBJECT",
        max_length=255,
        blank=True,
        null=False,
        verbose_name=_("subject"),
    )
    message = models.CharField(
        db_column="MESSAGE",
        max_length=1000,
        blank=True,
        null=False,
        verbose_name=_("message"),
    )
    entity = models.CharField(
        db_column="ENTITY",
        max_length=200,
        blank=True,
        null=False,
        verbose_name=_("entity"),
    )
    notification_username = models.CharField(
        db_column="NOTIFICATION_USERNAME",
        max_length=100,
        blank=False,
        null=False,
        verbose_name=_("notification_username"),
    )
    status = models.BooleanField(
        db_column="STATUS",
        null=False,
        blank=False,
        default=True,
        verbose_name=_("status"),
    )

    class Meta:
        db_table = "NOTIFICATION"
        managed = False

    def __str__(self):
        return str(self.id)


class NotificationTargetEmail(models.Model):
    id = models.AutoField(db_column="ID_NOTIFICATION_TARGET_EMAIL", primary_key=True)
    notification = models.ForeignKey(
        Notification,
        on_delete=models.CASCADE,
        db_column="ID_NOTIFICATION",
        related_name="emails",
    )
    target_email = models.EmailField(
        db_column="TARGET_EMAIL", max_length=200, blank=False, null=False
    )

    class Meta:
        db_table = "NOTIFICATION_TARGET_EMAIL"
        managed = False

    def __str__(self):
        return str(self.id)


class NotificationEmailField(models.Model):
    id = models.AutoField(db_column="ID_NOTIFICATION_EMAIL_FIELDS", primary_key=True)
    notification = models.ForeignKey(
        Notification,
        on_delete=models.CASCADE,
        db_column="ID_NOTIFICATION",
        related_name="email_fields",
    )
    email_field = models.CharField(
        db_column="EMAIL_FIELD", max_length=200, blank=False, null=False
    )

    class Meta:
        db_table = "NOTIFICATION_EMAIL_FIELD"
        managed = False

    def __str__(self):
        return str(self.id)


class NotificationEventHistory(models.Model):
    id = models.AutoField(db_column="ID_NOTIFICATION_EVENT_HISTORY", primary_key=True)
    notification = models.ForeignKey(
        Notification, on_delete=models.CASCADE, db_column="ID_NOTIFICATION"
    )
    notification_entity_pk = models.DecimalField(
        db_column="NOTIFICATION_ENTITY_PK",
        max_digits=9,
        decimal_places=0,
        blank=False,
        null=False,
    )

    class Meta:
        db_table = "NOTIFICATION_EVENT_HISTORY"
        managed = False

    def __str__(self):
        return str(self.id)


class NotificationHistory(models.Model):
    id = models.AutoField(db_column="ID_NOTIFICATION_HISTORY", primary_key=True)
    notification = models.ForeignKey(
        Notification, on_delete=models.CASCADE, db_column="ID_NOTIFICATION"
    )
    created_at = models.DateTimeField(auto_now=True, db_column="CREATED_AT")

    class Meta:
        db_table = "NOTIFICATION_HISTORY"
        managed = False

    def __str__(self):
        return str(self.id)


class AlarmTypePME(models.Model):
    DEVICE_COMUNICATION = 1
    UPPER_LIMIT = 2
    INFERIOR_LIMIT = 3
    ENERGY_QUALITY = 4
    TYPE_CHOICES = (
        (DEVICE_COMUNICATION, "Comunicação de dispositivos"),
        (UPPER_LIMIT, "Limite superior"),
        (INFERIOR_LIMIT, "Limite inferior"),
        (ENERGY_QUALITY, "Qualidade de energia"),
    )
    id = models.AutoField(db_column="ID_ALARMS_TYPE", primary_key=True)
    name_alarms_type = models.CharField(
        db_column="NAME_ALARMS_TYPE",
        choices=TYPE_CHOICES,
        max_length=50,
        blank=False,
        null=False,
    )

    class Meta:
        db_table = "ALARMS_TYPE"
        managed = False

    def __str__(self):
        return self.name_alarms_type


class EventTypePME(models.Model):
    SAG = 1
    SWELL = 2
    TRANSIENT = 3
    INTERRUPTION = 4
    COMMUNICATION = 5
    DEMAND = 6
    ENERGY = 7
    VOLTAGE = 8

    TYPE_CHOICES = (
        (SAG, "Sag"),
        (SWELL, "Swell"),
        (TRANSIENT, "Transient"),
        (INTERRUPTION, "Interruption"),
        (COMMUNICATION, "Communication"),
        (DEMAND, "Demand"),
        (ENERGY, "Energy"),
        (VOLTAGE, "Voltage"),
    )
    id = models.AutoField(db_column="ID_EVENT_TYPE", primary_key=True)
    name_event_type = models.CharField(
        db_column="NAME_EVENT_TYPE",
        choices=TYPE_CHOICES,
        max_length=50,
        blank=False,
        null=False,
    )

    class Meta:
        db_table = "EVENT_TYPE"
        managed = False

    def __str__(self):
        return self.name_event_type


class AlarmPME(models.Model):
    id = models.AutoField(db_column="ID_ALARMS_PME", primary_key=True)
    gauge_point = models.ForeignKey(
        "gauge_point.GaugePoint",
        db_column="ID_GAUGE_POINT",
        on_delete=models.DO_NOTHING,
    )
    utc_alarm_date = models.DateTimeField(db_column="UTC_ALARM_DATE")
    utc_creation = models.DateTimeField(db_column="UTC_CREATION")
    status = models.BooleanField(db_column="STATUS")
    alarm_type = models.ForeignKey(
        "notifications.AlarmTypePME",
        db_column="ID_ALARMS_TYPE",
        on_delete=models.DO_NOTHING,
    )
    event_type = models.ForeignKey(
        "notifications.EventTypePME",
        db_column="ID_EVENT_TYPE",
        on_delete=models.DO_NOTHING,
    )

    class Meta:
        db_table = "ALARMS_PME"
        managed = False
