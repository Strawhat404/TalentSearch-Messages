from rest_framework import serializers
from .models import Advert
from django.core.validators import FileExtensionValidator, MinValueValidator, MaxValueValidator
from django.utils import timezone
from drf_spectacular.utils import extend_schema_field
from drf_spectacular.types import OpenApiTypes
import os
import logging
import bleach
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)

# Constants for file size limits (in bytes)
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB
MAX_VIDEO_SIZE = 100 * 1024 * 1024  # 100MB

# Allowed HTML tags and attributes for content sanitization
ALLOWED_TAGS = ['p', 'br', 'strong', 'em', 'ul', 'ol', 'li', 'a']
ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title', 'target'],
}

class AdvertSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField(read_only=True)
    
    image = serializers.ImageField(
        allow_null=True,
        required=False,
        help_text="Image file for the advert (JPG, PNG, GIF, max 5MB)",
        error_messages={
            'invalid_image': 'Please upload a valid image file (JPG, PNG, GIF)',
            'max_size': 'Image file size must not exceed 5MB'
        }
    )
    
    video = serializers.FileField(
        allow_null=True,
        required=False,
        validators=[
            FileExtensionValidator(
                allowed_extensions=['mp4', 'mov', 'avi'],
                message='Only MP4, MOV, and AVI video formats are supported'
            )
        ],
        help_text="Video file for the advert (MP4, MOV, AVI, max 100MB)",
        error_messages={
            'invalid': 'Please upload a valid video file',
            'max_size': 'Video file size must not exceed 100MB'
        }
    )

    title = serializers.CharField(
        max_length=200,
        help_text="Title of the advertisement",
        error_messages={
            'blank': 'Title cannot be empty',
            'max_length': 'Title cannot be longer than 200 characters'
        }
    )

    description = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Detailed description of the advertisement"
    )

    status = serializers.ChoiceField(
        choices=Advert.STATUS_CHOICES,
        default='draft',
        help_text="Current status of the advertisement"
    )

    location = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=200,
        help_text="Location or region for the advertisement"
    )

    run_from = serializers.DateTimeField(
        required=False,
        help_text="Start date and time for the advertisement campaign"
    )

    run_to = serializers.DateTimeField(
        required=False,
        help_text="End date and time for the advertisement campaign"
    )

    @extend_schema_field(OpenApiTypes.OBJECT)
    def get_created_by(self, obj):
        return {
            'id': obj.created_by.id,
            'username': obj.created_by.username
        }

    def validate_image(self, value):
        if value and value.size > MAX_IMAGE_SIZE:
            raise serializers.ValidationError(
                f'Image file size must not exceed {MAX_IMAGE_SIZE/1024/1024}MB'
            )
        return value

    def validate_video(self, value):
        if value and value.size > MAX_VIDEO_SIZE:
            raise serializers.ValidationError(
                f'Video file size must not exceed {MAX_VIDEO_SIZE/1024/1024}MB'
            )
        return value

    def validate_title(self, value):
        # Sanitize title
        cleaned_title = bleach.clean(
            value,
            tags=[],  # No HTML tags allowed in title
            attributes={},
            strip=True
        )
        if not cleaned_title.strip():
            raise serializers.ValidationError('Title cannot be empty after sanitization')
        return cleaned_title

    def validate_description(self, value):
        if value:
            # Sanitize description with allowed HTML tags
            cleaned_description = bleach.clean(
                value,
                tags=ALLOWED_TAGS,
                attributes=ALLOWED_ATTRIBUTES,
                strip=True
            )
            return cleaned_description
        return value

    def validate_status(self, value):
        if self.instance:  # Only check transitions for existing adverts
            old_status = self.instance.status
            valid_transitions = {
                'draft': ['published', 'archived'],
                'published': ['archived', 'expired'],
                'archived': ['expired'],
                'expired': []  # No valid transitions from expired
            }
            if value not in valid_transitions.get(old_status, []):
                raise serializers.ValidationError(
                    f'Cannot transition from {old_status} to {value}. '
                    f'Valid transitions from {old_status} are: {", ".join(valid_transitions[old_status])}'
                )
        return value

    def validate(self, data):
        """
        Validate the advertisement data
        """
        # Validate run dates if provided
        run_from = data.get('run_from')
        run_to = data.get('run_to')

        if run_from and run_to:
            if run_from >= run_to:
                raise serializers.ValidationError({
                    'run_to': 'End date must be after start date'
                })
            
            # Ensure campaign duration is not too long (e.g., max 1 year)
            max_duration = timezone.timedelta(days=365)
            if run_to - run_from > max_duration:
                raise serializers.ValidationError({
                    'run_to': 'Campaign duration cannot exceed 1 year'
                })

        if run_from and run_from < timezone.now():
            raise serializers.ValidationError({
                'run_from': 'Start date cannot be in the past'
            })

        # Validate that published adverts have required fields
        if data.get('status') == 'published':
            required_fields = ['title', 'run_from', 'run_to']
            missing_fields = [field for field in required_fields if not data.get(field)]
            if missing_fields:
                raise serializers.ValidationError({
                    'status': f'Cannot publish advert without: {", ".join(missing_fields)}'
                })

        return data

    def update(self, instance, validated_data):
        # Handle video field update
        if 'video' in validated_data:
            if validated_data['video'] is None:
                # If video is being set to null, delete the old file
                if instance.video:
                    try:
                        if os.path.isfile(instance.video.path):
                            os.remove(instance.video.path)
                    except Exception as e:
                        logger.error(f"Error deleting old video: {e}")
                instance.video = None
            else:
                # If a new video is being uploaded, delete the old one
                if instance.video:
                    try:
                        if os.path.isfile(instance.video.path):
                            os.remove(instance.video.path)
                    except Exception as e:
                        logger.error(f"Error deleting old video: {e}")
                instance.video = validated_data['video']

        # Update other fields
        for attr, value in validated_data.items():
            if attr != 'video':  # Skip video as we handled it above
                setattr(instance, attr, value)
        
        instance.save()
        return instance

    class Meta:
        model = Advert
        fields = [
            'id', 'image', 'title', 'video', 'created_at', 'description',
            'created_by', 'updated_at', 'status', 'location', 'run_from', 'run_to'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']
