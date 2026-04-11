from django.urls import path
from . import views

urlpatterns = [
    path('crm/login/', views.manager_login_view, name='manager_login'),
    path('crm/logout/', views.manager_logout_view, name='manager_logout'),
    path('crm/', views.manager_dashboard_view, name='manager_dashboard'),
    path('crm/profile/', views.manager_profile_view, name='manager_profile'),
    path('crm/clients/', views.manager_clients_view, name='manager_clients'),
    path('crm/clients/create/', views.manager_client_create_view, name='manager_client_create'),
    path('crm/clients/<int:pk>/', views.manager_client_detail_view, name='manager_client_detail'),
    path('crm/shipments/', views.manager_shipments_view, name='manager_shipments'),
    path('crm/shipments/create/', views.manager_shipment_create_view, name='manager_shipment_create'),
    path('crm/shipments/<int:pk>/', views.manager_shipment_detail_view, name='manager_shipment_detail'),
    path('crm/shipments/<int:pk>/edit/', views.manager_shipment_edit_view, name='manager_shipment_edit'),
    path('crm/shipments/<int:pk>/status/', views.manager_shipment_status_view, name='manager_shipment_status'),
    path('crm/shipments/<int:pk>/status/quick/', views.manager_shipment_status_quick_update_view, name='manager_shipment_status_quick'),
    path('crm/shipments/<int:pk>/print/', views.manager_shipment_print_view, name='manager_shipment_print'),
    path('crm/shipments/<int:pk>/sticker/', views.manager_shipment_sticker_view, name='manager_shipment_sticker'),
    path('crm/analytics/', views.manager_analytics_view, name='manager_analytics'),
    path('crm/settings/', views.manager_settings_view, name='manager_settings'),
    path('crm/api/price-tiers/', views.api_price_tiers, name='api_price_tiers'),
]
