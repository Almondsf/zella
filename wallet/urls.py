from django.urls import path
from .views import TransferView, WalletBalanceView, TransactionHistoryView

urlpatterns = [
    path('transfer/', TransferView.as_view(), name='transfer'),
    path('balance/', WalletBalanceView.as_view(), name='balance'),
    path('transaction-history/', TransactionHistoryView.as_view(), name='transaction-history')
]