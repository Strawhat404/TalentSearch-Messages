from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from .models import Notification  # Adjust the import path based on your project structure
import re
from django.core.exceptions import ValidationError
import bleach
from django.utils.html import strip_tags


User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration with enhanced validation.
    """
    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'password']
        extra_kwargs = {
            'password': {'write_only': True},
            'name': {'min_length': 2, 'max_length': 255},
            'email': {'required': True}
        }

    def to_internal_value(self, data):
        # Check for admin privilege fields in the raw input
        if 'is_staff' in data or 'is_superuser' in data:
            raise serializers.ValidationError({
                'error': 'Admin privileges cannot be modified through this endpoint.'
            })
        return super().to_internal_value(data)

    def validate(self, attrs):
        # Remove any admin privilege fields from the data (defensive)
        attrs.pop('is_staff', None)
        attrs.pop('is_superuser', None)
        return attrs

    def validate_password(self, value):
        """
        Validate password complexity:
        - Minimum 8 characters
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one number
        - At least one special character
        """
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long.")
        
        if not re.search(r'[A-Z]', value):
            raise serializers.ValidationError("Password must contain at least one uppercase letter.")
        
        if not re.search(r'[a-z]', value):
            raise serializers.ValidationError("Password must contain at least one lowercase letter.")
        
        if not re.search(r'\d', value):
            raise serializers.ValidationError("Password must contain at least one number.")
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', value):
            raise serializers.ValidationError("Password must contain at least one special character.")
        
        return value

    def validate_name(self, value):
        """
        Validate name format:
        - Minimum 2 characters
        - Maximum 255 characters
        - Only letters, spaces, and basic punctuation
        - No numbers or special characters
        """
        if len(value.strip()) < 2:
            raise serializers.ValidationError("Name must be at least 2 characters long.")
        
        if not re.match(r'^[A-Za-z\s\-\'\.]+$', value):
            raise serializers.ValidationError("Name can only contain letters, spaces, hyphens, apostrophes, and periods.")
        
        return value.strip()

    def create(self, validated_data):
        # Ensure new users are created with non-admin privileges
        validated_data['is_staff'] = False
        validated_data['is_superuser'] = False
        user = User.objects.create_user(**validated_data)
        return user

    def update(self, instance, validated_data):
        # Prevent updating admin privileges
        validated_data.pop('is_staff', None)
        validated_data.pop('is_superuser', None)
        return super().update(instance, validated_data)


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
    Serializer for notifications with sanitization and validation.
    """
    class Meta:
        model = Notification
        fields = ['id', 'title', 'message', 'notification_type', 'read', 'link', 'created_at']
        read_only_fields = ['id', 'created_at']
        extra_kwargs = {
            'title': {'required': True},
            'message': {'required': True},
            'notification_type': {'required': True},
        }

    def validate_title(self, value):
        """
        Validate and sanitize the title field.
        """
        if not value or not value.strip():
            raise serializers.ValidationError("Title cannot be empty")
        
        # Strip HTML tags and sanitize
        cleaned_title = bleach.clean(
            strip_tags(value),
            strip=True,
            tags=[],  # No HTML tags allowed
            attributes={},
            protocols=[]
        )
        
        if len(cleaned_title) > Notification.MAX_TITLE_LENGTH:
            raise serializers.ValidationError(f"Title must be no more than {Notification.MAX_TITLE_LENGTH} characters")
        
        return cleaned_title

    def validate_message(self, value):
        """
        Validate and sanitize the message field.
        """
        if not value or not value.strip():
            raise serializers.ValidationError("Message cannot be empty")
        
        # Strip HTML tags and sanitize
        cleaned_message = bleach.clean(
            strip_tags(value),
            strip=True,
            tags=[],  # No HTML tags allowed
            attributes={},
            protocols=[]
        )
        
        if len(cleaned_message) > Notification.MAX_MESSAGE_LENGTH:
            raise serializers.ValidationError(f"Message must be no more than {Notification.MAX_MESSAGE_LENGTH} characters")
        
        return cleaned_message

    def validate_link(self, value):
        """
        Validate the link field if provided.
        """
        if value and len(value) > 500:
            raise serializers.ValidationError("Link must be no more than 500 characters")
        return value

    def validate(self, attrs):
        """
        Additional validation for the entire notification.
        """
        # Ensure notification_type is valid
        if attrs.get('notification_type') not in dict(Notification.NOTIFICATION_TYPES):
            raise serializers.ValidationError({
                'notification_type': 'Invalid notification type'
            })
        
        return attrs


class PasswordChangeSerializer(serializers.Serializer):
    """
    Serializer for password change endpoint with enhanced validation.
    """
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

    def validate_new_password(self, value):
        """
        Validate password complexity:
        - Minimum 8 characters
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one number
        - At least one special character
        """
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long.")
        
        if not re.search(r'[A-Z]', value):
            raise serializers.ValidationError("Password must contain at least one uppercase letter.")
        
        if not re.search(r'[a-z]', value):
            raise serializers.ValidationError("Password must contain at least one lowercase letter.")
        
        if not re.search(r'\d', value):
            raise serializers.ValidationError("Password must contain at least one number.")
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', value):
            raise serializers.ValidationError("Password must contain at least one special character.")
        
        return value

    def validate(self, data):
        """
        Validate that old and new passwords are different.
        """
        if data['old_password'] == data['new_password']:
            raise serializers.ValidationError("New password must be different from the old password.")
        return data
