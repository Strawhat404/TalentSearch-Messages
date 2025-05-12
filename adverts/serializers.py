from rest_framework import serializers
from .models import Advert
from django.core.validators import FileExtensionValidator, MinValueValidator, MaxValueValidator
from django.utils import timezone
from drf_spectacular.utils import extend_schema_field
from drf_spectacular.types import OpenApiTypes

class AdvertSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField(read_only=True)
    
    image = serializers.ImageField(
        required=False,
        help_text="Image file for the advert (JPG, PNG, GIF)",
        error_messages={
            'invalid_image': 'Please upload a valid image file (JPG, PNG, GIF)'
        }
    )
    
    video = serializers.FileField(
        required=False,
        validators=[
            FileExtensionValidator(
                allowed_extensions=['mp4', 'mov', 'avi'],
                message='Only MP4, MOV, and AVI video formats are supported'
            )
        ],
        help_text="Video file for the advert (MP4, MOV, AVI)",
        error_messages={
            'invalid': 'Please upload a valid video file'
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

    def validate(self, data):
        """
        Validate the advertisement data
        """
        # Validate run dates if provided
        run_from = data.get('run_from')
        run_to = data.get('run_to')

        if run_from and run_to and run_from >= run_to:
            raise serializers.ValidationError({
                'run_to': 'End date must be after start date'
            })

        if run_from and run_from < timezone.now():
            raise serializers.ValidationError({
                'run_from': 'Start date cannot be in the past'
            })

        return data

    class Meta:
        model = Advert
        fields = [
            'id', 'image', 'title', 'video', 'created_at', 'description',
            'created_by', 'updated_at', 'status', 'location', 'run_from', 'run_to'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']
