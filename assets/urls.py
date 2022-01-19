from django.urls import include, path
from rest_framework import routers

from assets import views as views_assets


urlpatterns = [

    # Assets
    path('assets-api/session_assets_find_basic/', views_assets.session_assets_get_find_basic),
    path('assets-api/session_assets/', views_assets.session_assets_get),
    path('assets-api/session_assets_post/', views_assets.session_assets_post),
    path('assets-api/session_assets_put/<int:pk>/', views_assets.session_assets_put),
    path('assets-api/session_assets/<int:pk>/', views_assets.session_assets_get_detail),

    path('assets-api/session_assets_post_Seasonality/<int:pk>/', views_assets.session_assets_post_Seasonality),
    path('assets-api/session_assets_put_Seasonality/', views_assets.session_assets_put_Seasonality),
    path('assets-api/show_assets/', views_assets.show_assets),

    #Generate CSV and PDF
    path('assets-api/session_assets_file/', views_assets.session_assets_file),

    # logs
    path('assets-api/session_log_basic_assets/<int:pk>/', views_assets.session_log_basic_assets),


    #list view
    path('assets-api/companyViews/', views_assets.show_company),
    path('assets-api/profileViews/', views_assets.show_profile),
    path('assets-api/submarketViews/', views_assets.show_submarket),
    path('assets-api/energyCompositionViews/<int:pk>/', views_assets.show_energyComposition),
    path('assets-api/usageContractViews/<int:pk>/', views_assets.show_contractUse),
    path('assets-api/get-by-profile/<int:pk>/', views_assets.session_assets_get_by_profile),
    path('assets-api/get-by-agent/<int:pk>/', views_assets.session_assets_get_by_agent),
    path('assets-api/get-profiles-basic/', views_assets.get_profiles_basic),
    path('assets-api/get-generators-assets/', views_assets.get_generators_assets),
    path('assets-api/get-consumers-assets/', views_assets.get_consumers_assets),
]