from rest_framework import serializers
from .models import RentalItem, RentalItemRating, RentalItemImage
from userprofile.serializers import ProfileSerializer
from django.core.files.storage import default_storage
import os

class RentalItemImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = RentalItemImage
        fields = ['id', 'image', 'created_at']
        read_only_fields = ['id', 'created_at']

class RentalItemRatingSerializer(serializers.ModelSerializer):
    user_profile = ProfileSerializer(source='user.profile', read_only=True)
    item_details = serializers.SerializerMethodField()

    class Meta:
        model = RentalItemRating
        fields = ['id', 'item_id', 'user_id', 'rating', 'comment', 'created_at', 'user_profile', 'item_details']
        read_only_fields = ['id', 'created_at', 'user_profile', 'item_details']

    def get_item_details(self, obj):
        return {
            'name': obj.rental_item.name,
            'image': obj.rental_item.image.url if obj.rental_item.image else None
        }

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['item_id'] = str(instance.rental_item.id)
        representation['user_id'] = str(instance.user.id)
        return representation

class RentalItemSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    specs = serializers.JSONField()
    image = serializers.ImageField(required=False)
    average_rating = serializers.SerializerMethodField()
    total_ratings = serializers.SerializerMethodField()
    user_profile = ProfileSerializer(source='user.profile', read_only=True)
    ratings = RentalItemRatingSerializer(many=True, read_only=True)
    images = RentalItemImageSerializer(many=True, read_only=True)

    class Meta:
        model = RentalItem
        fields = ['id', 'user', 'name', 'type', 'category', 'description', 
                 'daily_rate', 'image', 'specs', 'available', 'featured_item',
                 'approved', 'created_at', 'updated_at', 'average_rating', 'total_ratings',
                 'user_profile', 'ratings', 'images']
        read_only_fields = ['user', 'approved', 'created_at', 'updated_at', 'user_profile', 'ratings', 'images']

    def get_average_rating(self, obj):
        ratings = obj.ratings.all()
        if not ratings:
            return None
        return sum(r.rating for r in ratings) / len(ratings)

    def get_total_ratings(self, obj):
        return obj.ratings.count()

    def update(self, instance, validated_data):
        # Handle image update separately
        image = validated_data.pop('image', None)
        if image is not None:
            # The old image will be deleted by the pre_save signal
            instance.image = image

        # Update other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance

class RentalItemListSerializer(serializers.ModelSerializer):
    user_profile = ProfileSerializer(source='user.profile', read_only=True)
    average_rating = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    class Meta:
        model = RentalItem
        fields = [
            'id', 'name', 'type', 'category', 'daily_rate', 'image',
            'available', 'featured_item', 'approved', 'user_profile',
            'average_rating'
        ]

    def get_average_rating(self, obj):
        ratings = obj.ratings.all()
        if not ratings:
            return None
        return sum(r.rating for r in ratings) / len(ratings)

    def get_image(self, obj):
        if obj.image:
            return obj.image.url
        return None

class RentalItemUpdateSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(required=False)
    additional_images = serializers.ListField(
        child=serializers.ImageField(),
        required=False,
        write_only=True
    )

    class Meta:
        model = RentalItem
        fields = ['name', 'description', 'daily_rate', 'available', 'image', 'additional_images']

    def update(self, instance, validated_data):
        # Handle main image update
        if 'image' in validated_data:
            instance.image = validated_data.pop('image')
        
        # Handle additional images
        if 'additional_images' in validated_data:
            new_images = validated_data.pop('additional_images')
            
            # Get existing images
            existing_images = list(instance.images.all())
            
            # Update or create images
            for i, image in enumerate(new_images):
                if i < len(existing_images):
                    # Update existing image
                    existing_image = existing_images[i]
                    existing_image.image = image
                    existing_image.save()
                else:
                    # Create new image
                    RentalItemImage.objects.create(
                        rental_item=instance,
                        image=image
                    )
            
            # Delete any remaining images
            for old_image in existing_images[len(new_images):]:
                old_image.delete()

        # Update other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # Add additional images to the response
        representation['additional_images'] = [
            {
                'id': str(img.id),
                'image': img.image.url,
                'created_at': img.created_at
            }
            for img in instance.images.all()
        ]
        return representation 