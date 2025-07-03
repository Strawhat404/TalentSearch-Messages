from rest_framework import serializers
from .models import GalleryItem
from userprofile.models import Profile
import os
from PIL import Image
import mimetypes
import bleach


class ProfileIDField(serializers.Field):
    """
    Custom field to handle profile_id as a nested dictionary during deserialization
    and an integer during serialization.
    """

    def to_representation(self, value):
        return value.id

    def to_internal_value(self, data):
        if isinstance(data, dict):
            profile_id = data.get('id')
        else:
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
    profile_id = ProfileIDField()
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
        photo_url = ''
        try:
            if hasattr(obj.profile_id, 'headshot') and obj.profile_id.headshot and obj.profile_id.headshot.professional_headshot:
                photo_url = obj.profile_id.headshot.professional_headshot.url
        except:
            pass

        basic_info = getattr(obj.profile_id.basic_information, 'all', [None])[0] if hasattr(obj.profile_id,
                                                                                            'basic_information') else None
        name = basic_info.nationality if basic_info and basic_info.nationality else obj.profile_id.name

        professions_and_skills = obj.profile_id.professions_and_skills if hasattr(obj.profile_id,
                                                                                  'professions_and_skills') else ProfessionsAndSkills.objects.filter(
            profile_id=obj.profile_id).first()
        profession = professions_and_skills.professions if professions_and_skills and professions_and_skills.professions else [
            "Not specified"]

        return {
            'name': name,
            'profession': profession,
            'photo_url': photo_url
        }

    def validate_item_url(self, value):
        """
        Validate the uploaded file for extension, size, and content.

        Args:
            value (File): The uploaded file object.

        Raises:
            serializers.ValidationError: If the file extension, size, or content is invalid.

        Returns:
            File: The validated file object.
        """
        valid_image_extensions = ['.jpg', '.jpeg', '.png', '.gif']
        valid_video_extensions = ['.mp4', '.avi', '.mov', '.mkv']
        ext = os.path.splitext(value.name)[1].lower()

        if ext not in valid_image_extensions + valid_video_extensions:
            raise serializers.ValidationError(
                "File must be an image (.jpg, .jpeg, .png, .gif) or video (.mp4, .avi, .mov, .mkv).")

        if value.size > 50 * 1024 * 1024:
            raise serializers.ValidationError("File size must not exceed 50MB.")

        # Content validation
        if ext in valid_image_extensions:
            try:
                with Image.open(value) as img:
                    img.verify()
            except Exception as e:
                raise serializers.ValidationError(f"Invalid image file: {str(e)}")
        elif ext in valid_video_extensions:
            mime_type, _ = mimetypes.guess_type(value.name)
            if not mime_type or not mime_type.startswith('video/'):
                raise serializers.ValidationError("File must be a valid video (e.g., mp4, avi, mov, mkv).")

        return value

    def validate_description(self, value):
        """
        Sanitize the description field to prevent XSS attacks.

        Args:
            value (str): The description text.

        Returns:
            str: Sanitized description text.
        """
        if value:
            allowed_tags = ['p', 'br', 'strong', 'em', 'ul', 'li', 'a']
            return bleach.clean(value, tags=allowed_tags, strip=True)
        return value

    def create(self, validated_data):
        """
        Create a new GalleryItem instance with the associated profile.

        Args:
            validated_data (dict): Validated data from the request.

        Returns:
            GalleryItem: The created gallery item instance.
        """
        profile_id = validated_data.pop('profile_id')
        profile = Profile.objects.get(id=profile_id)
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
            if instance.item_url and os.path.isfile(instance.item_url.path):
                os.remove(instance.item_url.path)
            instance.item_url = item_url
            instance.save()  # Triggers model save for item_type and description sanitization
        instance.description = validated_data.get('description', instance.description)
        instance.item_type = validated_data.get('item_type', instance.item_type)
        instance.save()
        return instance