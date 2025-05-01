from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Message
from .serializers import MessageSerializer
from talentsearch.throttles import CreateRateThrottle

class SendMessageView(APIView):
    throttle_classes = [CreateRateThrottle]
    def post(self, request):
        serializer = MessageSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "id": serializer.data['id'],
                "message": "Message sent successfully."
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class FetchMessagesView(APIView):
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