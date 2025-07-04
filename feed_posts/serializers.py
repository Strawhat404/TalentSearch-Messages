from rest_framework import serializers
from .models import FeedPost, UserFollow
from userprofile.models import Profile
from django.core.validators import FileExtensionValidator
import os
import logging
from feed_likes.models import FeedLike
from feed_comments.models import Comment
from feed_comments.serializers import CommentSerializer

logger = logging.getLogger(__name__)

class UserFollowSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserFollow
        fields = ['id', 'follower', 'following', 'created_at']
        read_only_fields = ['id', 'created_at']

class ProfileSerializer(serializers.ModelSerializer):
    photo = serializers.SerializerMethodField()
    experience_level = serializers.SerializerMethodField()
    profession = serializers.SerializerMethodField()
    follower_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Profile
        fields = ['id', 'name', 'photo', 'profession', 'verified', 'experience_level', 'follower_count', 'following_count']
    
    def get_photo(self, obj):
        """Get photo from related Headshot model"""
        try:
            if hasattr(obj, 'headshot') and obj.headshot and obj.headshot.professional_headshot:
                return obj.headshot.professional_headshot.url
            return None
        except Exception as e:
            logger.warning(f"Error getting photo for profile {obj.id}: {e}")
            return None
    
    def get_experience_level(self, obj):
        """Get experience_level from related Experience model"""
        try:
            if hasattr(obj, 'experience') and obj.experience and obj.experience.experience_level:
                return obj.experience.experience_level
            return None
        except Exception as e:
            logger.warning(f"Error getting experience_level for profile {obj.id}: {e}")
            return None
    
    def get_profession(self, obj):
        """Get profession from related ProfessionsAndSkills model"""
        try:
            if hasattr(obj, 'professions_and_skills') and obj.professions_and_skills:
                # Return the first profession from the professions list, or a default value
                professions = obj.professions_and_skills.professions
                if professions and len(professions) > 0:
                    return professions[0]  # Return the first profession
                return None
            return None
        except Exception as e:
            logger.warning(f"Error getting profession for profile {obj.id}: {e}")
            return None

    def get_follower_count(self, obj):
        return UserFollow.objects.filter(following=obj.user).count()

    def get_following_count(self, obj):
        return UserFollow.objects.filter(follower=obj.user).count()

class FeedPostSerializer(serializers.ModelSerializer):
    user_id = serializers.UUIDField(source='user.id', read_only=True)
    profiles = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()
    user_has_liked = serializers.SerializerMethodField()
    replies = serializers.SerializerMethodField()

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
            'likes_count', 'comments_count', 'user_has_liked', 'profiles', 'replies'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'user_id']

    def get_profiles(self, obj):
        try:
            profile = Profile.objects.get(user=obj.user)
            return ProfileSerializer(profile).data
        except Profile.DoesNotExist:
            # Create a basic profile data structure instead of logging a warning
            return {
                'id': None,
                'name': obj.user.name or obj.user.username,
                'photo': None,
                'profession': None,
                'verified': False,
                'experience_level': None,
                'follower_count': 0,
                'following_count': 0
            }

    def get_likes_count(self, obj):
        return obj.likes.count()

    def get_comments_count(self, obj):
        return obj.comments.count()

    def get_user_has_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.likes.filter(user=request.user).exists()
        return False

    def get_replies(self, obj):
        # Only get first level replies
        if obj.parent is None:  # Only get replies for top-level comments
            replies = obj.replies.all()[:5]  # Limit to 5 replies
            return CommentSerializer(replies, many=True).data
        return []

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