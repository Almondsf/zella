from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from .models import Wallet, Transaction
from .serializers import TransferSerializer, TransactionSerializer
import uuid
from rest_framework.permissions import AllowAny, IsAuthenticated

class TransferView(APIView):

    def post(self, request):
        serializer = TransferSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        sender_wallet = request.user.wallet
        amount = serializer.validated_data['amount']
        phone_number = serializer.validated_data['phone_number']

        # check recipient exists
        try:
            recipient_wallet = Wallet.objects.get(user__phone_number=phone_number)
        except Wallet.DoesNotExist:
            return Response({'error': 'Recipient not found'}, status=status.HTTP_404_NOT_FOUND)

        # check sender is not sending to themselves
        if sender_wallet == recipient_wallet:
            return Response({'error': 'You cannot transfer to yourself'}, status=status.HTTP_400_BAD_REQUEST)

        # check sufficient balance
        if sender_wallet.balance < amount:
            return Response({'error': 'Insufficient balance'}, status=status.HTTP_400_BAD_REQUEST)

        # perform transfer atomically
        with transaction.atomic():
            sender_wallet.balance -= amount
            sender_wallet.save()

            recipient_wallet.balance += amount
            recipient_wallet.save()

            txn = Transaction.objects.create(
                reference=str(uuid.uuid4()),
                sender_wallet=sender_wallet,
                receiver_wallet=recipient_wallet,
                amount=amount,
                transaction_type='transfer',
                status='successful'
            )

        return Response({
            'message': 'Transfer successful',
            'transaction': TransactionSerializer(txn).data
        }, status=status.HTTP_200_OK)

class WalletBalanceView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        return Response({
            'balance': request.user.wallet.balance
        })