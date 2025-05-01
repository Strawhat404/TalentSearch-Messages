from rest_framework import serializers
from .models import Message
from django.contrib.auth import get_user_model

User = get_user_model()

class MessageSerializer(serializers.ModelSerializer):
    sender_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), source='sender')
    receiver_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), source='receiver')

    class Meta:
        model = Message
        fields = ['id', 'sender_id', 'receiver_id', 'message', 'is_read', 'created_at']
        read_only_fields = ['id', 'created_at']