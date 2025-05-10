# from rest_framework import serializers
# from .models import GalleryItem
# from userprofile.models import Profile
# import os
#
# class ProfileIDField(serializers.Field):
#     """
#     Custom field to handle profile_id as a nested dictionary during deserialization
#     and an integer during serialization.
#     """
#     def to_representation(self, value):
#         # When serializing (e.g., for GET), return the user.id as an integer
#         return value.user.id
#
#     def to_internal_value(self, data):
#         # When deserializing (e.g., for POST), handle nested dictionary or flat integer
#         if isinstance(data, dict):
#             # Handle nested structure like {'user': {'id': 6}}
#             user_data = data.get('user', {})
#             user_id = user_data.get('id')
#         else:
#             # Handle flat integer like 6
#             user_id = data
#
#         try:
#             user_id = int(user_id)
#         except (TypeError, ValueError):
#             raise serializers.ValidationError("profile_id must be a valid integer.")
#
#         return user_id
#
# class GalleryItemSerializer(serializers.ModelSerializer):
#     """
#     Serializer for the GalleryItem model, handling data validation and serialization.
#
#     Includes custom validation for file uploads and ensures consistency with the API specification.
#     """
#     profile_id = ProfileIDField()  # Removed source='profile_id'
#     item_url = serializers.FileField()
#     profile = serializers.SerializerMethodField()
#
#     class Meta:
#         model = GalleryItem
#         fields = ['id', 'profile_id', 'item_url', 'item_type', 'description', 'created_at', 'updated_at', 'profile']
#
#     def get_profile(self, obj):
#         """
#         Get profile details for the associated user.
#
#         Args:
#             obj (GalleryItem): The gallery item instance.
#
#         Returns:
#             dict: Profile details including name, profession, and photo URL.
#         """
#         return {
#             'name': obj.profile_id.name,
#             'profession': obj.profile_id.profession,
#             'photo_url': obj.profile_id.photo.url if obj.profile_id.photo else ''
#         }
#
#     def validate_item_url(self, value):
#         """
#         Validate the uploaded file for extension and size.
#
#         Args:
#             value (File): The uploaded file object.
#
#         Raises:
#             serializers.ValidationError: If the file extension or size is invalid.
#
#         Returns:
#             File: The validated file object.
#         """
#         valid_image_extensions = ['.jpg', '.jpeg', '.png', '.gif']
#         valid_video_extensions = ['.mp4', '.avi', '.mov', '.mkv']
#         ext = os.path.splitext(value.name)[1].lower()
#         if ext not in valid_image_extensions + valid_video_extensions:
#             raise serializers.ValidationError("File must be an image (.jpg, .jpeg, .png, .gif) or video (.mp4, .avi, .mov, .mkv).")
#         if value.size > 50 * 1024 * 1024:
#             raise serializers.ValidationError("File size must not exceed 50MB.")
#         return value
#
#     def create(self, validated_data):
#         """
#         Create a new GalleryItem instance with the associated profile.
#
#         Args:
#             validated_data (dict): Validated data from the request.
#
#         Returns:
#             GalleryItem: The created gallery item instance.
#         """
#         user_id = validated_data.pop('profile_id')
#         profile = Profile.objects.get(user__id=user_id)
#         item_url = validated_data.pop('item_url')
#         instance = GalleryItem.objects.create(profile_id=profile, item_url=item_url, **validated_data)
#         return instance
#
#     def update(self, instance, validated_data):
#         """
#         Update an existing GalleryItem instance, handling file uploads.
#
#         Args:
#             instance (GalleryItem): The gallery item to update.
#             validated_data (dict): Validated data from the request.
#
#         Returns:
#             GalleryItem: The updated gallery item instance.
#         """
#         item_url = validated_data.get('item_url')
#         if item_url:
#             # Delete the old file from the filesystem if it exists
#             if instance.item_url and os.path.isfile(instance.item_url.path):
#                 os.remove(instance.item_url.path)
#             instance.item_url = item_url
#             instance.save()  # Save to update item_type automatically via the model's save method
#         instance.description = validated_data.get('description', instance.description)
#         instance.item_type = validated_data.get('item_type', instance.item_type)
#         instance.save()
#         return instance

