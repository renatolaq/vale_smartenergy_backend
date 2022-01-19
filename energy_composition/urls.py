from django.urls import path
from energy_composition import views as views_energy_composition

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    path('energy_composition-api/session_energy_composition/', views_energy_composition.session_energy_composition_get),
    path('energy_composition-api/session_energy_composition_get_find_basic/', views_energy_composition.session_energy_composition_get_basic_find),
    path('energy_composition-api/session_energy_composition_post/', views_energy_composition.session_energy_composition_post),
    path('energy_composition-api/session_energy_composition_put/<int:pk>/',
         views_energy_composition.session_energy_composition_put),
    path('energy_composition-api/session_energy_composition/<int:pk>/',
         views_energy_composition.session_energy_composition_get_detail),
    path('energy_composition-api/session_energy_composition_file/',
         views_energy_composition.session_energy_composition_file),

     path('energy_composition-api/session_log_basic_composition/<int:pk>/',
         views_energy_composition.session_log_basic_energy_composition),
]
