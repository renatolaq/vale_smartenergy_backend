from django.urls import path
from SmartEnergy.utils.request.http_request_handling import http_method_handling
from .views import list_energy_contract_prioritization, get_energy_contract_prioritization, \
    save_energy_contract_prioritization, get_energy_contract_prioritization_history, \
    get_energy_contract_prioritization_revision, activate_energy_contract_prioritization, \
    activate_energy_contract_prioritization, deactivate_energy_contract_prioritization, \
    save_energy_contract_prioritization_order, export_energy_contract_prioritization


urlpatterns = [
    path('v1/energyContractPrioritization/', http_method_handling(
        get=list_energy_contract_prioritization,
        post=save_energy_contract_prioritization)),
    path('v1/energyContractPrioritization/export', http_method_handling(
        get=export_energy_contract_prioritization)),
    path('v1/energyContractPrioritization/<int:id>', http_method_handling(
        get=get_energy_contract_prioritization,
        put=save_energy_contract_prioritization)),
    path('v1/energyContractPrioritization/<int:id>/history', http_method_handling(
        get=get_energy_contract_prioritization_history)),
    path('v1/energyContractPrioritization/<int:id>/revision/<int:revision>', http_method_handling(
        get=get_energy_contract_prioritization_revision)),
    path('v1/energyContractPrioritization/<int:id>/activate', http_method_handling(
        put=activate_energy_contract_prioritization)),
    path('v1/energyContractPrioritization/<int:id>/deactivate', http_method_handling(
        put=deactivate_energy_contract_prioritization)),
    path('v1/energyContractPrioritization/priority', http_method_handling(
        put=save_energy_contract_prioritization_order))
]
