from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from .models import Notification  # Adjust the import path based on your project structure


User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    """
    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user


class LoginSerializer(serializers.Serializer):
    """
    Serializer for login functionality (using email).
    """
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class AdminLoginSerializer(serializers.Serializer):
    """
    Serializer for admin login functionality.
    """
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class TokenSerializer(serializers.ModelSerializer):
    """
    Serializer for JWT Token.
    """
    token = serializers.CharField()
    user = UserSerializer()

    class Meta:
        model = Token
        fields = ['token', 'user']


class NotificationSerializer(serializers.ModelSerializer):
    """
    Serializer for notifications.
    """
    class Meta:
        model = Notification
        fields = ['id', 'message', 'created_at']
