from rest_framework import serializers
from .models import Message, MessageThread
from django.contrib.auth import get_user_model
from django.core.validators import MinLengthValidator, MaxLengthValidator
from django.utils.html import strip_tags
import bleach

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'name', 'email']

class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    receiver = UserSerializer(read_only=True)
    sender_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(is_active=True),
        source='sender',
        write_only=True
    )
    receiver_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(is_active=True),
        source='receiver',
        write_only=True
    )
    thread_id = serializers.PrimaryKeyRelatedField(
        queryset=MessageThread.objects.filter(is_active=True),
        source='thread',
        write_only=True
    )

    class Meta:
        model = Message
        fields = ['id', 'thread_id', 'sender_id', 'receiver_id', 'sender', 'receiver', 
                 'message', 'is_read', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at', 'sender', 'receiver']

    def validate(self, data):
        """
        Validate that:
        1. Sender and receiver are different users
        2. Both users are active
        3. Both users are participants in the thread
        4. Clean and sanitize message content
        """
        sender = data.get('sender')
        receiver = data.get('receiver')
        thread = data.get('thread')
        message = data.get('message')

        # Check if sender and receiver are the same
        if sender == receiver:
            raise serializers.ValidationError({
                "receiver_id": "You cannot send messages to yourself"
            })

        # Check if both users are participants in the thread
        if thread:
            if sender not in thread.participants.all():
                raise serializers.ValidationError({
                    "sender_id": "Sender must be a participant in the thread"
                })
            if receiver not in thread.participants.all():
                raise serializers.ValidationError({
                    "receiver_id": "Receiver must be a participant in the thread"
                })

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
    participants = UserSerializer(many=True, read_only=True)
    participant_ids = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(is_active=True),
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
        """Get the last message in the thread"""
        last_message = obj.get_last_message()
        if last_message:
            return MessageSerializer(last_message).data
        return None

    def get_unread_count(self, obj):
        """Get the number of unread messages for the current user"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.messages.filter(receiver=request.user, is_read=False).count()
        return 0

    def validate(self, data):
        """
        Validate that:
        1. Thread has at least 2 participants
        2. All participants are active users
        """
        participants = data.get('participants', [])
        if len(participants) < 2:
            raise serializers.ValidationError({
                "participant_ids": "Thread must have at least 2 participants"
            })
        return data