from rest_framework import serializers
from .models import Message

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['id', 'sender_id', 'receiver_id', 'message', 'created_at', 'is_read']
        read_only_fields = ['id', 'created_at']

    sender_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), source='sender')
    receiver_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), source='receiver')