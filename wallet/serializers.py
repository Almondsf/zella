from rest_framework import serializers
from .models import Wallet, Transaction

class TransferSerializer(serializers.Serializer):
    phone_number = serializers.CharField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError('Amount must be greater than zero')
        return value
    
    


class TransactionSerializer(serializers.ModelSerializer):
    direction = serializers.SerializerMethodField()
    
    class Meta:
        model = Transaction
        fields = ['reference', 'amount', 'transaction_type', 'status', 'direction', 'created_at']
        
    def get_direction(self, obj):
        request = self.context.get('request')
        if obj.sender_wallet.user == request.user:
            return 'debit'
        return 'credit'