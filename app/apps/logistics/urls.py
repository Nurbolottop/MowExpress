from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('tracking/', views.tracking_view, name='tracking'),
    path('shipment/<int:pk>/print/', views.shipment_print_view, name='shipment_print'),
]
