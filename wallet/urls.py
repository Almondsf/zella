from django.urls import path
from .views import TransferView, WalletBalanceView

urlpatterns = [
    path('transfer/', TransferView.as_view(), name='transfer'),
    path('balance/', WalletBalanceView.as_view(), name='balance'),
]