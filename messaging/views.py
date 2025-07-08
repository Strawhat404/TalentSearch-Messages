from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import Message, MessageThread
from .serializers import MessageSerializer, MessageThreadSerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.db.models import Q
from django.core.cache import cache
from rest_framework.throttling import UserRateThrottle
from django.core.exceptions import ValidationError
from userprofile.models import Profile
from authapp.services import notify_new_message  # Import the notification function


class MessageThreadThrottle(UserRateThrottle):
    rate = '10/minute'


class MessageThreadView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [MessageThreadThrottle]

    @swagger_auto_schema(
        tags=['messages'],
        operation_summary='List message threads',
        operation_description='Get all message threads for the current user',
        responses={
            200: MessageThreadSerializer(many=True),
            401: openapi.Response('Unauthorized'),
        }
    )
    def get(self, request):
        """Get all threads where the user's profile is a participant"""
        try:
            user_profile = request.user.profile
        except Profile.DoesNotExist:
            return Response(
                {"detail": "User must have a profile to access messages"},
                status=status.HTTP_400_BAD_REQUEST
            )

        threads = MessageThread.objects.filter(
            participants=user_profile,
            is_active=True
        ).prefetch_related(
            'participants',
            'messages__sender',
            'messages__receiver'
        ).order_by('-updated_at')

        serializer = MessageThreadSerializer(
            threads,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data)

    @swagger_auto_schema(
        tags=['messages'],
        operation_summary='Create message thread',
        operation_description='Create a new message thread with participants',
        request_body=MessageThreadSerializer,
        responses={
            201: MessageThreadSerializer,
            400: openapi.Response('Bad Request'),
            401: openapi.Response('Unauthorized'),
        }
    )
    def post(self, request):
        """Create a new message thread"""
        try:
            user_profile = request.user.profile
        except Profile.DoesNotExist:
            return Response(
                {"detail": "User must have a profile to create threads"},
                status=status.HTTP_400_BAD_REQUEST
            )

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
            user_profile = self.request.user.profile
        except Profile.DoesNotExist:
            return None

        try:
            return MessageThread.objects.get(
                id=thread_id,
                participants=user_profile,
                is_active=True
            )
        except MessageThread.DoesNotExist:
            return None

    @swagger_auto_schema(
        tags=['messages'],
        operation_summary='Get thread details',
        operation_description='Get details of a specific message thread',
        responses={
            200: MessageThreadSerializer,
            404: openapi.Response('Not Found'),
        }
    )
    def get(self, request, thread_id):
        """Get thread details and mark messages as read"""
        try:
            user_profile = request.user.profile
        except Profile.DoesNotExist:
            return Response(
                {"detail": "User must have a profile to access messages"},
                status=status.HTTP_400_BAD_REQUEST
            )

        thread = self.get_object(thread_id)
        if not thread:
            return Response(
                {"detail": "Thread not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Mark messages as read
        thread.mark_as_read(user_profile)

        serializer = MessageThreadSerializer(
            thread,
            context={'request': request}
        )
        return Response(serializer.data)

    @swagger_auto_schema(
        tags=['messages'],
        operation_summary='Update thread',
        operation_description='Update thread details (e.g., title)',
        request_body=MessageThreadSerializer,
        responses={
            200: MessageThreadSerializer,
            400: openapi.Response('Bad Request'),
            404: openapi.Response('Not Found'),
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

    @swagger_auto_schema(
        tags=['messages'],
        operation_summary='Delete thread',
        operation_description='Soft delete a message thread',
        responses={
            204: openapi.Response('No Content'),
            404: openapi.Response('Not Found'),
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

    def find_or_create_thread(self, sender_profile, receiver_profile):
        """
        Find existing thread between two profiles or create a new one
        """
        # Look for existing active thread between these profiles
        existing_thread = MessageThread.objects.filter(
            participants=sender_profile,
            is_active=True
        ).filter(
            participants=receiver_profile,
            is_active=True
        ).first()

        if existing_thread:
            return existing_thread

        # Get display names with fallback to email
        def get_display_name(profile):
            if hasattr(profile, 'name') and profile.name and profile.name != 'Unknown User':
                return profile.name
            return profile.user.email if profile.user else 'Unknown Profile'

        # Create new thread if none exists
        thread = MessageThread.objects.create(
            title=f"Conversation between {get_display_name(sender_profile)} and {get_display_name(receiver_profile)}"
        )
        thread.participants.add(sender_profile, receiver_profile)
        return thread

    @swagger_auto_schema(
        tags=['messages'],
        operation_summary='List messages',
        operation_description='Get all messages for the user or messages from a specific thread',
        manual_parameters=[
            openapi.Parameter(
                name='thread_id',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_INTEGER,
                required=False,
                description='Thread ID to get messages from (optional - if not provided, returns all user messages)'
            ),
            openapi.Parameter(
                name='sender',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_INTEGER,
                required=False,
                description='Filter messages by sender ID'
            ),
            openapi.Parameter(
                name='receiver',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_INTEGER,
                required=False,
                description='Filter messages by receiver ID'
            )
        ],
        responses={
            200: MessageSerializer(many=True),
            400: openapi.Response('Bad Request'),
        }
    )
    def get(self, request):
        """Get messages - either all user messages or from a specific thread"""
        try:
            user_profile = request.user.profile
        except Profile.DoesNotExist:
            return Response(
                {"detail": "User must have a profile to access messages"},
                status=status.HTTP_400_BAD_REQUEST
            )

        thread_id = request.query_params.get('thread_id')
        sender_id = request.query_params.get('sender')
        receiver_id = request.query_params.get('receiver')

        # If thread_id is provided, get messages from that specific thread
        if thread_id:
            try:
                thread = MessageThread.objects.get(
                    id=thread_id,
                    participants=user_profile,
                    is_active=True
                )
            except MessageThread.DoesNotExist:
                return Response(
                    {"detail": "Thread not found"},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Mark messages as read
            thread.mark_as_read(user_profile)

            messages = thread.messages.all().order_by('created_at')
        else:
            # Get all messages where user's profile is sender or receiver
            messages = Message.objects.filter(
                Q(sender=user_profile) | Q(receiver=user_profile)
            ).select_related('sender', 'receiver', 'thread').order_by('-created_at')

            # Apply additional filters if provided
            if sender_id:
                messages = messages.filter(sender_id=sender_id)
            if receiver_id:
                messages = messages.filter(receiver_id=receiver_id)

        serializer = MessageSerializer(messages, many=True, context={'request': request})
        return Response(serializer.data)

    @swagger_auto_schema(
        tags=['messages'],
        operation_summary='Create message',
        operation_description='Create a new message in a thread (thread will be auto-created if needed)',
        request_body=MessageSerializer,
        responses={
            201: MessageSerializer,
            400: openapi.Response('Bad Request'),
            404: openapi.Response('Not Found'),
        }
    )
    def post(self, request):
        """Create a new message"""
        try:
            user_profile = request.user.profile
        except Profile.DoesNotExist:
            return Response(
                {"detail": "User must have a profile to send messages"},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = MessageSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            # Get receiver from validated data
            receiver_profile = serializer.validated_data.get('receiver')

            # Find or create thread
            thread = self.find_or_create_thread(user_profile, receiver_profile)

            # Create message
            message = serializer.save(
                sender=user_profile,
                thread=thread
            )

            # Notify the receiver of the new message
            notify_new_message(user=receiver_profile.user, sender_name=user_profile.name or user_profile.user.email)

            return Response(
                MessageSerializer(message, context={'request': request}).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MessageDetailView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [MessageThreadThrottle]

    def get_object(self, message_id):
        """Get message object, ensuring user's profile has permission to access it"""
        try:
            user_profile = self.request.user.profile
        except Profile.DoesNotExist:
            return None

        try:
            return Message.objects.filter(
                id=message_id
            ).filter(
                Q(sender=user_profile) | Q(receiver=user_profile)
            ).first()
        except Message.DoesNotExist:
            return None

    @swagger_auto_schema(
        tags=['messages'],
        operation_summary='Get message details',
        operation_description='Get details of a specific message',
        responses={
            200: MessageSerializer,
            404: openapi.Response('Not Found'),
        }
    )
    def get(self, request, message_id):
        """Get a specific message"""
        try:
            user_profile = request.user.profile
        except Profile.DoesNotExist:
            return Response(
                {"detail": "User must have a profile to access messages"},
                status=status.HTTP_400_BAD_REQUEST
            )

        message = self.get_object(message_id)
        if not message:
            return Response(
                {"detail": "Message not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = MessageSerializer(message, context={'request': request})
        return Response(serializer.data)

    @swagger_auto_schema(
        tags=['messages'],
        operation_summary='Update message',
        operation_description='Update message content or read status',
        request_body=MessageSerializer,
        responses={
            200: MessageSerializer,
            400: openapi.Response('Bad Request'),
            404: openapi.Response('Not Found'),
        }
    )
    def patch(self, request, message_id):
        """Update a message (only sender can update content)"""
        try:
            user_profile = request.user.profile
        except Profile.DoesNotExist:
            return Response(
                {"detail": "User must have a profile to update messages"},
                status=status.HTTP_400_BAD_REQUEST
            )

        message = self.get_object(message_id)
        if not message:
            return Response(
                {"detail": "Message not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Only sender can update message content
        if 'message' in request.data and message.sender != user_profile:
            return Response(
                {"detail": "Only the sender can update message content"},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = MessageSerializer(
            message,
            data=request.data,
            partial=True,
            context={'request': request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        tags=['messages'],
        operation_summary='Delete message',
        operation_description='Delete a message (only sender can delete)',
        responses={
            204: openapi.Response('No Content'),
            403: openapi.Response('Forbidden'),
            404: openapi.Response('Not Found'),
        }
    )
    def delete(self, request, message_id):
        """Delete a message (only sender can delete)"""
        try:
            user_profile = request.user.profile
        except Profile.DoesNotExist:
            return Response(
                {"detail": "User must have a profile to delete messages"},
                status=status.HTTP_400_BAD_REQUEST
            )

        message = self.get_object(message_id)
        if not message:
            return Response(
                {"detail": "Message not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Only sender can delete message
        if message.sender != user_profile:
            return Response(
                {"detail": "Only the sender can delete the message"},
                status=status.HTTP_403_FORBIDDEN
            )

        message.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

