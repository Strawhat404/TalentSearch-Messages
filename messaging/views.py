from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Message
from .serializers import MessageSerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

class MessageView(APIView):
    throttle_classes = []

    @swagger_auto_schema(
        operation_summary='List messages',
        operation_description='Get all messages',
        responses={
            200: MessageSerializer(many=True),
        }
    )
    def get(self, request):
        sender_id = request.query_params.get('sender_id', None)
        receiver_id = request.query_params.get('receiver_id', None)
        messages = Message.objects.all()
        if sender_id:
            messages = messages.filter(sender_id=sender_id)
        if receiver_id:
            messages = messages.filter(receiver_id=receiver_id)
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_summary='Create message',
        operation_description='Create a new message',
        request_body=MessageSerializer,
        responses={
            201: openapi.Response(
                description="Message sent successfully.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'id': openapi.Schema(type=openapi.TYPE_STRING, example='uuid'),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, example='Message sent successfully.')
                    }
                )
            ),
            400: openapi.Response(description="Validation Error")
        }
    )
    def post(self, request):
        serializer = MessageSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "id": serializer.data['id'],
                "message": "Message sent successfully."
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)