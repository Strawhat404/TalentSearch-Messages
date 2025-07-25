# feed/serializers.py

from rest_framework import serializers
from .models import FeedPost, FeedLike, Follow, Comment, CommentLike
from userprofile.serializers import ProfileSerializer
from userprofile.models import Profile

class FeedPostSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)
    likes_count = serializers.SerializerMethodField()
    user_has_liked = serializers.SerializerMethodField()

    class Meta:
        model = FeedPost
        fields = [
            'id', 'profile', 'content', 'media_type', 'media',
            'project_title', 'project_type', 'location', 'created_at',
            'likes_count', 'user_has_liked'
        ]
        read_only_fields = ['id', 'profile', 'created_at', 'likes_count', 'user_has_liked']

    def get_likes_count(self, obj):
        return obj.likes.count()

    def get_user_has_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                return obj.likes.filter(profile=request.user.profile).exists()
            except:
                return False
        return False

class FeedProfileSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)
    follower_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = [
            'id', 'profile',
            'follower_count', 'following_count'
        ]

    def get_follower_count(self, obj):
        return obj.followers.count()

    def get_following_count(self, obj):
        return obj.following.count()

class FeedLikeSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)

    class Meta:
        model = FeedLike
        fields = ['id', 'profile', 'post', 'created_at']
        read_only_fields = ['id', 'profile', 'post', 'created_at']

class FollowSerializer(serializers.ModelSerializer):
    follower = ProfileSerializer(read_only=True)
    following = ProfileSerializer(read_only=True)

    class Meta:
        model = Follow
        fields = ['id', 'follower', 'following', 'created_at']
        read_only_fields = ['id', 'follower', 'following', 'created_at']

class ProfileMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile  # or your profile model
        fields = ['id', 'name', 'headshot']  # Add only what you need

class ProfileIdSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile  # or your profile model
        fields = ['id']

class CommentReplySerializer(serializers.ModelSerializer):
    profile_id = serializers.IntegerField(source='profile.id', read_only=True)
    profile_name = serializers.CharField(source='profile.name', read_only=True)
    likes_count = serializers.SerializerMethodField()
    user_has_liked = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = [
            'id', 'content', 'created_at', 'profile_id', 'profile_name',
            'parent', 'post', 'likes_count', 'user_has_liked'
        ]

    def get_likes_count(self, obj):
        return obj.likes.count()

    def get_user_has_liked(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            return obj.likes.filter(profile=user.profile).exists()
        return False

class CommentSerializer(serializers.ModelSerializer):
    profile_id = serializers.IntegerField(source='profile.id', read_only=True)
    profile_name = serializers.CharField(source='profile.name', read_only=True)
    replies = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()
    user_has_liked = serializers.SerializerMethodField()
    replies_count = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = [
            'id', 'content', 'created_at', 'profile_id', 'profile_name',
            'parent', 'post', 'likes_count', 'user_has_liked', 'replies_count', 'replies'
        ]
        read_only_fields = [
            'id', 'created_at', 'profile_id', 'profile_name',
            'likes_count', 'user_has_liked', 'replies_count', 'replies'
        ]

    def get_likes_count(self, obj):
        return obj.likes.count()

    def get_user_has_liked(self, obj):
        user = self.context['request'].user
        return obj.likes.filter(profile=user.profile).exists()

    def get_replies_count(self, obj):
        return obj.replies.count()

    def get_replies(self, obj):
        replies_qs = obj.replies.all()[:2]  # or whatever limit you want
        return CommentReplySerializer(replies_qs, many=True, context=self.context).data

class CommentLikeSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)

    class Meta:
        model = CommentLike
        fields = ['id', 'comment', 'profile', 'is_like', 'created_at']
        read_only_fields = ['id', 'profile', 'created_at']

class CommentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ['id', 'content', 'created_at', 'profile', 'parent', 'post']
        read_only_fields = ['id', 'created_at', 'profile', 'post']
        extra_kwargs = {
            'parent': {'required': False}
        }

    def validate_parent(self, value):
        if value and value.parent is not None:
            raise serializers.ValidationError("Cannot reply to a reply")
        return value

class ReplyCreateSerializer(serializers.ModelSerializer):
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

class CommentReplyMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment  # or your comment model
        fields = ['id', 'content']
