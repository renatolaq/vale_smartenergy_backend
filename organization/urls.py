from django.urls import path

from organization import views as views_organization

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    # Organization
    path('organization-api/session_organization/', views_organization.session_organizational_get),
    path('organization-api/session_organization_post/', views_organization.session_organizational_post),
    path('organization-api/session_organization_put/<int:pk>/<str:classe>/',
         views_organization.session_organizational_put),
    path('organization-api/session_organization/<int:pk>/<str:classe>/',
         views_organization.session_organizational_get_detail),
    path('organization-api/organization_find/', views_organization.OrganizationFind.as_view()),
    path('organization-api/organization_find_file/', views_organization.organization_find_file),
    # logs
    path('organization-api/session_log_basic_organization/<int:pk>/<str:classe>/', views_organization.organization_log_basic),

    path('organization-api/show_organization/<int:model>/', views_organization.show_organization),
    path('organization-api/session_show_values_organization/', views_organization.show_values_organization),

    path('organization-api/session_organizational_find_basic/', views_organization.session_organizational_find_basic),
]
