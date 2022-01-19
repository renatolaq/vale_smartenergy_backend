"""SmartEnergy URL Configuration
The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework_swagger.views import get_swagger_view

schema_view = get_swagger_view(title='SmartEnery API')


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api-docs/', schema_view),
    path('', include('core.urls')),
    path('', include('organization.urls')),
    path('', include('assets.urls')),
    path('', include('company.urls')),
    path('', include('gauge_point.urls')),
    path('', include('consumption_metering_reports.urls')),
    path('', include('agents.urls')),
    path('', include('profiles.urls')),
    path('', include('asset_items.urls')),
    path('', include('energy_composition.urls')),
    path('', include('energy_contract.urls')),
    path('', include('cliq_contract.urls')),
    path('', include('transfer_contract_priority.urls')),
    path('', include('budget.urls')),
    path('', include('global_variables.urls')),
    path('', include('statistical_indexes.urls')),
    path('', include('balance_report_market_settlement.urls')),
    path('', include('usage_contract.urls')),
    path('', include('manual_import.urls')),
    path('', include('plan_monitoring.urls')),
    path('', include('contract_allocation_parameters.urls')),
    path('', include('occurrence_record.urls')),
    path('', include('contract_dispatch.urls')),
    path('', include('contract_allocation_report.urls')),
    path('', include('notifications.urls')),
    path('api-core/', include('global_variables.urls')),
]
