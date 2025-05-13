from rest_framework import serializers
from .models import FeedPost
from userprofile.models import Profile
from django.core.validators import FileExtensionValidator
import os
import logging

logger = logging.getLogger(__name__)

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['id', 'name', 'photo_url', 'profession', 'verified', 'experience_level']

class FeedPostSerializer(serializers.ModelSerializer):
    user_id = serializers.UUIDField(source='user.id', read_only=True)
    profiles = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()
    user_has_liked = serializers.SerializerMethodField()

    media_url = serializers.FileField(
        validators=[
            FileExtensionValidator(
                allowed_extensions=['jpg', 'jpeg', 'png', 'gif', 'mp4', 'mov', 'avi'],
                message='Only image (JPG, PNG, GIF) and video (MP4, MOV, AVI) formats are supported'
            )
        ],
        help_text="Upload an image or video file"
    )

    class Meta:
        model = FeedPost
        fields = [
            'id', 'user_id', 'content', 'media_type', 'media_url',
            'project_title', 'project_type', 'location', 'created_at', 'updated_at',
            'likes_count', 'comments_count', 'user_has_liked', 'profiles'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'user_id']

    def get_profiles(self, obj):
        try:
            profile = Profile.objects.get(user=obj.user)
            return ProfileSerializer(profile).data
        except Profile.DoesNotExist:
            return None

    def get_likes_count(self, obj):
        # TODO: Implement likes count
        return 0

    def get_comments_count(self, obj):
        # TODO: Implement comments count
        return 0

    def get_user_has_liked(self, obj):
        # TODO: Implement user has liked check
        return False

    def validate(self, data):
        """
        Validate that the media_type matches the uploaded file
        """
        media_type = data.get('media_type')
        media_url = data.get('media_url')

        if not media_url:
            raise serializers.ValidationError({
                'media_url': 'Media file is required'
            })

        # Check file extension
        ext = os.path.splitext(media_url.name)[1].lower()
        
        if media_type == 'image' and ext not in ['.jpg', '.jpeg', '.png', '.gif']:
            raise serializers.ValidationError({
                'media_url': 'Please upload a valid image file (JPG, PNG, GIF)'
            })
        elif media_type == 'video' and ext not in ['.mp4', '.mov', '.avi']:
            raise serializers.ValidationError({
                'media_url': 'Please upload a valid video file (MP4, MOV, AVI)'
            })

        return data

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['user'] = user
        
        # Set media_url based on media_type
        if validated_data.get('media_type') == 'image':
            validated_data['media_url'] = validated_data.pop('media_url')
        else:
            validated_data['media_url'] = validated_data.pop('media_url')
            
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # Handle file updates
        if 'media_url' in validated_data:
            new_file = validated_data.get('media_url')
            if new_file:
                # Delete old file if it exists
                if instance.media_url:
                    try:
                        if os.path.isfile(instance.media_url.path):
                            os.remove(instance.media_url.path)
                    except Exception as e:
                        logger.error(f"Error deleting old media file: {e}")
                instance.media_url = new_file

        # Update other fields
        for attr, value in validated_data.items():
            if attr not in ['media_url']:  # Skip files as we handled them above
                setattr(instance, attr, value)
        
        instance.save()
        return instance 