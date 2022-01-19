from django.http import HttpResponse
from django_filters import rest_framework as filters
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
    action,
)

from core.models import Log as CoreLog
from .utils.locale import get_request_language
from .utils.pagination import NotificationResultsSetPagination
from notifications.business.notifications_business import NotificationBusiness
from notifications.business.notification_processor import NotificationProcessor
from rest_framework.filters import OrderingFilter

from .models import Notification
from .serializers import (
    NotificationSerializer,
    NotificationListSerializer,
    NotificationDetailsSerializer,
    NotificationWriteSerializer,
    LogSerializer,
    NotificationPDFSerializer,
)

from SmartEnergy.auth.IAM import IAMAuthentication
from SmartEnergy.auth import groups, permissions, check_permission

class NotificationFilter(filters.FilterSet):
    name = filters.CharFilter(field_name="name", lookup_expr="icontains")
    description = filters.CharFilter(field_name="description", lookup_expr="icontains")
    notification_username = filters.CharFilter(
        field_name="notification_username", lookup_expr="icontains"
    )
    start_date = filters.DateFilter(field_name="start_date", lookup_expr="exact")
    status = filters.BooleanFilter(field_name="status")
    frequency = filters.CharFilter(
        field_name="notification_frequency__notification_frequency", lookup_expr="exact"
    )
    notification_type = filters.CharFilter(
        field_name="notification_type__notification_type", lookup_expr="exact"
    )

    class Meta:
        model = Notification
        fields = [
            "name",
            "description",
            "notification_username",
            "start_date",
            "status",
            "frequency",
            "notification_type",
        ]


class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    filter_backends = [filters.DjangoFilterBackend, OrderingFilter]
    filterset_class = NotificationFilter
    ordering_fields = [
        "name",
        "description",
        "notification_type",
        "notification_frequency",
        "notification_username",
        "start_date",
        "status",
    ]
    ordering = ["id"]
    pagination_class = NotificationResultsSetPagination

    def get_serializer_class(self):
        serializer_class = self.serializer_class
        if self.request.method in ("GET",):
            if "pk" in self.kwargs:
                serializer_class = NotificationDetailsSerializer
            else:
                serializer_class = NotificationListSerializer
        if self.request.method in ("POST", "PUT",):
            serializer_class = NotificationWriteSerializer
        if self.action == "export_to_pdf" or self.action == "export_to_xls":
            serializer_class = NotificationPDFSerializer
        return serializer_class

    @action(methods=["get"], detail=False)
    def check_available_name(self, request, *args, **kwargs):
        name = kwargs.get("name")
        notification_id = kwargs.get("notification_id")
        response = NotificationBusiness.check_available_name(name, notification_id)
        return Response(response, status=status.HTTP_200_OK)

    @action(methods=["patch"], detail=False)
    def change_status(self, request, id):
        request_status = request.data["status"]
        response = NotificationBusiness.change_status(id, request_status)
        return Response(response, status=status.HTTP_200_OK)

    @action(methods=["get"], detail=True)
    def history(self, request, *args, **kwargs):
        notification_pk = (
            kwargs.get("pk") if "pk" in kwargs else kwargs.get("notification_pk")
        )
        history_pk = kwargs.get("history_pk")

        logs = CoreLog.objects.filter(
            table_name="NOTIFICATION", field_pk=notification_pk
        )
        if history_pk:
            logs = logs.filter(pk=history_pk)

        serialized_logs = LogSerializer(
            logs.all(), many=True, context={"request": request}
        )
        return Response(serialized_logs.data, status=status.HTTP_200_OK)

    @action(["GET"], detail=False)
    def export_to_pdf(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        language = get_request_language(request)
        pdf = NotificationBusiness.export(
            serializer.data, type="pdf", language=language
        )
        return HttpResponse(
            pdf, content_type="application/pdf", status=status.HTTP_200_OK
        )

    @action(["GET"], detail=False)
    def export_to_xls(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        language = get_request_language(request)
        xlsx = NotificationBusiness.export(
            serializer.data, type="xlsx", language=language
        )
        return HttpResponse(
            xlsx,
            content_type="application/excel; charset=utf-8-sig",
            status=status.HTTP_200_OK,
        )


@api_view(["GET"])
def notifications_modules_fields(request):

    modules_fields = NotificationBusiness.retrieve_modules_fields()

    return Response(modules_fields, status=status.HTTP_200_OK)


@api_view(["POST"])
def validate_string(request):

    string = request.data["string"]
    module_nome = request.data["module"]

    response = NotificationBusiness.analyze_string(string, module_nome)

    return Response(response)


@api_view(["POST"])
def execute_string(request):
    string = request.data["string"]
    module_nome = request.data["module"]

    response = NotificationBusiness.execute_string(string, module_nome)

    return Response(response)


@api_view(["GET"])
@authentication_classes([IAMAuthentication])
@check_permission(groups.administrator, [permissions.VIEW, permissions.EDITN1])
def execute_notification_daily(request):
    NotificationProcessor.execute_notifications()
    return Response(status=status.HTTP_200_OK)


@api_view(["GET"])
@authentication_classes([IAMAuthentication])
@check_permission(groups.administrator, [permissions.VIEW, permissions.EDITN1])
def execute_notification_high_frequency(request):
    NotificationProcessor.execute_pme_notifications()
    return Response(status=status.HTTP_200_OK)


@api_view(["POST"])
def get_lexemes(request):
    string = request.data["string"]

    lexemes = NotificationBusiness.get_lexemes(string)
    return Response(lexemes, status=status.HTTP_200_OK)
