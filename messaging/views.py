from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import Message, MessageThread
from .serializers import MessageSerializer, MessageThreadSerializer
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from django.db.models import Q
from django.core.cache import cache
from rest_framework.throttling import UserRateThrottle

class MessageThreadThrottle(UserRateThrottle):
    rate = '10/minute'

class MessageThreadView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [MessageThreadThrottle]

    @extend_schema(
        tags=['messages'],
        summary='List message threads',
        description='Get all message threads for the current user',
        responses={
            200: MessageThreadSerializer(many=True),
            401: OpenApiTypes.OBJECT,
        }
    )
    def get(self, request):
        """Get all threads where the user is a participant"""
        threads = MessageThread.objects.filter(
            participants=request.user,
            is_active=True
        ).prefetch_related('participants', 'messages')
        
        serializer = MessageThreadSerializer(
            threads,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data)

    @extend_schema(
        tags=['messages'],
        summary='Create message thread',
        description='Create a new message thread with participants',
        request=MessageThreadSerializer,
        responses={
            201: MessageThreadSerializer,
            400: OpenApiTypes.OBJECT,
            401: OpenApiTypes.OBJECT,
        }
    )
    def post(self, request):
        """Create a new message thread"""
        serializer = MessageThreadSerializer(
            data=request.data,
            context={'request': request}
        )
        if serializer.is_valid():
            thread = serializer.save()
            return Response(
                MessageThreadSerializer(thread, context={'request': request}).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class MessageThreadDetailView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [MessageThreadThrottle]

    def get_object(self, thread_id):
        try:
            return MessageThread.objects.get(
                id=thread_id,
                participants=self.request.user,
                is_active=True
            )
        except MessageThread.DoesNotExist:
            return None

    @extend_schema(
        tags=['messages'],
        summary='Get thread details',
        description='Get details of a specific message thread',
        responses={
            200: MessageThreadSerializer,
            404: OpenApiTypes.OBJECT,
        }
    )
    def get(self, request, thread_id):
        """Get thread details and mark messages as read"""
        thread = self.get_object(thread_id)
        if not thread:
            return Response(
                {"detail": "Thread not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Mark messages as read
        thread.mark_as_read(request.user)
        
        serializer = MessageThreadSerializer(
            thread,
            context={'request': request}
        )
        return Response(serializer.data)

    @extend_schema(
        tags=['messages'],
        summary='Update thread',
        description='Update thread details (e.g., title)',
        request=MessageThreadSerializer,
        responses={
            200: MessageThreadSerializer,
            400: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
        }
    )
    def put(self, request, thread_id):
        """Update thread details"""
        thread = self.get_object(thread_id)
        if not thread:
            return Response(
                {"detail": "Thread not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = MessageThreadSerializer(
            thread,
            data=request.data,
            partial=True,
            context={'request': request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=['messages'],
        summary='Delete thread',
        description='Soft delete a message thread',
        responses={
            204: None,
            404: OpenApiTypes.OBJECT,
        }
    )
    def delete(self, request, thread_id):
        """Soft delete a thread"""
        thread = self.get_object(thread_id)
        if not thread:
            return Response(
                {"detail": "Thread not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        thread.is_active = False
        thread.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

class MessageView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [MessageThreadThrottle]

    @extend_schema(
        tags=['messages'],
        summary='List messages',
        description='Get messages from a specific thread',
        parameters=[
            OpenApiParameter(
                name='thread_id',
                type=int,
                location=OpenApiParameter.QUERY,
                description='Thread ID to get messages from'
            )
        ],
        responses={
            200: MessageSerializer(many=True),
            400: OpenApiTypes.OBJECT,
        }
    )
    def get(self, request):
        """Get messages from a specific thread"""
        thread_id = request.query_params.get('thread_id')
        if not thread_id:
            return Response(
                {"detail": "thread_id parameter is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            thread = MessageThread.objects.get(
                id=thread_id,
                participants=request.user,
                is_active=True
            )
        except MessageThread.DoesNotExist:
            return Response(
                {"detail": "Thread not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        messages = thread.messages.all()
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)

    @extend_schema(
        tags=['messages'],
        summary='Create message',
        description='Create a new message in a thread',
        request=MessageSerializer,
        responses={
            201: MessageSerializer,
            400: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
        }
    )
    def post(self, request):
        """Create a new message in a thread"""
        # Check if message queue is full
        if cache.get('message_queue_full'):
            return Response(
                {"detail": "Message queue is full. Please try again later."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        serializer = MessageSerializer(data=request.data)
        if serializer.is_valid():
            try:
                message = serializer.save()
                return Response(
                    MessageSerializer(message).data,
                    status=status.HTTP_201_CREATED
                )
            except Exception as e:
                return Response(
                    {"detail": str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)