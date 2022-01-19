from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path
from rest_framework import routers
from core import views as views_core
from gauge_point import urls as gauge_router
from company import urls as company_router
from energy_contract import urls as energy_contract_router

routeLists = [
    gauge_router.routeList,
    company_router.routeList,
]
router = routers.DefaultRouter()
router.register(r'log', views_core.LogViewSet)
for routeList in routeLists:
    for route in routeList:
        router.register(route[0], route[1])

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    path('auth-api/', include('rest_framework.urls', namespace='rest_framework')),
    path('core-api/', include(router.urls)),
    path('core-api/validated_code_ccee/<str:code_ccee_request>/<str:type_request>/', views_core.validated_code_ccee),
    path('core-api/peek_time/<int:year>/<int:month>/<str:country>', views_core.get_peek_time),
    path('core-api/get_pme_token/', views_core.get_pme_token),
    path('core-api/logout_pme/', views_core.logout_pme),
    path('core-api/change_lang_pme/<str:lang>', views_core.change_lang_pme),
]

urlpatterns += energy_contract_router.urlpatterns
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
