from rest_framework import serializers
from .models import PaymentIntent, Item, SplitPayment, CustomerInfo

class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = ['name', 'amount', 'quantity']

class SplitPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SplitPayment
        fields = ['beneficiary_id', 'amount']

class CustomerInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerInfo
        fields = ['name', 'email', 'phone']

class PaymentIntentSerializer(serializers.ModelSerializer):
    items = ItemSerializer(many=True, required=False)
    split_payments = SplitPaymentSerializer(many=True, required=False)
    customer_info = CustomerInfoSerializer(required=False)

    class Meta:
        model = PaymentIntent
        fields = [
            'amount', 'currency', 'payment_intent_unique_id', 'payment_link_unique_id',
            'methods', 'return_url', 'expire_in', 'callback_url',
            'commission_paid_by_customer', 'items', 'split_payments', 'customer_info',
            'status', 'fenanpay_client_secret', 'fenanpay_payment_url'
        ]

    def validate_currency(self, value):
        if value not in ['ETB', 'USD']:
            raise serializers.ValidationError("Currency must be ETB or USD.")
        return value

    def validate_methods(self, value):
        valid_methods = ['TELE_BIRR', 'TELE_BIRR_USSD', 'CBE', 'ETS_SWITCH', 'M_PESA']
        if not value:
            return valid_methods
        for method in value:
            if method not in valid_methods:
                raise serializers.ValidationError(f"Invalid payment method: {method}")
        return value

    def validate(self, data):
        if 'items' in data:
            total_items = sum(item['amount'] * item['quantity'] for item in data['items'])
            if total_items < 1.00:
                raise serializers.ValidationError("Total items amount must be at least 1.00.")
            if total_items != data['amount']:
                raise serializers.ValidationError("Total items amount must equal payment amount.")
        return data

    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        split_payments_data = validated_data.pop('split_payments', [])
        customer_info_data = validated_data.pop('customer_info', None)

        payment_intent = PaymentIntent.objects.create(**validated_data)

        for item_data in items_data:
            Item.objects.create(payment_intent=payment_intent, **item_data)
        for split_data in split_payments_data:
            SplitPayment.objects.create(payment_intent=payment_intent, **split_data)
        if customer_info_data:
            CustomerInfo.objects.create(payment_intent=payment_intent, **customer_info_data)

        return payment_intent

