from django.urls import path
from profiles import views as views_profile

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    path('profile-api/session_profile_find_basic/', views_profile.session_profile_find_basic),
    path('profile-api/session_profile/', views_profile.session_profile_get), #GET
    path('profile-api/session_profile_post/', views_profile.session_profile_post), #POST
    path('profile-api/session_profile_put/<int:pk>/', views_profile.session_profile_put), #PUT
    path('profile-api/session_profile/<int:pk>/', views_profile.session_profile_get_detail), #GET detail
    path('profile-api/session_log_basic_profile/<int:pk>/', views_profile.session_log_basic_profile),
    path('profile-api/session_profile_file/', views_profile.session_profile_file),
]
