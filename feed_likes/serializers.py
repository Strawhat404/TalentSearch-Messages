from rest_framework import serializers
from .models import FeedLike
from feed_posts.models import FeedPost

class FeedLikeSerializer(serializers.ModelSerializer):
    # For reading (in responses)
    post_id = serializers.UUIDField(source='post.id', read_only=True)
    user_id = serializers.UUIDField(source='user.id', read_only=True)
    
    # For writing (in requests)
    post = serializers.UUIDField(write_only=True)

    class Meta:
        model = FeedLike
        fields = ['id', 'post', 'post_id', 'user_id', 'created_at']
        read_only_fields = ['id', 'post_id', 'user_id', 'created_at']

    def validate_post(self, value):
        try:
            FeedPost.objects.get(id=value)
            return value
        except FeedPost.DoesNotExist:
            raise serializers.ValidationError('Post does not exist')

    def create(self, validated_data):
        post_id = validated_data.pop('post')
        user = self.context['request'].user
        
        # Get or create like
        like, created = FeedLike.objects.get_or_create(
            post_id=post_id,
            user=user,
            defaults={'post_id': post_id, 'user': user}
        )
        
        if not created:
            raise serializers.ValidationError({'post': 'You have already liked this post'})
            
        return like

    def to_representation(self, instance):
        """Custom representation to ensure consistent field names"""
        ret = super().to_representation(instance)
        # Ensure post_id is always present in the response
        ret['post_id'] = str(instance.post.id)
        ret['user_id'] = str(instance.user.id)
        return ret
