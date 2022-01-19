from django.urls import path
from agents import views as views_agents


# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    path('agents-api/session_agents_find_basic/', views_agents.session_agents_get_find_basic),
    path('agents-api/session_agents/', views_agents.session_agents_get),
    path('agents-api/session_agents_post/', views_agents.session_agents_post),
    path('agents-api/session_agents_put/<int:pk>/', views_agents.session_agents_put),
    path('agents-api/session_agents/<int:pk>/', views_agents.session_agents_get_detail),
    path('agents-api/get_data_agents/', views_agents.get_data_agents),
    path('agents-api/get_data_agents_basic/', views_agents.get_data_agents_basic),
    path('agents-api/session_log_basic_agents/<int:pk>/', views_agents.session_log_basic_agents),
    path('agents-api/session_agents_file/', views_agents.session_agents_file)
]
