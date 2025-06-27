import time, requests
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from .serializers import PaymentIntentSerializer
from .models import PaymentIntent
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
import json
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

class PaymentIntentView(APIView):
    @swagger_auto_schema(
        operation_description="Create a new payment intent and send it to FenanPay API",
        operation_summary="Create Payment Intent",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['amount', 'currency', 'payment_intent_unique_id', 'return_url', 'expire_in'],
            properties={
                'amount': openapi.Schema(type=openapi.TYPE_NUMBER, description="Payment amount (minimum 1.00)"),
                'currency': openapi.Schema(type=openapi.TYPE_STRING, enum=['ETB', 'USD'], description="Currency code"),
                'payment_intent_unique_id': openapi.Schema(type=openapi.TYPE_STRING, description="Unique identifier for the payment intent"),
                'payment_link_unique_id': openapi.Schema(type=openapi.TYPE_STRING, description="Optional payment link ID"),
                'methods': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_STRING, enum=['TELE_BIRR', 'TELE_BIRR_USSD', 'CBE', 'ETS_SWITCH', 'M_PESA']),
                    description="Payment methods (defaults to all if empty)"
                ),
                'return_url': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_URI, description="URL to redirect after payment"),
                'expire_in': openapi.Schema(type=openapi.TYPE_INTEGER, minimum=5, description="Expiration time in minutes"),
                'callback_url': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_URI, description="Optional webhook callback URL"),
                'commission_paid_by_customer': openapi.Schema(type=openapi.TYPE_BOOLEAN, default=False, description="Whether customer pays commission"),
                'items': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'name': openapi.Schema(type=openapi.TYPE_STRING, description="Item name"),
                            'amount': openapi.Schema(type=openapi.TYPE_NUMBER, description="Item amount"),
                            'quantity': openapi.Schema(type=openapi.TYPE_INTEGER, minimum=1, description="Item quantity")
                        }
                    ),
                    description="Optional list of items"
                ),
                'split_payments': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'beneficiary_id': openapi.Schema(type=openapi.TYPE_STRING, description="Beneficiary ID"),
                            'amount': openapi.Schema(type=openapi.TYPE_NUMBER, description="Split amount")
                        }
                    ),
                    description="Optional split payment configuration"
                ),
                'customer_info': openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'name': openapi.Schema(type=openapi.TYPE_STRING, description="Customer name"),
                        'email': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_EMAIL, description="Customer email"),
                        'phone': openapi.Schema(type=openapi.TYPE_STRING, description="Customer phone")
                    },
                    description="Optional customer information"
                )
            }
        ),
        responses={
            201: openapi.Response(
                description="Payment intent created successfully",
                schema=PaymentIntentSerializer
            ),
            400: openapi.Response(description="Invalid request data"),
            500: openapi.Response(description="FenanPay API error")
        },
        tags=['Payment']
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

    @swagger_auto_schema(
        operation_description="Retrieve all payment intents",
        operation_summary="Get All Payment Intents",
        responses={
            200: openapi.Response(
                description="Payment intents retrieved successfully",
                schema=PaymentIntentSerializer(many=True)
            )
        },
        tags=['Payment']
    )
    def get(self, request):
        payment_intents = PaymentIntent.objects.all()
        serializer = PaymentIntentSerializer(payment_intents, many=True)
        return Response(serializer.data)

class PaymentIntentDetailView(APIView):
    @swagger_auto_schema(
        operation_description="Retrieve a specific payment intent by unique ID",
        operation_summary="Get Payment Intent by ID",
        manual_parameters=[
            openapi.Parameter(
                'payment_intent_unique_id',
                openapi.IN_PATH,
                description="Payment intent unique ID",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            200: openapi.Response(
                description="Payment intent retrieved successfully",
                schema=PaymentIntentSerializer
            ),
            404: openapi.Response(description="Payment intent not found")
        },
        tags=['Payment']
    )
    def get(self, request, payment_intent_unique_id):
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
                {"error": "Payment intent not found"},
                status=status.HTTP_404_NOT_FOUND
            )

@swagger_auto_schema(
    method='post',
    operation_description="Handle payment webhook callbacks from FenanPay",
    operation_summary="Payment Callback",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'paymentIntentUniqueId': openapi.Schema(type=openapi.TYPE_STRING, description="Payment intent unique ID"),
            'status': openapi.Schema(type=openapi.TYPE_STRING, description="Payment status"),
            'event': openapi.Schema(type=openapi.TYPE_STRING, description="Event type")
        }
    ),
    responses={
        200: openapi.Response(description="Callback processed successfully"),
        400: openapi.Response(description="Invalid callback data"),
        404: openapi.Response(description="Payment intent not found"),
        405: openapi.Response(description="Method not allowed")
    },
    tags=['Payment']
)
@api_view(['POST'])
@csrf_exempt
def payment_callback(request):
    try:
        webhook_data = json.loads(request.body)
        payment_intent_id = webhook_data.get('paymentIntentUniqueId')
        status = webhook_data.get('status')
        event_type = webhook_data.get('event')  # e.g., 'payment_intent.succeeded'

        if not payment_intent_id or not status:
            return Response({"error": "Missing required fields"}, status=status.HTTP_400_BAD_REQUEST)

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

            return Response({"message": "Callback processed successfully"}, status=status.HTTP_200_OK)
        except PaymentIntent.DoesNotExist:
            return Response({"error": "Payment intent not found"}, status=status.HTTP_404_NOT_FOUND)
    except json.JSONDecodeError:
        return Response({"error": "Invalid JSON data"}, status=status.HTTP_400_BAD_REQUEST)
