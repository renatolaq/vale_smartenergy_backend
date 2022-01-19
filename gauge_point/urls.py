from django.urls import path
from gauge_point import views as views_gauge

routeList = ((r'gauge', views_gauge.GaugePointViewSet),)

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    path('gauge_point-api/session_gauge_point_post/', views_gauge.session_gauge_point_post),
    path('gauge_point-api/session_gauge_point/', views_gauge.session_gauge_point_get),
    path('gauge_point-api/session_gauge_point_put/<int:pk>/', views_gauge.session_gauge_point_put),
    path('gauge_point-api/session_gauge_point/<int:pk>/', views_gauge.session_gauge_point_get_detail),
    path('gauge_point-api/session_log_basic_gauge_point/<int:pk>/', views_gauge.session_log_basic_gauge_point),
    path('gauge_point-api/session_gauge_company/', views_gauge.session_gauge_company),
    path('gauge_point-api/get_data_source_pme/', views_gauge.get_data_source_pme),
    path('gauge_point-api/session_gauge_point_file/', views_gauge.session_gauge_point_file),
    path('gauge_point-api/validate_gauge_using/<int:pk>/', views_gauge.validated_using),

    path('gauge_point-api/session_gauge_point_find_basic/', views_gauge.session_gauge_point_find_basic),
    path('gauge_point-api/session_show_gauge_type/', views_gauge.session_show_gauge_type),
    path('gauge_point-api/session_show_meter_type/', views_gauge.session_show_meter_type),
    
    
]