from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from .models import Wallet, Transaction
from .serializers import TransferSerializer, TransactionSerializer
import uuid
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.db.models import Q
from .paystack import initialize_payment

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

class TransactionHistoryView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        transactions = Transaction.objects.filter(Q(sender_wallet__user=request.user) | Q(receiver_wallet__user=request.user))
        
        serializer = TransactionSerializer(transactions, many=True, context={'request': request})
        return Response({
            'transaction history': serializer.data
        })

class DepositView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        amount = request.data.get('amount')
        email = request.user.email
        reference_id = str(uuid.uuid4())
        
        txn = Transaction.objects.create(
            reference=reference_id,
            amount=amount,
            transaction_type='deposit',
            status='pending',
            receiver_wallet=request.user.wallet
        )
        paystack_response = initialize_payment(email, amount, reference_id)
        if paystack_response['status'] == True:
            return Response({
                'message': 'Deposit Initiated',
                'payment_link': paystack_response['data']['authorization_url'],
                'reference': paystack_response['data']['reference']
                
            }, status=status.HTTP_200_OK)
        else:
            txn.delete()
            return Response({
            'error': 'Could not initialize payment'
            }, status=status.HTTP_400_BAD_REQUEST)
            