# feed/serializers.py

from rest_framework import serializers
from .models import FeedPost, FeedLike, Follow, Comment, CommentLike
from userprofile.serializers import ProfileSerializer
from userprofile.models import Profile
from feed.models import Follow  # or wherever your Follow model is
from rest_framework import serializers
from .models import Comment
from userprofile.serializers import UserSerializer


# class FeedPostSerializer(serializers.ModelSerializer):
#     profile = ProfileSerializer(read_only=True)

#     class Meta:
#         model = FeedPost
#         fields = [
#             'id', 'profile', 'content', 'media_type', 'media',
#             'project_title', 'project_type', 'location', 'created_at', 'updated_at'
#         ]
#         read_only_fields = ['id', 'profile', 'created_at', 'updated_at']



class FeedProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    follower_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = [
            'id', 'user',    # 👈 include the nested user
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

class FeedProfileSerializer(serializers.ModelSerializer):
    follower_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()
    email = serializers.CharField(source='user.email', read_only=True)  # Get email from related User

    class Meta:
        model = Profile
        fields = [
            'id', 'name', 'email',  # email comes from user.email
            'follower_count', 'following_count'
        ]

    def get_follower_count(self, obj):
        return obj.followers.count()

    def get_following_count(self, obj):
        return obj.following.count()

class FollowSerializer(serializers.ModelSerializer):
    follower = FeedProfileSerializer(read_only=True)
    following = FeedProfileSerializer(read_only=True)

    class Meta:
        model = Follow
        fields = ['id', 'follower', 'following', 'created_at']
        read_only_fields = ['id', 'follower', 'following', 'created_at']


class CommentSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)  # shows the user who wrote the comment

    class Meta:
        model = Comment
        fields = [
            'id',
            'content',
            'created_at',
            'profile',
            'parent',
            'post',
        ]
        read_only_fields = ['id', 'created_at', 'profile']


class CommentLikeSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)

    class Meta:
        model = CommentLike
        fields = ['id', 'comment', 'profile', 'is_like', 'created_at']
        read_only_fields = ['id', 'profile', 'created_at']



class CommentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ['content', 'parent']  # Do NOT include 'post'
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
