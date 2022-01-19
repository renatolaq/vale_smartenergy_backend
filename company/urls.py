from django.urls import include, path
from rest_framework import routers
from company import views as view_company

router = routers.DefaultRouter()
routeList = ((r'company', view_company.CompanyViewSet), (r'country', view_company.CountriesViewSet),
             (r'address', view_company.AddressViewSet),)

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    path('company-api/', include(router.urls)),
    path('company-api/session_company/', view_company.session_company_get),
    path('company-api/session_company_post/', view_company.session_company_post),
    path('company-api/session_company_put/<int:pk>/', view_company.session_company_put),
    path('company-api/session_company/<int:pk>/', view_company.session_company_get_detail),
    path('company-api/company_find/', view_company.CompanyFind.as_view()),
    path('company-api/company_find_basic/', view_company.CompanyFindBasic.as_view()),
    path('company-api/get_state_by_country/', view_company.get_state_by_country),
    path('company-api/get_country/', view_company.get_country),
    path('company-api/get_cities_by_state/', view_company.get_cities_by_state),
    path('company-api/get_energy_composition_company/<int:pk>/', view_company.get_energy_composition_company),
    path('company-api/company_find_file/', view_company.session_company_file),
    path('company-api/session_basic_log/<int:pk>/', view_company.session_basic_log),
    path('company-api/validated_sap/<str:id_sap_resquest>/', view_company.validated_code_sap),
    path('company-api/list_company_basic/', view_company.list_company_basic),    
    path('company-api/list_account_types/', view_company.list_account_types),    
    path('company-api/validated_company_using/<int:pk>/', view_company.validated_using),
    path('company-api/get_energy_compositions_basic/<int:company_id>/', view_company.get_energy_compositions_basic)
]
