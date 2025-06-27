from django.urls import path
from .views import PaymentIntentView, PaymentIntentDetailView, payment_callback

urlpatterns = [
    path('intent/', PaymentIntentView.as_view(), name='payment-intent'),
    path('intent/<str:payment_intent_unique_id>/', PaymentIntentDetailView.as_view(), name='payment-intent-detail'),
    path('callback/', payment_callback, name='payment-callback'),
] 