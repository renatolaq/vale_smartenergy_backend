from django.urls import path, include
from rest_framework import routers
from .views import *

router = routers.DefaultRouter()
router.register(r'gross-consumption', GrossConsumptionReportsViewSet)
router.register(r'gross-consumption/logs', LogReportsViewSet)
router.register(r'gross-consumption-data', GrossConsumptionDataViewSet)
router.register(r'gross-consumption-save', GrossConsumptionSaveViewSet)
router.register(r'projected-consumption', ProjectedConsumptionReportsViewSet)
router.register(r'projected-consumption-list', ProjectedConsumptionReportListViewSet)
router.register(r'projected-consumption/logs', LogReportsViewSet)
router.register(r'projected-consumption-data', ProjectedConsumptionDataViewSet)
router.register(r'projected-consumption-change-datasource', ProjectedConsumptionChangeDatasourceViewSet)
router.register(r'projected-consumption-save', ProjectedConsumptionSaveViewSet)
router.register(r'detailed-consumption', DetailedConsumptionReportsViewSet)
router.register(r'detailed-consumption/logs', LogReportsViewSet)
router.register(r'detailed-consumption-data', DetailedConsumptionDataViewSet)
router.register(r'detailed-consumption-change-losstype', DetailedConsumptionChangeLossTypeViewSet)
router.register(r'detailed-consumption-save', DetailedConsumptionSaveViewSet)

router.register(r'detailed-consumption-new', DetailedConsumptionReportsViewSetNew)
router.register(r'detailed-consumption-new/logs', LogReportsViewSetNew)
router.register(r'detailed-consumption-new-data', DetailedConsumptionDataViewSetNew)
router.register(r'detailed-consumption-new-change-losstype', DetailedConsumptionChangeLossTypeViewSetNew)
router.register(r'detailed-consumption-new-change-datasource', DetailedConsumptionChangeChangeDatasourceViewSet)
router.register(r'detailed-consumption-new-save', DetailedConsumptionSaveViewSetNew)

urlpatterns = [
    path('reports-api/', include(router.urls)),
    path('reports-api/schedule/generate-gross-consumption/', generate_gross_consumption),
    path('reports-api/schedule/generate-projected-consumption/', generate_projected_consumption),
    #path('reports-api/schedule/generate-detailed-projected-consumption/', generate_detailed_projected_consumption),
    path('reports-api/schedule/generate-detailed-projected-consumption/', generate_detailed_projected_consumption_new)
]
