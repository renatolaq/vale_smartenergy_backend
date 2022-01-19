from django.urls import path, include
from rest_framework import routers

from contract_dispatch import views

router = routers.DefaultRouter()
router.register(
    "", views.CliqContractCCEEStateViewset, basename="CliqContractCCEEState"
)

urlpatterns = [
    path("cliq_contract_ccee_state/", include(router.urls)),
    path("contract_dispatch/", views.contract_dispatch),
    path("contract_dispatch/update_contracts_status/", views.update_contracts_status),
    path(
        "contract_dispatch/contracts_to_send/<int:year>/<int:month>/",
        views.contracts_to_send,
    ),
    path(
        "contract_dispatch/contracts_to_send/<int:year>/<int:month>/<int:balance_id>/",
        views.contracts_to_send,
    ),
    path("contract_dispatch/<int:pk>/", views.contract_dispatch_detail),
    path(
        "contract_dispatch/<int:pk>/contracts/",
        views.contract_dispatch_detail_contracts,
    ),
    path("contract_dispatch/list_balance/<int:year>/<int:month>/", views.list_balance),
    path("contract_dispatch/ccee_synchronize/", views.ccee_synchronize),
    path("contract_dispatch/ccee_synchronize_discrepancies/", views.ccee_synchronize_discrepancies),
    path("contract_dispatch/pdf/", views.contract_dispatch_pdf),
    path("contract_dispatch/xlsx/", views.contract_dispatch_xlsx),
    path(
        "contract_dispatch/<int:pk>/contracts/pdf/",
        views.contract_dispatch_detail_contracts_pdf,
    ),
    path(
        "contract_dispatch/<int:pk>/contracts/xlsx/",
        views.contract_dispatch_detail_contracts_xlsx,
    ),
    path(
        "contract_dispatch/contracts_to_send/<int:year>/<int:month>/pdf/",
        views.contracts_to_send_pdf,
    ),
    path(
        "contract_dispatch/contracts_to_send/<int:year>/<int:month>/xlsx/",
        views.contracts_to_send_xlsx,
    ),
    path(
        "contract_dispatch/contracts_to_send/<int:year>/<int:month>/<int:balance_id>/pdf/",
        views.contracts_to_send_pdf,
    ),
    path(
        "contract_dispatch/contracts_to_send/<int:year>/<int:month>/<int:balance_id>/xlsx/",
        views.contracts_to_send_xlsx,
    ),
    path("contract_dispatch/pdf_by_ids/<int:year>/<int:month>/", views.pdf_by_ids,),
    path("contract_dispatch/xlsx_by_ids/<int:year>/<int:month>/", views.xlsx_by_ids,),
    path(
        "contract_dispatch/pdf_by_ids/<int:year>/<int:month>/<int:balance_id>/",
        views.pdf_by_ids,
    ),
    path(
        "contract_dispatch/xlsx_by_ids/<int:year>/<int:month>/<int:balance_id>/",
        views.xlsx_by_ids,
    ),
]
