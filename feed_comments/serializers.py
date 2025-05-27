from rest_framework import serializers
from .models import Comment, CommentLike
from userprofile.serializers import ProfileSerializer

class CommentLikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommentLike
        fields = ['id', 'comment', 'user', 'is_like', 'created_at']
        read_only_fields = ['id', 'created_at']

class CommentSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(source='user.profile', read_only=True)
    replies = serializers.SerializerMethodField()
    user_has_liked = serializers.SerializerMethodField()
    user_has_disliked = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = [
            'id', 'post', 'user', 'content', 'parent',
            'created_at', 'updated_at', 'likes_count', 'dislikes_count',
            'profile', 'replies', 'user_has_liked', 'user_has_disliked'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at',
            'likes_count', 'dislikes_count', 'profile',
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
            return obj.likes.filter(user=request.user, is_like=True).exists()
        return False

    def get_user_has_disliked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.likes.filter(user=request.user, is_like=False).exists()
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
