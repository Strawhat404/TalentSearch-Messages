from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Message
from .serializers import MessageSerializer
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes

class MessageView(APIView):
    throttle_classes = []

    @extend_schema(
        tags=['messages'],
        summary='List or create messages',
        description='Get all messages or create a new message',
        request=MessageSerializer,
        responses={
            200: MessageSerializer(many=True),
            201: MessageSerializer,
            400: OpenApiTypes.OBJECT,
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

    @extend_schema(
        tags=['messages'],
        summary='Create message',
        description='Create a new message',
        request=MessageSerializer,
        responses={
            201: MessageSerializer,
            400: OpenApiTypes.OBJECT,
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