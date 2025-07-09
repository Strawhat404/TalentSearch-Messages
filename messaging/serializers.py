from rest_framework import serializers
from .models import Message, MessageThread
from django.contrib.auth import get_user_model
from django.core.validators import MinLengthValidator, MaxLengthValidator
from django.utils.html import strip_tags
import bleach
from userprofile.models import Profile

User = get_user_model()

class ProfileSerializer(serializers.ModelSerializer):
    display_name = serializers.SerializerMethodField()
    user_email = serializers.EmailField(source='user.email', read_only=True)
    
    class Meta:
        model = Profile
        fields = ['id', 'display_name', 'user_email', 'name']
        ref_name = "MessagingProfileSerializer"  # another unique name
    
    def get_display_name(self, obj):
        """Get display name with fallback to email"""
        if hasattr(obj, 'name') and obj.name and obj.name != 'Unknown User':
            return obj.name
        return obj.user.email if obj.user else 'Unknown Profile'

class MessageSerializer(serializers.ModelSerializer):
    sender = ProfileSerializer(read_only=True)
    receiver = ProfileSerializer(read_only=True)
    receiver_id = serializers.PrimaryKeyRelatedField(
        queryset=Profile.objects.filter(availability_status=True),
        source='receiver',
        write_only=True
    )
    thread_id = serializers.PrimaryKeyRelatedField(
        queryset=MessageThread.objects.filter(is_active=True),
        source='thread',
        write_only=True,
        required=False,
        allow_null=True
    )

    class Meta:
        model = Message
        fields = ['id', 'thread_id', 'receiver_id', 'sender', 'receiver', 
                 'message', 'is_read', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at', 'sender', 'receiver']

    def validate(self, data):
        """
        Validate that:
        1. Sender and receiver are different profiles
        2. Both profiles are active
        3. Both profiles are participants in the thread (if thread provided)
        4. Clean and sanitize message content
        """
        # Get sender profile from context (current authenticated user's profile)
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError("User must be authenticated")
        
        # Get the profile of the authenticated user
        try:
            sender_profile = request.user.profile
        except Profile.DoesNotExist:
            raise serializers.ValidationError("User must have a profile to send messages")
        
        receiver = data.get('receiver')
        thread = data.get('thread')
        message = data.get('message')

        # Check if sender and receiver are the same
        if sender_profile == receiver:
            raise serializers.ValidationError({
                "receiver_id": "You cannot send messages to yourself"
            })

        # Validate thread participants (only if thread is explicitly provided)
        if thread:
            # If thread is provided, ensure both profiles are participants
            if sender_profile not in thread.participants.all():
                raise serializers.ValidationError({
                    "thread_id": "You must be a participant in the specified thread to send messages"
                })
            if receiver not in thread.participants.all():
                raise serializers.ValidationError({
                    "receiver_id": "The receiver must be a participant in the specified thread"
                })
        # If no thread provided, auto-creation will handle participant validation

        # Sanitize message content
        if message:
            # First strip HTML tags
            clean_message = strip_tags(message)
            # Then sanitize using bleach
            data['message'] = bleach.clean(
                clean_message,
                strip=True,
                strip_comments=True,
                tags=[],  # No HTML tags allowed
                attributes={},
                protocols=[]
            )

        return data

class MessageThreadSerializer(serializers.ModelSerializer):
    participants = ProfileSerializer(many=True, read_only=True)
    participant_ids = serializers.PrimaryKeyRelatedField(
        queryset=Profile.objects.filter(availability_status=True),
        many=True,
        source='participants',
        write_only=True
    )
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = MessageThread
        fields = ['id', 'title', 'participants', 'participant_ids', 
                 'last_message', 'unread_count', 'created_at', 'updated_at', 'is_active']
        read_only_fields = ['id', 'created_at', 'updated_at', 'participants']

    def get_last_message(self, obj):
        """Get the last message in the thread with optimized queries"""
        # Use optimized query to prevent N+1 problems
        last_message = obj.messages.select_related('sender', 'receiver').order_by('-created_at').first()
        if last_message:
            return MessageSerializer(last_message).data
        return None

    def get_unread_count(self, obj):
        """Get the number of unread messages for the current user's profile"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                user_profile = request.user.profile
            except Profile.DoesNotExist:
                return 0
            
            # Count unread messages where user's profile is the receiver
            unread_received = obj.messages.filter(receiver=user_profile, is_read=False).count()
            
            # For group conversations, also consider messages sent by others that user hasn't seen
            # This provides a more comprehensive unread count
            unread_others = obj.messages.filter(
                sender__in=obj.participants.all(),
                receiver__in=obj.participants.all()
            ).exclude(
                sender=user_profile
            ).filter(is_read=False).count()
            
            # Return the higher count to ensure user sees all unread activity
            return max(unread_received, unread_others)
        return 0

    def validate(self, data):
        """
        Validate that:
        1. Thread has at least 2 participants
        2. All participants are active profiles
        """
        participants = data.get('participants', [])
        if len(participants) < 2:
            raise serializers.ValidationError({
                "participant_ids": "Thread must have at least 2 participants"
            })
        return data