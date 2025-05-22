"""
Serializer for the Profile model, handling data validation and serialization.
Includes custom validation for file uploads, URLs, and profile fields.
"""

from rest_framework import serializers
from .models import Profile
from django.core.files.storage import default_storage
import os
import re
from datetime import date

class ProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for the Profile model, mapping user and profile fields.
    Handles validation, file uploads, and custom serialization logic.
    """
    email = serializers.EmailField(source='user.email', read_only=True)
    id = serializers.IntegerField(read_only=True)  # Use Profile's id field

    class Meta:
        model = Profile
        fields = [
            'id', 'name', 'email', 'age', 'weight', 'height', 'profession', 'location',
            'gender', 'hair_color', 'eye_color', 'body_type', 'has_driving_license',
            'video', 'photo', 'created_at', 'experience_level', 'skills',
            'nationality', 'availability', 'education_level', 'languages', 'min_salary',
            'max_salary', 'work_authorization', 'industry_experience', 'marital_status',
            'ethnicity', 'disability_status', 'disability_type', 'landmark',
            'availability_status', 'health_conditions', 'medications',
            'social_media_links', 'years_of_experience', 'employment_status',
            'previous_employers', 'projects', 'training', 'internship_experience', 'degree_type',
            'field_of_study', 'certifications', 'online_courses', 'preferred_work_location',
            'shift_preference', 'willingness_to_relocate', 'overtime_availability',
            'travel_willingness', 'software_proficiency', 'typing_speed', 'driving_skills',
            'equipment_experience', 'personality_type', 'work_preference', 'hobbies',
            'volunteer_experience', 'company_culture_preference', 'id_type', 'id_number',
            'id_expiry_date', 'id_front', 'id_back', 'id_verified', 'residence_type', 'address',
            'city', 'region', 'postal_code', 'residence_duration', 'housing_status',
            'emergency_contact', 'emergency_phone', 'birthdate', 'skin_tone', 'facial_hair',
            'tattoos_visible', 'piercings_visible', 'physical_condition', 'role_title',
            'portfolio_url', 'social_media_handles', 'union_membership', 'reference',
            'available_start_date', 'graduation_year', 'gpa', 'institution_name',
            'scholarships', 'academic_achievements', 'language_proficiency', 'special_skills',
            'tools_experience', 'award_recognitions', 'preferred_company_size',
            'preferred_industry', 'leadership_style', 'communication_style', 'motivation',
            'verified', 'flagged', 'status'
        ]
        read_only_fields = ['id', 'age', 'created_at', 'verified', 'flagged', 'email']

    def to_representation(self, instance):
        """
        Customize serialization to include file URLs and handle missing files.
        Sets file fields to None if the file does not exist on disk.
        """
        representation = super().to_representation(instance)
        file_fields = ['photo', 'video', 'id_front', 'id_back']
        for field in file_fields:
            file_obj = getattr(instance, field)
            if file_obj and default_storage.exists(file_obj.name):
                representation[field] = file_obj.url
            else:
                if file_obj:
                    setattr(instance, field, None)
                    instance.save()
                representation[field] = None
        return representation

    def validate_name(self, value):
        """
        Ensure the name field is not blank.
        """
        if not value.strip():
            raise serializers.ValidationError("Name cannot be blank.")
        return value

    def validate_email(self, value):
        """
        Ensure the email field is not blank.
        """
        if not value.strip():
            raise serializers.ValidationError("Email cannot be blank.")
        return value

    def validate_profession(self, value):
        """
        Ensure the profession field is not blank.
        """
        if not value.strip():
            raise serializers.ValidationError("Profession cannot be blank.")
        return value

    def validate_weight(self, value):
        """
        Ensure weight is not negative if provided.
        """
        if value is not None and value < 0:
            raise serializers.ValidationError("Weight cannot be negative.")
        return value

    def validate_height(self, value):
        """
        Ensure height is not negative if provided.
        """
        if value is not None and value < 0:
            raise serializers.ValidationError("Height cannot be negative.")
        return value

    def validate_birthdate(self, value):
        """
        Ensure birthdate is not in the future and is in a valid format.
        """
        if value is None:
            return value
        try:
            if value > date.today():
                raise serializers.ValidationError("Birthdate cannot be in the future.")
        except TypeError:
            raise serializers.ValidationError("Invalid date format. Use YYYY-MM-DD.")
        return value

    def validate_photo(self, value):
        """
        Validate photo file extension and size.
        """
        if not value:
            return value
        valid_image_extensions = ['.jpg', '.jpeg', '.png', '.gif']
        ext = os.path.splitext(value.name)[1].lower()
        if ext not in valid_image_extensions:
            raise serializers.ValidationError("Photo must be an image file (.jpg, .jpeg, .png, .gif).")
        if value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError("Photo file size must not exceed 5MB.")
        return value

    def validate_id_front(self, value):
        """
        Validate ID front image file extension and size.
        """
        if not value:
            return value
        valid_image_extensions = ['.jpg', '.jpeg', '.png', '.gif']
        ext = os.path.splitext(value.name)[1].lower()
        if ext not in valid_image_extensions:
            raise serializers.ValidationError("ID front must be an image file (.jpg, .jpeg, .png, .gif).")
        if value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError("ID front file size must not exceed 5MB.")
        return value

    def validate_id_back(self, value):
        """
        Validate ID back image file extension and size.
        """
        if not value:
            return value
        valid_image_extensions = ['.jpg', '.jpeg', '.png', '.gif']
        ext = os.path.splitext(value.name)[1].lower()
        if ext not in valid_image_extensions:
            raise serializers.ValidationError("ID back must be an image file (.jpg, .jpeg, .png, .gif).")
        if value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError("ID back file size must not exceed 5MB.")
        return value

    def validate_video(self, value):
        """
        Validate video file extension and size.
        """
        if not value:
            return value
        valid_video_extensions = ['.mp4', '.avi', '.mov', '.mkv']
        ext = os.path.splitext(value.name)[1].lower()
        if ext not in valid_video_extensions:
            raise serializers.ValidationError("Video must be a video file (.mp4, .avi, .mov, .mkv).")
        if value.size > 50 * 1024 * 1024:
            raise serializers.ValidationError("Video file size must not exceed 50MB.")
        return value

    def validate_social_media_links(self, value):
        """
        Validate social media URLs to ensure they start with http:// or https://.
        """
        for platform, url in value.items():
            if url and not (url.startswith('http://') or url.startswith('https://')):
                raise serializers.ValidationError({platform: "Invalid URL. Must start with http:// or https://"})
        return value

    def validate_url(self, url):
        """
        Validate URL format and domain restrictions.
        """
        url_pattern = re.compile(
            r'^(https?://)'
            r'((?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,6})'
            r'(/[-a-zA-Z0-9@:%._\+~#=]*)*'
            r'(\?[a-zA-Z0-9_=&-]*)?'
            r'(\#[a-zA-Z0-9_-]*)?$'
        )
        if not url_pattern.match(url):
            return False
        domain = url.split('/')[2]
        invalid_domains = ['invalid.com']
        if domain in invalid_domains:
            return False
        return True

    def create(self, validated_data):
        """
        Create a new Profile instance.
        """
        user = self.context['request'].user
        validated_data.pop('user', {})
        profile = Profile.objects.create(user=user, **validated_data)
        return profile

    def update(self, instance, validated_data):
        """
        Update an existing Profile instance, handling file uploads.
        Deletes old files when replaced and clears fields if set to None.
        """
        validated_data.pop('user', {})

        file_fields = ['photo', 'video', 'id_front', 'id_back']
        for field in file_fields:
            if field in validated_data:
                new_file = validated_data[field]
                old_file = getattr(instance, field)
                if old_file and new_file and old_file != new_file:
                    if default_storage.exists(old_file.name):
                        default_storage.delete(old_file.name)
                if new_file:
                    upload_to = getattr(getattr(instance, field), 'field').upload_to
                    os.makedirs(os.path.join(default_storage.location, upload_to), exist_ok=True)
                    getattr(instance, field).save(new_file.name, new_file, save=True)
                else:
                    if old_file:
                        if default_storage.exists(old_file.name):
                            default_storage.delete(old_file.name)
                    setattr(instance, field, None)
            elif self.partial and field in validated_data and validated_data[field] is None:
                old_file = getattr(instance, field)
                if old_file:
                    if default_storage.exists(old_file.name):
                        default_storage.delete(old_file.name)
                    # setattr(instance, field, None)

        for attr, value in validated_data.items():
            if attr not in file_fields:
                setattr(instance, attr, value)

        instance.save()
        return instance











