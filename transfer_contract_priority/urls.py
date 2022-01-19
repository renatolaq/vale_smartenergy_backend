from django.urls import path
from transfer_contract_priority import views as views_transf_cntrct_priority

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    path('transfer_contract_priority-api/session_transfer_contract_priority/', views_transf_cntrct_priority.session_transfer_contract_priority),
    path('transfer_contract_priority-api/session_log_transfer_contract_priority/<int:pk>/', views_transf_cntrct_priority.session_log_transfer_contract_priority),
    path('transfer_contract_priority-api/session_log_basic_transfer_contract_priority/<int:pk>/', views_transf_cntrct_priority.session_log_basic_transfer_contract_priority),
    path('transfer_contract_priority-api/session_transfer_contract_priority_reorder/', views_transf_cntrct_priority.session_transfer_contract_priority_reorder),
    path('transfer_contract_priority-api/session_transfer_contract_priority_export_file/', views_transf_cntrct_priority.session_transfer_contract_priority_file),
]
