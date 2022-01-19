from django.urls import path
from energy_contract import views

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    path('energy-contract-api/session_energy_contract_post/', views.session_energy_contract_post),
    path('energy-contract-api/session_energy_contract/', views.session_energy_contract_get),
    path('energy-contract-api/session_energy_contract/<int:pk>/', views.session_energy_contract_get_detail),
    path('energy-contract-api/session_energy_contract_put/<int:pk>/', views.session_energy_contract_put),
    path('energy-contract-api/session_energy_contract_cancel_temporary/<int:pk>/', views.session_energy_contract_cancel_temporary),
    path('energy-contract-api/session_energy_contract_save_temporary/<int:pk>/', views.session_energy_contract_save_temporary),

    path('energy-contract-api/session_log_basic_energy_contract/<int:pk>/', views.session_log_basic_energy_contract),
    path('energy-contract-api/session_energy_contract_file/', views.session_energy_contract_file),
    path('energy-contract-api/get_energy_product/', views.get_energy_product),

    path('energy-contract-api/session_energy_contract_attachment/', views.session_energy_contract_attachment_get),
    path('energy-contract-api/session_energy_contract_attachment_post/', views.session_energy_contract_attachment_post),
    path('energy-contract-api/session_energy_contract_attachment_put/<int:pk>/',views.session_energy_contract_attachment_put),
    path('energy-contract-api/session_energy_contract_attachment/<int:pk>/',views.session_energy_contract_attachment_get_detail),

    path('energy-contract-api/session_valid_contract_name/<str:name>/', views.valid_contract_name),
    path('energy-contract-api/show_variable/', views.show_variable),
    path('energy-contract-api/session_energy_contract_find_basic/', views.session_energy_contract_get_find_basic),
    path('energy-contract-api/get_data_agents_basic/', views.get_data_agents_basic),
    path('energy-contract-api/get_data_profile_basic/', views.get_data_profile_basic),
    path('energy-contract-api/list_energy_contract/', views.list_energy_contract_summary),
    path('energy-contract-api/list_flexibilization_type/', views.list_flexibilization_type),
    path('energy-contract-api/update_current_price_energy_contract/', views.update_current_price_energy_contract)
]

