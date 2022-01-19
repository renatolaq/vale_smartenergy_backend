from django.urls import include, path
from rest_framework import routers
from notifications import views

router = routers.DefaultRouter()
router.register("", views.NotificationViewSet, basename="Notification")

urlpatterns = [
    path("notifications/", include(router.urls)),
    path("notifications/get_modules_fields", views.notifications_modules_fields),
    path("notifications/validate_string", views.validate_string),
    path("notifications/execute_string", views.execute_string),
    path("notifications/execute_notification_daily", views.execute_notification_daily),
    path(
        "notifications/execute_notification_high_frequency",
        views.execute_notification_high_frequency,
    ),
    path(
        "notifications/check_available_name/<str:name>/<int:notification_id>",
        views.NotificationViewSet.as_view({"get": "check_available_name"}),
    ),
    path(
        "notifications/check_available_name/<str:name>",
        views.NotificationViewSet.as_view({"get": "check_available_name"}),
    ),
    path(
        "notifications/change_status/<int:id>",
        views.NotificationViewSet.as_view({"patch": "change_status"}),
    ),
    path(
        "notifications/<int:notification_pk>/history/<int:history_pk>",
        views.NotificationViewSet.as_view({"get": "history"}),
    ),
    path("notifications/get_lexemes", views.get_lexemes),
]
