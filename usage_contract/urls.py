from django.urls import include, path
from rest_framework import routers

from .views import CompanyViewSet
from .views import EnergyDealerViewSet
from .views import RatedVoltageViewSet
from .views import UsageContractViewSet
from .views import RatePostExceptionViewSet
from .views import UploadFileUsageContractViewSet

from usage_contract import views as view_ctu

router = routers.DefaultRouter()
router.register('companies', CompanyViewSet)
router.register('energydealers', EnergyDealerViewSet, basename='Company')
router.register('ratedvoltages', RatedVoltageViewSet)
router.register('ratepostexceptions', RatePostExceptionViewSet)
router.register('usagecontracts', UsageContractViewSet)
router.register('uploadfileusagecontract', UploadFileUsageContractViewSet)

urlpatterns = [
    path('usage-contract/', include(router.urls)),
    path('usage-contract/session_log/<int:pk>/', view_ctu.session_log),
    path('usage-contract/renovacao/<int:_pk>/', view_ctu.renovacao),
    path('usage-contract/download_file/<int:_pk>', view_ctu.download_file),
    path('usage-contract/check_ctu_number/<str:_number>/<int:_ctu_id>/', view_ctu.check_ctu_number),
    path('usage-contract/check_ctu_number/<str:_number>/', view_ctu.check_ctu_number),
    path('usage-contract/get_contract_number/<int:company_id>/', view_ctu.get_contract_number),
    path('usage-contract/renew_expired_contracts/', view_ctu.renew_expired_contracts)
]
