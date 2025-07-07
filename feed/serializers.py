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
