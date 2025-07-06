from rest_framework import serializers
from .models import FeedLike
from feed_posts.models import FeedPost

class FeedLikeSerializer(serializers.ModelSerializer):
    # For reading (in responses)
    post_id = serializers.UUIDField(source='post.id', read_only=True)
    profile_id = serializers.IntegerField(source='profile.id', read_only=True)
    
    # For writing (in requests)
    post = serializers.UUIDField(write_only=True)

    class Meta:
        model = FeedLike
        fields = ['id', 'post', 'post_id', 'profile_id', 'created_at']
        read_only_fields = ['id', 'post_id', 'profile_id', 'created_at']

    def validate_post(self, value):
        try:
            FeedPost.objects.get(id=value)
            return value
        except FeedPost.DoesNotExist:
            raise serializers.ValidationError('Post does not exist')

    def create(self, validated_data):
        post_id = validated_data.pop('post')
        
        # Get the user's profile
        try:
            user_profile = self.context['request'].user.profile
        except Exception as e:
            raise serializers.ValidationError(f"User profile not found: {str(e)}")
        
        # Get or create like
        like, created = FeedLike.objects.get_or_create(
            post_id=post_id,
            profile=user_profile,
            defaults={'post_id': post_id, 'profile': user_profile}
        )
        
        if not created:
            raise serializers.ValidationError({'post': 'You have already liked this post'})
            
        return like

    def to_representation(self, instance):
        """Custom representation to ensure consistent field names"""
        ret = super().to_representation(instance)
        # Ensure post_id is always present in the response
        ret['post_id'] = str(instance.post.id)
        ret['profile_id'] = instance.profile.id
        return ret
