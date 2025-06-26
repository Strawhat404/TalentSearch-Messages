import time, requests
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import PaymentIntentSerializer
from .models import PaymentIntent
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
import json
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter

class PaymentIntentView(APIView):
    @extend_schema(
        tags=['Payment'],
        request=PaymentIntentSerializer,
        responses={
            201: PaymentIntentSerializer,
            400: OpenApiResponse(description="Invalid data"),
            500: OpenApiResponse(description="FenanPay API error"),
        },
        summary="Create a Payment Intent",
        description="Creates a new payment intent and sends it to the FenanPay API. Returns client secret and payment URL on success."

    )
    def post(self, request):
        serializer = PaymentIntentSerializer(data=request.data)
        if serializer.is_valid():
            # Save Payment Intent locally
            payment_intent = serializer.save()

            # Prepare data for FenanPay
            fenanpay_data = {
                "amount": str(serializer.validated_data['amount']),
                "currency": serializer.validated_data['currency'],
                "paymentIntentUniqueId": serializer.validated_data['payment_intent_unique_id'],
                "paymentLinkUniqueId": serializer.validated_data.get('payment_link_unique_id', ''),
                "methods": serializer.validated_data['methods'],
                "returnUrl": serializer.validated_data['return_url'],
                "expireIn": serializer.validated_data['expire_in'],
                "callbackUrl": serializer.validated_data.get('callback_url', ''),
                "commissionPaidByCustomer": serializer.validated_data['commission_paid_by_customer'],
                "items": [
                    {"name": item['name'], "amount": str(item['amount']), "quantity": item['quantity']}
                    for item in serializer.validated_data.get('items', [])
                ],
                "splitPayment": [
                    {"beneficiary_id": split['beneficiary_id'], "amount": str(split['amount'])}
                    for split in serializer.validated_data.get('split_payments', [])
                ],
                "customerInfo": serializer.validated_data.get('customer_info', {})
            }

            # Call FenanPay API
            try:
                response = requests.post(
                    f'{settings.FENANPAY_API_URL}/api/v1/payment-intents',
                    json=fenanpay_data,
                    headers={
                        'Authorization': f'Bearer {settings.FENAN_PAY_API_KEY}',
                        'Content-Type': 'application/json',
                        'Idempotency-Key': serializer.validated_data['payment_intent_unique_id']  # Prevent duplicates
                    }
                )
                response.raise_for_status()
                fenanpay_response = response.json()

                # Update PaymentIntent with FenanPay data
                payment_intent.fenanpay_client_secret = fenanpay_response.get('client_secret')
                payment_intent.fenanpay_payment_url = fenanpay_response.get('payment_url')
                payment_intent.status = fenanpay_response.get('status', 'pending')
                payment_intent.save()

                # Return response with FenanPay data
                serializer_data = serializer.data
                serializer_data['fenanpay_client_secret'] = payment_intent.fenanpay_client_secret
                serializer_data['fenanpay_payment_url'] = payment_intent.fenanpay_payment_url
                return Response(serializer_data, status=status.HTTP_201_CREATED)
            except requests.RequestException as e:
                return Response(
                    {"error": f"FenanPay API error: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=['Payment'],
        parameters=[
            OpenApiParameter(
                name='payment_intent_unique_id',
                required=False,
                type=str,
                location=OpenApiParameter.PATH,
                description="Optional Payment Intent Unique ID to fetch a specific intent"
            )
        ],
        responses={
            200: PaymentIntentSerializer(many=True),
            404: OpenApiResponse(description="Payment intent not found")
        },
        summary="Retrieve Payment Intent(s)",
        description="Fetch a single payment intent by unique ID or all intents if no ID is provided."

    )
    def get(self, request, payment_intent_unique_id=None):
        if payment_intent_unique_id:
            try:
                payment_intent = PaymentIntent.objects.get(
                    payment_intent_unique_id=payment_intent_unique_id
                )
                # Optionally check status with FenanPay
                try:
                    response = requests.get(
                        f'{settings.FENANPAY_API_URL}/payment-intents/{payment_intent_unique_id}',
                        headers={'Authorization': f'Bearer {settings.FENANPAY_API_KEY}'}
                    )
                    response.raise_for_status()
                    fenanpay_data = response.json()
                    payment_intent.status = fenanpay_data.get('status', payment_intent.status)
                    payment_intent.save()
                except requests.RequestException as e:
                    # Log error but return local data
                    print(f"FenanPay status check failed: {str(e)}")

                serializer = PaymentIntentSerializer(payment_intent)
                return Response(serializer.data)
            except PaymentIntent.DoesNotExist:
                return Response(
                    {"error": "Payment intent not not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            payment_intents = PaymentIntent.objects.all()
            serializer = PaymentIntentSerializer(payment_intents, many=True)
            return Response(serializer.data)

@csrf_exempt
def payment_callback(request):
    if request.method == 'POST':  
        try:
            webhook_data = json.loads(request.body)
            payment_intent_id = webhook_data.get('paymentIntentUniqueId')
            status = webhook_data.get('status')
            event_type = webhook_data.get('event')  # e.g., 'payment_intent.succeeded'

            if not payment_intent_id or not status:
                return HttpResponse(status=400)

            try:
                payment_intent = PaymentIntent.objects.get(
                    payment_intent_unique_id=payment_intent_id
                )
                payment_intent.status = status
                payment_intent.save()

                # Add business logic (e.g., update order status, send email)
                if status == 'succeeded':
                    # Example: Update order status
                    print(f"Payment {payment_intent_id} succeeded")
                elif status == 'failed':
                    print(f"Payment {payment_intent_id} failed")

                return HttpResponse(status=200)
            except PaymentIntent.DoesNotExist:
                return HttpResponse(status=404)
        except json.JSONDecodeError:
            return HttpResponse(status=400)
    return HttpResponse(status=405)
