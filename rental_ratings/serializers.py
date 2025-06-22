from rest_framework import serializers
from .models import Rating
from userprofile.serializers import ProfileSerializer
from rental_items.models import RentalItem

class RatingSerializer(serializers.ModelSerializer):
    user_profile = ProfileSerializer(source='user.profile', read_only=True)
    item_details = serializers.SerializerMethodField()

    class Meta:
        model = Rating
        fields = ['id', 'item_id', 'user_id', 'rating', 'comment', 'created_at', 'user_profile', 'item_details']
        read_only_fields = ['id', 'created_at', 'user_profile', 'item_details', 'user_id', 'item_id']

    def get_item_details(self, obj):
        try:
            rental_item = RentalItem.objects.get(id=obj.item_id)
            return {
                'name': rental_item.name,
                'image': rental_item.image.url if rental_item.image else None
            }
        except RentalItem.DoesNotExist:
            return {
                'name': 'Item not found',
                'image': None
            }

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['user_id'] = str(instance.user.id)
        return representation

    def validate(self, data):
        user = self.context['request'].user
        item_id = data.get('item_id')
        if self.instance is None and Rating.objects.filter(user=user, item_id=item_id).exists():
            raise serializers.ValidationError("You have already rated this item.")
        return data 