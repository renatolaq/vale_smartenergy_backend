from django.urls import path, include
from rest_framework import routers
from .views import IndexesViewSet, CompaniesViewSet, IndexesDataViewSet, ReverseIndexViewSet, HistoryViewSet, \
    SAPViewSet, ShowIndexesViewSet, IndexesScheduleDataViewSet, update_flat_rate_apportionment, SaveIndexViewSet

router = routers.DefaultRouter()
router.register(r'indexes', IndexesViewSet)
router.register(r'indexes-data', IndexesDataViewSet)
router.register(r'companies', CompaniesViewSet)
router.register(r'check-sap', SAPViewSet)
router.register(r'reverse', ReverseIndexViewSet)
router.register(r'save', SaveIndexViewSet)
router.register(r'indexes/logs', HistoryViewSet)
router.register(r'show-indexes', ShowIndexesViewSet)
router.register(r'schedule/generate-and-sender', IndexesScheduleDataViewSet)

urlpatterns = [
    path('statistical-indexes-api/', include(router.urls)),
    path('statistical-indexes-api/schedule/update-flat-rate-apportionment/', update_flat_rate_apportionment)
]
