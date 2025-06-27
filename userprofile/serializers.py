from rest_framework import serializers
from .models import (
    Profile, BasicInformation, LocationInformation, IdentityVerification, PhysicalAttributes,
    MedicalInfo, PersonalInfo, VerificationStatus, VerificationAuditLog, ProfessionsAndSkills, SocialMedia, Headshot, NaturalPhotos
)
from django.core.files.storage import default_storage
from django.db import IntegrityError, transaction
import os
import re
import magic
from datetime import date
import bleach
import json
from django.conf import settings

# Helper function to sanitize strings
def sanitize_string(value):
    if not value:
        return value
    # First, remove HTML tags using bleach
    cleaned_value = bleach.clean(value, tags=[], strip=True)
    # Remove JavaScript-like patterns (e.g., alert(...), evil(), etc.)
    cleaned_value = re.sub(r'\b(alert|eval|prompt|confirm|evil)\s*\([^)]*\)', '', cleaned_value, flags=re.IGNORECASE)
    # Remove any remaining parentheses content that might resemble JavaScript
    cleaned_value = re.sub(r'\b\w+\s*\([^)]*\)', '', cleaned_value)
    # Remove excessive whitespace and strip
    cleaned_value = re.sub(r'\s+', ' ', cleaned_value).strip()
    return cleaned_value

# Helper function to convert string to lowercase for case insensitive handling
def to_lowercase(value):
    if isinstance(value, str):
        return value.lower()
    return value

class IdentityVerificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = IdentityVerification
        fields = ['id_type', 'id_number', 'id_expiry_date', 'id_front', 'id_back', 'id_verified']
        read_only_fields = ['id_verified']

    def validate(self, data):
        return data

    def get_id_number(self, obj):
        id_number = obj.id_number
        if id_number and len(id_number) > 4:
            return '*' * (len(id_number) - 4) + id_number[-4:]
        return id_number

    def validate_id_type(self, value):
        if value:
            value = to_lowercase(value)
            value = sanitize_string(value)
            if not value.strip():
                raise serializers.ValidationError("ID type cannot be empty after sanitization.")
        return value

    def validate_id_expiry_date(self, value):
        if value is None:
            return value
        try:
            if value < date.today():
                raise serializers.ValidationError("ID expiry date cannot be in the past.")
        except TypeError:
            raise serializers.ValidationError("Invalid date format. Use YYYY-MM-DD.")
        return value

    def validate_id_front(self, value):
        if not value:
            return value
        valid_image_extensions = ['.jpg', '.jpeg', '.png', '.gif']
        ext = os.path.splitext(value.name)[1].lower()
        if ext not in valid_image_extensions:
            raise serializers.ValidationError("ID front must be an image file (.jpg, .jpeg, .png, .gif).")
        if value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError("ID front file size must not exceed 5MB.")
        mime = magic.Magic(mime=True)
        mime_type = mime.from_buffer(value.read(2048))
        value.seek(0)
        valid_mime_types = ['image/jpeg', 'image/png', 'image/gif']
        if mime_type not in valid_mime_types:
            raise serializers.ValidationError("Invalid ID front image. Must be a valid image format (jpg, jpeg, png, gif).")
        return value

    def validate_id_back(self, value):
        if not value:
            return value
        valid_image_extensions = ['.jpg', '.jpeg', '.png', '.gif']
        ext = os.path.splitext(value.name)[1].lower()
        if ext not in valid_image_extensions:
            raise serializers.ValidationError("ID back must be an image file (.jpg, .jpeg, .png, .gif).")
        if value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError("ID back file size must not exceed 5MB.")
        mime = magic.Magic(mime=True)
        mime_type = mime.from_buffer(value.read(2048))
        value.seek(0)
        valid_mime_types = ['image/jpeg', 'image/png', 'image/gif']
        if mime_type not in valid_mime_types:
            raise serializers.ValidationError("Invalid ID back image. Must be a valid image format (jpg, jpeg, png, gif).")
        return value

class ActorCategorySerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()
    description = serializers.CharField()

class PhysicalAttributesSerializer(serializers.ModelSerializer):
    class Meta:
        model = PhysicalAttributes
        fields = [
            'id', 'facial_hair', 'physical_condition'
        ]
        read_only_fields = ['id']

    def validate(self, data):
        # Convert string fields to lowercase for case insensitive handling
        string_fields = ['facial_hair', 'physical_condition']
        
        for field in string_fields:
            if field in data and data[field]:
                data[field] = to_lowercase(data[field])
        
        # No required fields validation needed since all fields are optional
        return data

class MedicalInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicalInfo
        fields = [
            'id', 'disability_status', 'disability_type'
        ]
        read_only_fields = ['id']

    def validate(self, data):
        # Convert string fields to lowercase for case insensitive handling
        string_fields = ['disability_status', 'disability_type']
        
        for field in string_fields:
            if field in data and data[field]:
                data[field] = to_lowercase(data[field])
        
        # No required fields validation needed since all fields are optional
        return data

class PersonalInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PersonalInfo
        fields = [
            'id', 'first_name', 'last_name', 'language_proficiency',
            'custom_language', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate(self, data):
        # Convert string fields to lowercase for case insensitive handling
        string_fields = ['first_name', 'last_name', 'custom_language']
        
        for field in string_fields:
            if field in data and data[field]:
                data[field] = to_lowercase(data[field])
        
        # Validate language_proficiency
        if not data.get('language_proficiency'):
            raise serializers.ValidationError("Language proficiency is required.")

        # Validate that custom_language is provided if language_proficiency contains 'other'
        if 'other' in data.get('language_proficiency', []) and not data.get('custom_language'):
            raise serializers.ValidationError("Custom language is required when 'other' is selected in language proficiency.")

        # Validate custom_language format if provided
        if data.get('custom_language'):
            custom_lang = data['custom_language']
            # Check for minimum length
            if len(custom_lang.strip()) < 2:
                raise serializers.ValidationError("Custom language must be at least 2 characters long.")
            
            # Check for maximum length
            if len(custom_lang.strip()) > 50:
                raise serializers.ValidationError("Custom language cannot exceed 50 characters.")
            
            # Check for valid characters (letters, spaces, hyphens, apostrophes)
            if not re.match(r'^[a-zA-Z\s\-\']+$', custom_lang.strip()):
                raise serializers.ValidationError("Custom language can only contain letters, spaces, hyphens, and apostrophes.")
            
            # Check for excessive spaces
            if '  ' in custom_lang:
                raise serializers.ValidationError("Custom language cannot contain excessive spaces.")
            
            # Check for leading/trailing spaces
            if custom_lang != custom_lang.strip():
                raise serializers.ValidationError("Custom language cannot have leading or trailing spaces.")

        return data

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

class SocialMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = SocialMedia
        fields = [
            'id', 'instagram_username', 'instagram_followers', 'facebook_username', 
            'facebook_followers', 'youtube_username', 'youtube_followers', 
            'tiktok_username', 'tiktok_followers'
        ]
        read_only_fields = ['id']

    def validate(self, data):
        # Convert string fields to lowercase for case insensitive handling
        string_fields = ['instagram_username', 'facebook_username', 'youtube_username', 'tiktok_username']
        
        for field in string_fields:
            if field in data and data[field]:
                data[field] = to_lowercase(data[field])
        
        return data

class HeadshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Headshot
        fields = ['id', 'professional_headshot', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_professional_headshot(self, value):
        if not value:
            return value
        
        # Validate file extension
        valid_image_extensions = ['.jpg', '.jpeg', '.png']
        ext = os.path.splitext(value.name)[1].lower()
        if ext not in valid_image_extensions:
            raise serializers.ValidationError("Professional headshot must be an image file (.jpg, .jpeg, .png).")
        
        # Validate file size
        if value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError("Professional headshot file size must not exceed 5MB.")
        
        # Validate MIME type
        mime = magic.Magic(mime=True)
        mime_type = mime.from_buffer(value.read(2048))
        value.seek(0)
        valid_mime_types = ['image/jpeg', 'image/png']
        if mime_type not in valid_mime_types:
            raise serializers.ValidationError("Invalid professional headshot image. Must be a valid image format (jpg, jpeg, png).")
        
        return value

class NaturalPhotosSerializer(serializers.ModelSerializer):
    class Meta:
        model = NaturalPhotos
        fields = ['natural_photo_1', 'natural_photo_2', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

    def validate_natural_photo_1(self, value):
        if not value:
            return value
        valid_image_extensions = ['.jpg', '.jpeg', '.png']
        ext = os.path.splitext(value.name)[1].lower()
        if ext not in valid_image_extensions:
            raise serializers.ValidationError("Natural photo 1 must be an image file (.jpg, .jpeg, .png).")
        if value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError("Natural photo 1 file size must not exceed 5MB.")
        mime = magic.Magic(mime=True)
        mime_type = mime.from_buffer(value.read(2048))
        value.seek(0)
        valid_mime_types = ['image/jpeg', 'image/png']
        if mime_type not in valid_mime_types:
            raise serializers.ValidationError("Invalid natural photo 1 image. Must be a valid image format (jpg, jpeg, png).")
        return value

    def validate_natural_photo_2(self, value):
        if not value:
            return value
        valid_image_extensions = ['.jpg', '.jpeg', '.png']
        ext = os.path.splitext(value.name)[1].lower()
        if ext not in valid_image_extensions:
            raise serializers.ValidationError("Natural photo 2 must be an image file (.jpg, .jpeg, .png).")
        if value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError("Natural photo 2 file size must not exceed 5MB.")
        mime = magic.Magic(mime=True)
        mime_type = mime.from_buffer(value.read(2048))
        value.seek(0)
        valid_mime_types = ['image/jpeg', 'image/png']
        if mime_type not in valid_mime_types:
            raise serializers.ValidationError("Invalid natural photo 2 image. Must be a valid image format (jpg, jpeg, png).")
        return value

class BasicInformationSerializer(serializers.ModelSerializer):
    class Meta:
        model = BasicInformation
        fields = [
            'id', 'nationality', 'gender', 'languages', 'hair_color', 'eye_color', 'skin_tone',
            'body_type', 'medical_condition', 'medicine_type', 'marital_status', 'hobbies',
            'date_of_birth', 'height', 'weight', 'emergency_contact_name', 'emergency_contact_phone',
            'custom_hobby', 'driving_license', 'visible_piercings', 'visible_tattoos', 'willing_to_travel',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate(self, data):
        # Convert string fields to lowercase for case insensitive handling
        string_fields = [
            'nationality', 'gender', 'hair_color', 'eye_color', 'skin_tone', 'body_type',
            'marital_status', 'emergency_contact_name', 'custom_hobby', 'willing_to_travel'
        ]
        
        for field in string_fields:
            if field in data and data[field]:
                data[field] = to_lowercase(data[field])
        
        # Validate required fields
        if not data.get('nationality'):
            raise serializers.ValidationError({"nationality": "Nationality is required."})
        if not data.get('gender'):
            raise serializers.ValidationError({"gender": "Gender is required."})
        if not data.get('languages'):
            raise serializers.ValidationError({"languages": "Languages are required."})
        if not data.get('hair_color'):
            raise serializers.ValidationError({"hair_color": "Hair color is required."})
        if not data.get('eye_color'):
            raise serializers.ValidationError({"eye_color": "Eye color is required."})
        if not data.get('skin_tone'):
            raise serializers.ValidationError({"skin_tone": "Skin tone is required."})
        if not data.get('body_type'):
            raise serializers.ValidationError({"body_type": "Body type is required."})
        if not data.get('medical_condition'):
            raise serializers.ValidationError({"medical_condition": "Medical condition is required."})
        if not data.get('medicine_type'):
            raise serializers.ValidationError({"medicine_type": "Medicine type is required."})
        if not data.get('marital_status'):
            raise serializers.ValidationError({"marital_status": "Marital status is required."})
        if not data.get('hobbies'):
            raise serializers.ValidationError({"hobbies": "Hobbies are required."})
        if not data.get('date_of_birth'):
            raise serializers.ValidationError({"date_of_birth": "Date of birth is required."})
        if not data.get('height'):
            raise serializers.ValidationError({"height": "Height is required."})
        if not data.get('weight'):
            raise serializers.ValidationError({"weight": "Weight is required."})
        if not data.get('emergency_contact_name'):
            raise serializers.ValidationError({"emergency_contact_name": "Emergency contact name is required."})
        if not data.get('emergency_contact_phone'):
            raise serializers.ValidationError({"emergency_contact_phone": "Emergency contact phone is required."})
        if not data.get('willing_to_travel'):
            raise serializers.ValidationError({"willing_to_travel": "Willingness to travel is required."})

        # Validate date of birth
        date_of_birth = data.get('date_of_birth')
        if date_of_birth:
            if date_of_birth > date.today():
                raise serializers.ValidationError({
                    'date_of_birth': 'Date of birth cannot be in the future.'
                })
            # Calculate age
            age = (date.today() - date_of_birth).days // 365
            if age < 18:
                raise serializers.ValidationError({
                    'date_of_birth': 'Must be at least 18 years old.'
                })
            if age > 100:
                raise serializers.ValidationError({
                    'date_of_birth': 'Age cannot exceed 100 years.'
                })

        return data

class LocationInformationSerializer(serializers.ModelSerializer):
    class Meta:
        model = LocationInformation
        fields = [
            'id', 'housing_status', 'region', 'duration', 'city', 'country',
            'address', 'specific_area', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate(self, data):
        # Convert string fields to lowercase for case insensitive handling
        string_fields = [
            'housing_status', 'region', 'duration', 'city', 'address', 'specific_area'
        ]
        
        for field in string_fields:
            if field in data and data[field]:
                data[field] = to_lowercase(data[field])
        
        # Validate required fields
        if not data.get('address'):
            raise serializers.ValidationError({"address": "Address is required."})
        if not data.get('specific_area'):
            raise serializers.ValidationError({"specific_area": "Specific area is required."})

        return data

class ProfessionsAndSkillsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfessionsAndSkills
        fields = [
            'id', 'professions', 'actor_category', 'model_categories', 'performer_categories',
            'influencer_categories', 'skills', 'main_skill', 'skill_description', 'video_url'
        ]
        read_only_fields = ['id']

    def validate(self, data):
        # Validate that at least one profession is selected
        if not data.get('professions'):
            raise serializers.ValidationError({"professions": "At least one profession is required."})
        
        return data

class ProfileSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='user.name', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    age = serializers.IntegerField(read_only=True)
    identity_verification = IdentityVerificationSerializer(required=True)
    basic_information = BasicInformationSerializer(required=True)
    location_information = LocationInformationSerializer(required=True)
    professions_and_skills = ProfessionsAndSkillsSerializer(required=True)
    physical_attributes = PhysicalAttributesSerializer(required=True)
    medical_info = MedicalInfoSerializer(required=True)
    personal_info = PersonalInfoSerializer(required=True)
    social_media = SocialMediaSerializer(required=False)
    headshot = HeadshotSerializer(required=False)
    natural_photos = NaturalPhotosSerializer(required=False)

    class Meta:
        model = Profile
        fields = [
            'id', 'name', 'email', 'birthdate', 'profession', 'age', 'location', 'created_at',
            'availability_status', 'verified', 'flagged', 'status',
            'identity_verification', 'basic_information', 'location_information', 'professions_and_skills', 'physical_attributes',
            'medical_info', 'personal_info', 'social_media', 'headshot', 'natural_photos'
        ]
        read_only_fields = ['id', 'name', 'age', 'created_at', 'verified', 'flagged', 'email']

    def validate(self, data):
        # Convert string fields to lowercase for case insensitive handling
        string_fields = ['profession', 'location', 'status']
        
        for field in string_fields:
            if field in data and data[field]:
                data[field] = to_lowercase(data[field])
        
        return data

    def create(self, validated_data):
        # Extract nested data
        identity_verification_data = validated_data.pop('identity_verification', {})
        basic_information_data = validated_data.pop('basic_information', {})
        location_information_data = validated_data.pop('location_information', {})
        professions_and_skills_data = validated_data.pop('professions_and_skills', {})
        physical_attributes_data = validated_data.pop('physical_attributes', {})
        medical_info_data = validated_data.pop('medical_info', {})
        personal_info_data = validated_data.pop('personal_info', {})
        social_media_data = validated_data.pop('social_media', {})
        headshot_data = validated_data.pop('headshot', {})
        natural_photos_data = validated_data.pop('natural_photos', {})

        # Create profile
        profile = Profile.objects.create(**validated_data)

        # Create related objects
        related_objects = [
            ('identity_verification', IdentityVerification, IdentityVerificationSerializer),
            ('basic_information', BasicInformation, BasicInformationSerializer),
            ('location_information', LocationInformation, LocationInformationSerializer),
            ('professions_and_skills', ProfessionsAndSkills, ProfessionsAndSkillsSerializer),
            ('physical_attributes', PhysicalAttributes, PhysicalAttributesSerializer),
            ('medical_info', MedicalInfo, MedicalInfoSerializer),
            ('personal_info', PersonalInfo, PersonalInfoSerializer),
            ('social_media', SocialMedia, SocialMediaSerializer),
            ('headshot', Headshot, HeadshotSerializer),
            ('natural_photos', NaturalPhotos, NaturalPhotosSerializer),
        ]

        for field_name, model_class, serializer_class in related_objects:
            data = locals()[f'{field_name}_data']
            if data:
                serializer = serializer_class(data=data)
                if serializer.is_valid():
                    model_class.objects.create(profile=profile, **serializer.validated_data)

        return profile

    def update(self, instance, validated_data):
        # Extract nested data
        identity_verification_data = validated_data.pop('identity_verification', {})
        basic_information_data = validated_data.pop('basic_information', {})
        location_information_data = validated_data.pop('location_information', {})
        professions_and_skills_data = validated_data.pop('professions_and_skills', {})
        physical_attributes_data = validated_data.pop('physical_attributes', {})
        medical_info_data = validated_data.pop('medical_info', {})
        personal_info_data = validated_data.pop('personal_info', {})
        social_media_data = validated_data.pop('social_media', {})
        headshot_data = validated_data.pop('headshot', {})
        natural_photos_data = validated_data.pop('natural_photos', {})

        # Update profile
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update related objects
        related_objects = [
            ('identity_verification', IdentityVerification, IdentityVerificationSerializer),
            ('basic_information', BasicInformation, BasicInformationSerializer),
            ('location_information', LocationInformation, LocationInformationSerializer),
            ('professions_and_skills', ProfessionsAndSkills, ProfessionsAndSkillsSerializer),
            ('physical_attributes', PhysicalAttributes, PhysicalAttributesSerializer),
            ('medical_info', MedicalInfo, MedicalInfoSerializer),
            ('personal_info', PersonalInfo, PersonalInfoSerializer),
            ('social_media', SocialMedia, SocialMediaSerializer),
            ('headshot', Headshot, HeadshotSerializer),
            ('natural_photos', NaturalPhotos, NaturalPhotosSerializer),
        ]

        for field_name, model_class, serializer_class in related_objects:
            data = locals()[f'{field_name}_data']
            if data:
                related_instance = getattr(instance, field_name, None)
                if related_instance:
                    serializer = serializer_class(related_instance, data=data, partial=True)
                    if serializer.is_valid():
                        serializer.save()
                else:
                    serializer = serializer_class(data=data)
                    if serializer.is_valid():
                        model_class.objects.create(profile=instance, **serializer.validated_data)

        return instance

class VerificationStatusSerializer(serializers.ModelSerializer):
    verified_by_email = serializers.EmailField(source='verified_by.email', read_only=True)
    
    class Meta:
        model = VerificationStatus
        fields = [
            'is_verified', 'verification_type', 'verification_date', 
            'verified_by', 'verified_by_email', 'verification_method', 
            'verification_notes', 'last_updated'
        ]
        read_only_fields = ['verification_date', 'verified_by', 'last_updated']

    def validate(self, data):
        # Only allow verification through proper channels
        if 'is_verified' in data and data['is_verified']:
            request = self.context.get('request')
            if not request or not request.user.has_perm('userprofile.verify_profiles'):
                raise serializers.ValidationError("You don't have permission to verify profiles")
        return data

class VerificationAuditLogSerializer(serializers.ModelSerializer):
    changed_by_email = serializers.EmailField(source='changed_by.email', read_only=True)
    profile_name = serializers.CharField(source='profile.name', read_only=True)

    class Meta:
        model = VerificationAuditLog
        fields = [
            'id', 'profile', 'profile_name', 'previous_status', 'new_status',
            'changed_by', 'changed_by_email', 'changed_at', 'verification_type',
            'verification_method', 'notes', 'ip_address', 'user_agent'
        ]
        read_only_fields = ['changed_at', 'changed_by', 'ip_address', 'user_agent']

class PublicProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for public profile data - excludes sensitive information
    """
    name = serializers.CharField(source='user.name', read_only=True)
    age = serializers.IntegerField(read_only=True)
    
    # Only include basic professional and physical attributes for public viewing
    professions_and_skills = serializers.SerializerMethodField()
    physical_attributes = serializers.SerializerMethodField()
    headshot = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = [
            'id', 'name', 'profession', 'age', 'location', 'created_at',
            'availability_status', 'verified', 'status',
            'professions_and_skills', 'physical_attributes', 'headshot'
        ]
        read_only_fields = ['id', 'name', 'age', 'created_at', 'verified']

    def get_professions_and_skills(self, obj):
        try:
            if hasattr(obj, 'professions_and_skills') and obj.professions_and_skills:
                return {
                    'professions': obj.professions_and_skills.professions,
                    'skills': obj.professions_and_skills.skills,
                    'skill_description': obj.professions_and_skills.skill_description,
                    'video_url': obj.professions_and_skills.video_url
                }
        except:
            pass
        return {}

    def get_physical_attributes(self, obj):
        try:
            if hasattr(obj, 'physical_attributes') and obj.physical_attributes:
                return {
                    'facial_hair': obj.physical_attributes.facial_hair,
                    'physical_condition': obj.physical_attributes.physical_condition
                }
        except:
            pass
        return {}

    def get_headshot(self, obj):
        try:
            if hasattr(obj, 'headshot') and obj.headshot and obj.headshot.professional_headshot:
                return {
                    'professional_headshot': obj.headshot.professional_headshot.url
                }
        except:
            pass
        return {}