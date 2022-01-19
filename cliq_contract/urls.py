from django.urls import path
from cliq_contract import views as views_cliq_contract

#Included URLs for all models but GET method is intended to be used
# only with session_cliq_contract, which returns all related data
#For PUT and POST you should use proper model URL
urlpatterns = [
    path('cliq_contract-api/session_cliq_contract/', views_cliq_contract.session_cliq_contract_get), #GET
    path('cliq_contract-api/session_cliq_contract_post/', views_cliq_contract.session_cliq_contract_post), #POST
    path('cliq_contract-api/session_cliq_contract_put/<int:pk>/', views_cliq_contract.session_cliq_contract_put), #PUT
    path('cliq_contract-api/session_cliq_contract/<int:pk>/', views_cliq_contract.session_cliq_contract_get_detail), #GET DETAIL
    path('cliq_contract-api/session_cliq_contract_modulation_read', views_cliq_contract.session_cliq_contract_modulation_read),

    path('cliq_contract-api/session_log_basic_cliq_contract/<int:pk>/', views_cliq_contract.session_log_basic_cliq_contract),
    path('cliq_contract-api/session_cliq_contract_export_file/', views_cliq_contract.session_cliq_contract_file),
    path('cliq_contract-api/session_cliq_contract_modulation_template' , views_cliq_contract.modulation_template),

    path('cliq_contract-api/session_view_max_value_contract/<int:pk_contract>/', views_cliq_contract.session_calculator_value_max), #GET used to calculate the maximum contract value
]