from rest_framework import serializers
from .models import GalleryItem
from userprofile.models import Profile
import os

class ProfileIDField(serializers.Field):
    """
    Custom field to handle profile_id as a nested dictionary during deserialization
    and an integer during serialization.
    """
    def to_representation(self, value):
        # When serializing (e.g., for GET), return the Profile.id as an integer
        return value.id  # Changed from value.user.id to value.id

    def to_internal_value(self, data):
        # When deserializing (e.g., for POST), handle nested dictionary or flat integer
        if isinstance(data, dict):
            # Handle nested structure like {'id': 6}
            profile_id = data.get('id')
        else:
            # Handle flat integer like 6
            profile_id = data

        try:
            profile_id = int(profile_id)
        except (TypeError, ValueError):
            raise serializers.ValidationError("profile_id must be a valid integer.")

        return profile_id

class GalleryItemSerializer(serializers.ModelSerializer):
    """
    Serializer for the GalleryItem model, handling data validation and serialization.

    Includes custom validation for file uploads and ensures consistency with the API specification.
    """
    profile_id = ProfileIDField()  # Custom field for profile_id
    item_url = serializers.FileField()
    profile = serializers.SerializerMethodField()

    class Meta:
        model = GalleryItem
        fields = ['id', 'profile_id', 'item_url', 'item_type', 'description', 'created_at', 'updated_at', 'profile']

    def get_profile(self, obj):
        """
        Get profile details for the associated user.

        Args:
            obj (GalleryItem): The gallery item instance.

        Returns:
            dict: Profile details including name, profession, and photo URL.
        """
        return {
            'name': obj.profile_id.name,
            'profession': obj.profile_id.profession,
            'photo_url': obj.profile_id.photo.url if obj.profile_id.photo else ''
        }

    def validate_item_url(self, value):
        """
        Validate the uploaded file for extension and size.

        Args:
            value (File): The uploaded file object.

        Raises:
            serializers.ValidationError: If the file extension or size is invalid.

        Returns:
            File: The validated file object.
        """
        valid_image_extensions = ['.jpg', '.jpeg', '.png', '.gif']
        valid_video_extensions = ['.mp4', '.avi', '.mov', '.mkv']
        ext = os.path.splitext(value.name)[1].lower()
        if ext not in valid_image_extensions + valid_video_extensions:
            raise serializers.ValidationError("File must be an image (.jpg, .jpeg, .png, .gif) or video (.mp4, .avi, .mov, .mkv).")
        if value.size > 50 * 1024 * 1024:
            raise serializers.ValidationError("File size must not exceed 50MB.")
        return value

    def create(self, validated_data):
        """
        Create a new GalleryItem instance with the associated profile.

        Args:
            validated_data (dict): Validated data from the request.

        Returns:
            GalleryItem: The created gallery item instance.
        """
        profile_id = validated_data.pop('profile_id')  # Now directly the Profile.id
        profile = Profile.objects.get(id=profile_id)  # Changed from user__id to id
        item_url = validated_data.pop('item_url')
        instance = GalleryItem.objects.create(profile_id=profile, item_url=item_url, **validated_data)
        return instance

    def update(self, instance, validated_data):
        """
        Update an existing GalleryItem instance, handling file uploads.

        Args:
            instance (GalleryItem): The gallery item to update.
            validated_data (dict): Validated data from the request.

        Returns:
            GalleryItem: The updated gallery item instance.
        """
        item_url = validated_data.get('item_url')
        if item_url:
            # Delete the old file from the filesystem if it exists
            if instance.item_url and os.path.isfile(instance.item_url.path):
                os.remove(instance.item_url.path)
            instance.item_url = item_url
            instance.save()  # Save to update item_type automatically via the model's save method
        instance.description = validated_data.get('description', instance.description)
        instance.item_type = validated_data.get('item_type', instance.item_type)
        instance.save()
        return instance