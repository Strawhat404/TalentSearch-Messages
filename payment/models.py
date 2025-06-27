from django.db import models
from django.core.validators import MinValueValidator, URLValidator
from django.core.exceptions import ValidationError

class PaymentIntent(models.Model):
    amount = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(1.00)]
    )
    currency = models.CharField(max_length=3, choices=[('ETB', 'ETB'), ('USD', 'USD')])
    payment_intent_unique_id = models.CharField(max_length=100, unique=True)
    payment_link_unique_id = models.CharField(max_length=100, blank=True, null=True)
    methods = models.JSONField(default=list)
    return_url = models.URLField(validators=[URLValidator()])
    expire_in = models.IntegerField(validators=[MinValueValidator(5)])
    callback_url = models.URLField(blank=True, null=True, validators=[URLValidator()])
    commission_paid_by_customer = models.BooleanField(default=False)
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('succeeded', 'Succeeded'),
            ('failed', 'Failed'),
            ('canceled', 'Canceled')
        ],
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    fenanpay_client_secret = models.CharField(max_length=255, blank=True, null=True)  # Store FenanPay’s client secret
    fenanpay_payment_url = models.URLField(blank=True, null=True)  # Store payment URL

    def clean(self):
        items = self.items.all()
        if items:
            total_items_amount = sum(item.amount for item in items)
            if total_items_amount != self.amount:
                raise ValidationError("Total items amount must equal payment intent amount.")

class Item(models.Model):
    payment_intent = models.ForeignKey(
        PaymentIntent, related_name='items', on_delete=models.CASCADE
    )
    name = models.CharField(max_length=255)
    amount = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)]
    )
    quantity = models.IntegerField(validators=[MinValueValidator(1)])

class SplitPayment(models.Model):
    payment_intent = models.ForeignKey(
        PaymentIntent, related_name='split_payments', on_delete=models.CASCADE
    )
    beneficiary_id = models.CharField(max_length=100)
    amount = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)]
    )

class CustomerInfo(models.Model):
    payment_intent = models.OneToOneField(
        PaymentIntent, related_name='customer_info', on_delete=models.CASCADE
    )
    name = models.CharField(max_length=255, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
