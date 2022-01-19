from django.urls import path
from SmartEnergy.utils.request.http_request_handling import http_method_handling
from .views import list_company_budgets, create_company_budget, \
    update_company_budget, get_company_budget, release_company_budget_to_analysis, \
    disapprove_company_budget, release_company_budget_to_operational_manager_approval,\
    release_company_budget_to_energy_manager_approval, energy_manager_company_budget_approve, \
    calculate_budget, autofilled_fields, budget_already_exists, export_company_budgets, get_company_budget_revision, release_to_technical_area

urlpatterns = [
    path('v1/budget/', http_method_handling(get=list_company_budgets,
                                             post=create_company_budget)),
    path('v1/budget/<int:id>',
         http_method_handling(put=update_company_budget, get=get_company_budget)),
    path('v1/budget/<int:id>/revision/<int:revision_number>',
         http_method_handling(get=get_company_budget_revision)),
    path('v1/budget/<int:id>/sendToTechnicalArea',
         http_method_handling(post=release_to_technical_area)),
    path('v1/budget/<int:id>/releaseToAnalysis',
         http_method_handling(post=release_company_budget_to_analysis)),
    path('v1/budget/<int:id>/releaseToOperationalManagerApproval',
         http_method_handling(post=release_company_budget_to_operational_manager_approval)),
    path('v1/budget/<int:id>/operationalManagerApprove',
         http_method_handling(post=release_company_budget_to_energy_manager_approval)),
    path('v1/budget/<int:id>/energyManagerApprove',
         http_method_handling(post=energy_manager_company_budget_approve)),
    path('v1/budget/<int:id>/disapprove',
         http_method_handling(post=disapprove_company_budget)),
    path('v1/budget/calculateBudget',
         http_method_handling(post=calculate_budget)),
    path('v1/budget/<int:company_id>/<int:year>/autofilledFields',
         http_method_handling(get=autofilled_fields)),
    path('v1/budget/<int:company_id>/<int:year>/exists',
         http_method_handling(get=budget_already_exists)),
    path('v1/budget/export', http_method_handling(get=export_company_budgets))]
