from django.urls import path, include
from rest_framework import routers
from .views import (GlobalVariablesViewSet, icms_aliquot, taxes_and_tariffs, states, indexes, icms_logs, taxes_tariffs_logs, indexes_logs)

routeList = ((r'global-variables-api', GlobalVariablesViewSet))

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    path('global-variables-api/icms-aliquot/', icms_aliquot),
    path('global-variables-api/taxes-and-tariffs/', taxes_and_tariffs),
    path('global-variables-api/indexes/', indexes),
    path('global-variables-api/states/', states),
    path('global-variables-api/icms-aliquot/logs', icms_logs),
    path('global-variables-api/taxes-and-tariffs/logs', taxes_tariffs_logs),
    path('global-variables-api/indexes/logs', indexes_logs)
]