from rest_framework import serializers
from .models import Comment, CommentLike
from userprofile.serializers import ProfileSerializer

class CommentLikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommentLike
        fields = ['id', 'comment', 'profile', 'is_like', 'created_at']
        read_only_fields = ['id', 'created_at']

class CommentSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)
    username = serializers.CharField(source='profile.user.username', read_only=True)
    replies = serializers.SerializerMethodField()
    user_has_liked = serializers.SerializerMethodField()
    user_has_disliked = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = [
            'id', 'post', 'profile', 'content', 'parent',
            'created_at', 'updated_at', 'likes_count', 'dislikes_count',
            'profile', 'username', 'replies', 'user_has_liked', 'user_has_disliked'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at',
            'likes_count', 'dislikes_count', 'profile', 'username',
            'replies', 'user_has_liked', 'user_has_disliked'
        ]

    def get_replies(self, obj):
        # Only get first level replies
        if obj.parent is None:  # Only get replies for top-level comments
            replies = obj.replies.all()[:5]  # Limit to 5 replies
            return CommentSerializer(replies, many=True).data
        return []

    def get_user_has_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            # Get the user's profile
            try:
                user_profile = request.user.profile
                return obj.likes.filter(profile=user_profile, is_like=True).exists()
            except:
                return False
        return False

    def get_user_has_disliked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            # Get the user's profile
            try:
                user_profile = request.user.profile
                return obj.likes.filter(profile=user_profile, is_like=False).exists()
            except:
                return False
        return False

class CommentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ['post', 'content', 'parent']
        extra_kwargs = {
            'parent': {'required': False}
        }

    def validate_parent(self, value):
        if value and value.parent is not None:
            raise serializers.ValidationError("Cannot reply to a reply")
        return value

# 🆕 COOL NEW REPLY SERIALIZERS

class ReplyCreateSerializer(serializers.ModelSerializer):
    """
    🚀 Serializer for creating replies
    Simplified and focused on reply creation
    """
    class Meta:
        model = Comment
        fields = ['content']
        extra_kwargs = {
            'content': {
                'help_text': 'The content of your reply',
                'style': {'placeholder': 'Write your reply here...'}
            }
        }

    def validate_content(self, value):
        if len(value.strip()) < 1:
            raise serializers.ValidationError("Reply content cannot be empty")
        if len(value) > 1000:
            raise serializers.ValidationError("Reply content cannot exceed 1000 characters")
        return value

class ReplySerializer(serializers.ModelSerializer):
    """
    📝 Serializer for reply responses
    Optimized for reply display with user info and engagement metrics
    """
    profile = ProfileSerializer(read_only=True)
    username = serializers.CharField(source='profile.user.username', read_only=True)
    user_has_liked = serializers.SerializerMethodField()
    user_has_disliked = serializers.SerializerMethodField()
    engagement_score = serializers.SerializerMethodField()
    is_reply = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = [
            'id', 'content', 'profile', 'username',
            'created_at', 'updated_at', 'likes_count', 'dislikes_count',
            'user_has_liked', 'user_has_disliked', 'engagement_score', 'is_reply'
        ]
        read_only_fields = [
            'id', 'profile', 'username', 'created_at', 'updated_at',
            'likes_count', 'dislikes_count', 'user_has_liked', 'user_has_disliked',
            'engagement_score', 'is_reply'
        ]

    def get_user_has_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                user_profile = request.user.profile
                return obj.likes.filter(profile=user_profile, is_like=True).exists()
            except:
                return False
        return False

    def get_user_has_disliked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                user_profile = request.user.profile
                return obj.likes.filter(profile=user_profile, is_like=False).exists()
            except:
                return False
        return False

    def get_engagement_score(self, obj):
        """Calculate engagement score based on likes and replies"""
        return obj.likes_count + (obj.replies.count() * 2)

    def get_is_reply(self, obj):
        """Indicate this is a reply"""
        return obj.parent is not None
