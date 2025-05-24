from rest_framework import serializers
from .models import Message
from django.contrib.auth import get_user_model
from django.core.validators import MinLengthValidator, MaxLengthValidator
from django.utils.html import strip_tags
import bleach

User = get_user_model()

class MessageSerializer(serializers.ModelSerializer):
    sender_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(is_active=True),
        source='sender'
    )
    receiver_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(is_active=True),
        source='receiver'
    )
    message = serializers.CharField(
        validators=[
            MinLengthValidator(1, message="Message cannot be empty"),
            MaxLengthValidator(5000, message="Message cannot exceed 5000 characters")
        ]
    )

    class Meta:
        model = Message
        fields = ['id', 'sender_id', 'receiver_id', 'message', 'is_read', 'created_at']
        read_only_fields = ['id', 'created_at']

    def validate(self, data):
        """
        Validate that:
        1. Sender and receiver are different users
        2. Both users are active
        3. Clean and sanitize message content
        """
        sender = data.get('sender')
        receiver = data.get('receiver')
        message = data.get('message')

        # Check if sender and receiver are the same
        if sender == receiver:
            raise serializers.ValidationError({
                "receiver_id": "You cannot send messages to yourself"
            })

        # Sanitize message content
        # First strip HTML tags
        clean_message = strip_tags(message)
        # Then sanitize using bleach
        clean_message = bleach.clean(
            clean_message,
            strip=True,
            strip_comments=True,
            tags=[],  # No HTML tags allowed
            attributes={},
            protocols=[]
        )
        
        # Update the message with cleaned content
        data['message'] = clean_message

        return data

    def create(self, validated_data):
        """
        Create a new message with validated data
        """
        return Message.objects.create(**validated_data)