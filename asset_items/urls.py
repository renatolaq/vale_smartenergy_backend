from django.urls import path
from asset_items import views as views_asset_items
from asset_items import views

#from rest_framework import routers

#router = routers.DefaultRouter()


#routeList = ((r'session_asset_items', ),)

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.

urlpatterns = [
    path('asset-items-api/session_asset_items_find_basic/', views_asset_items.session_asset_items_get_find_basic),
    path('asset-items-api/session_asset_items/', views_asset_items.session_asset_items_get),
    path('asset-items-api/session_asset_items_post/', views_asset_items.session_asset_items_post),
    path('asset-items-api/session_asset_items_put/<int:pk>/', views_asset_items.session_asset_items_put),
    path('asset-items-api/session_asset_items/<int:pk>/', views_asset_items.session_asset_items_get_detail),

    path('asset_items-api/session_log_basic_asset_items/<int:pk>/', views_asset_items.session_log_basic_asset_items), 
    path('asset-items-api/session_asset_items_file/', views_asset_items.session_asset_items_file),

    # list 
    path('asset-items-api/show_company/', views_asset_items.show_company),
    path('asset-items-api/show_assets_basic/', views_asset_items.show_assets_basic),
    path('asset-items-api/show_assets_get_basic/', views_asset_items.show_assets_basic),
    path('asset-items-api/show_energyComposition/<int:pk>/', views_asset_items.show_energyComposition),
   

    # Seasonality Active Item
    path('asset-items-api/session_asset_items_put_Seasonality_Asset_Item/', views_asset_items.session_asset_items_put_Seasonality_Asset_Item),
    path('asset-items-api/session_asset_items_post_Seasonality_Asset_Item/<int:pk>/', views_asset_items.session_asset_items_post_Seasonality_Asset_Item),

    # Seasonality Depreciation
    path('asset-items-api/session_asset_items_post_Seasonality_Depreciation/<int:pk>/', views_asset_items.session_asset_items_post_Seasonality_Depreciation),
    path('asset-items-api/session_asset_items_put_Seasonality_Depreciation/', views_asset_items.session_asset_items_put_Seasonality_Depreciation),

    # Seasonality Item Cost
    path('asset-items-api/session_asset_items_post_Seasonality_Item_Cost/<int:pk>/', views_asset_items.session_asset_items_post_Seasonality_Item_Cost),
    path('asset-items-api/session_asset_items_put_Seasonality_Item_Cost/', views_asset_items.session_asset_items_put_Seasonality_Item_Cost)

]




