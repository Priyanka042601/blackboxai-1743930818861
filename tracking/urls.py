from django.urls import path
from .views import (
    ShipmentListCreateView,
    ShipmentRetrieveUpdateView,
    SensorDataCreateView,
    AlertListView,
    AlertResolveView
)

urlpatterns = [
    path('shipments/', ShipmentListCreateView.as_view(), name='shipment-list-create'),
    path('shipments/<str:tracking_id>/', ShipmentRetrieveUpdateView.as_view(), name='shipment-detail'),
    path('shipments/<str:tracking_id>/sensor-data/', SensorDataCreateView.as_view(), name='sensor-data-create'),
    path('alerts/', AlertListView.as_view(), name='alert-list'),
    path('alerts/<int:pk>/resolve/', AlertResolveView.as_view(), name='alert-resolve'),
]