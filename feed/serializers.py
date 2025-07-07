# feed/serializers.py

from rest_framework import serializers
from .models import FeedPost, FeedLike, Follow, Comment, CommentLike
from userprofile.serializers import ProfileSerializer

class FeedPostSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)

    class Meta:
        model = FeedPost
        fields = [
            'id', 'profile', 'content', 'media_type', 'media',
            'project_title', 'project_type', 'location', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'profile', 'created_at', 'updated_at']

class FeedLikeSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)

    class Meta:
        model = FeedLike
        fields = ['id', 'post', 'profile', 'created_at']
        read_only_fields = ['id', 'profile', 'created_at']

class FollowSerializer(serializers.ModelSerializer):
    follower = ProfileSerializer(read_only=True)
    following = ProfileSerializer(read_only=True)

    class Meta:
        model = Follow
        fields = ['id', 'follower', 'following', 'created_at']
        read_only_fields = ['id', 'follower', 'following', 'created_at']

class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = '__all__'

class CommentLikeSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)

    class Meta:
        model = CommentLike
        fields = ['id', 'comment', 'profile', 'is_like', 'created_at']
        read_only_fields = ['id', 'profile', 'created_at']

from rest_framework import serializers
from .models import Comment

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
