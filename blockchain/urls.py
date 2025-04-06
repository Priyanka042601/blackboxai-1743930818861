from django.urls import path
from .views import TransactionVerifyView, EventListenerView

urlpatterns = [
    path('transactions/<str:transaction_hash>/', TransactionVerifyView.as_view(), name='transaction-verify'),
    path('events/listen/', EventListenerView.as_view(), name='event-listener'),
]