from rest_framework import serializers
from .models import Rating
from userprofile.serializers import ProfileSerializer
from rental_items.models import RentalItem

class RatingSerializer(serializers.ModelSerializer):
    user_profile = ProfileSerializer(source='user.profile', read_only=True)
    item_details = serializers.SerializerMethodField()
    rating_stats = serializers.SerializerMethodField()

    class Meta:
        model = Rating
        fields = [
            'id', 'item_id', 'user_id', 'rating', 'comment', 'created_at', 
            'updated_at', 'user_profile', 'item_details', 'rating_stats',
            'is_verified_purchase', 'helpful_votes', 'reported', 'is_edited'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'user_profile', 'item_details', 
            'rating_stats', 'helpful_votes', 'reported'
        ]

    def get_item_details(self, obj):
        try:
            rental_item = RentalItem.objects.get(id=obj.item_id)
            return {
                'id': str(rental_item.id),
                'name': rental_item.name,
                'image': rental_item.image.url if rental_item.image else None,
                'type': rental_item.type,
                'category': rental_item.category,
                'daily_rate': rental_item.daily_rate
            }
        except RentalItem.DoesNotExist:
            return {
                'id': str(obj.item_id),
                'name': 'Item not found',
                'image': None,
                'type': None,
                'category': None,
                'daily_rate': None
            }

    def get_rating_stats(self, obj):
        """Get rating statistics for the item this rating belongs to"""
        return Rating.get_item_rating_stats(obj.item_id)

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['user_id'] = str(instance.user.id)
        return representation

    def validate(self, data):
        user = self.context['request'].user
        item_id = data.get('item_id')
        
        # Check if user already rated this item
        if self.instance is None and Rating.objects.filter(user=user, item_id=item_id).exists():
            raise serializers.ValidationError("You have already rated this item.")
        
        # Validate item exists
        try:
            RentalItem.objects.get(id=item_id)
        except RentalItem.DoesNotExist:
            raise serializers.ValidationError("Rental item does not exist.")
        
        return data

class RatingStatsSerializer(serializers.Serializer):
    """Serializer for rating statistics"""
    total_ratings = serializers.IntegerField()
    average_rating = serializers.FloatField()
    rating_distribution = serializers.DictField()
    verified_ratings = serializers.IntegerField(required=False)
    recent_ratings = serializers.IntegerField(required=False)
    top_rated_items = serializers.ListField(required=False)
    most_active_users = serializers.ListField(required=False)

class RatingUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating ratings"""
    class Meta:
        model = Rating
        fields = ['rating', 'comment']
        
    def validate(self, data):
        # Mark as edited when updating
        if self.instance:
            data['is_edited'] = True
        return data

class RatingSearchSerializer(serializers.Serializer):
    """Serializer for rating search parameters"""
    query = serializers.CharField(required=False, help_text="Search in comments and user info")
    item_id = serializers.UUIDField(required=False, help_text="Filter by item ID")
    min_rating = serializers.IntegerField(min_value=1, max_value=5, required=False)
    max_rating = serializers.IntegerField(min_value=1, max_value=5, required=False)
    verified_only = serializers.BooleanField(required=False)
    date_range = serializers.ChoiceField(
        choices=[('week', 'Week'), ('month', 'Month'), ('year', 'Year')],
        required=False
    )
    sort_by = serializers.ChoiceField(
        choices=[
            ('helpful', 'Most Helpful'),
            ('rating_high', 'Highest Rating'),
            ('rating_low', 'Lowest Rating'),
            ('recent', 'Most Recent'),
            ('oldest', 'Oldest'),
            ('verified_first', 'Verified First')
        ],
        required=False
    ) 