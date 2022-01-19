from django.urls import path, include
from rest_framework import routers
from .views import HistoryBalancesViewSet, CliqContractsViewSet, LastBalancesViewSet, generate_balance, schedule_save_balance, \
    save_balance, consolidate_balance, GetBalanceViewSet, LastBalanceFieldsViewSet, load_cache, \
    DetailedConsumptionReferenceViewSet

router = routers.DefaultRouter()
router.register(r'cliq-contracts', CliqContractsViewSet)
router.register(r'history-balance', HistoryBalancesViewSet)
router.register(r'last-balances', LastBalancesViewSet, base_name='last-balances')
router.register(r'get-balance', GetBalanceViewSet)
router.register(r'last-balance-fields', LastBalanceFieldsViewSet)
router.register(r'detailed-consumption-reference', DetailedConsumptionReferenceViewSet)

urlpatterns = [
    path('balance_market_settlement-api/', include(router.urls)),
    path('balance_market_settlement-api/consolidate-balance/<int:pk>/', consolidate_balance),
    path('balance_market_settlement-api/generate-balance/', generate_balance),
    path('balance_market_settlement-api/save-balance/', save_balance),
    path('balance_market_settlement-api/schedule/generate-balance/', schedule_save_balance),
    path('balance_market_settlement-api/load_cache/', load_cache)
]
