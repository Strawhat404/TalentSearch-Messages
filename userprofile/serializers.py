from rest_framework import serializers
from .models import (
    Profile, IdentityVerification, ProfessionalQualifications, PhysicalAttributes,
    MedicalInfo, Education, WorkExperience, ContactInfo, PersonalInfo, Media
)
from django.core.files.storage import default_storage
from django.db import IntegrityError, transaction
import os
import re
import magic
from datetime import date
import bleach

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

class IdentityVerificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = IdentityVerification
        fields = ['id_type', 'id_number', 'id_expiry_date', 'id_front', 'id_back', 'id_verified']
        read_only_fields = ['id_verified']

    def get_id_number(self, obj):
        id_number = obj.id_number
        if id_number and len(id_number) > 4:
            return '*' * (len(id_number) - 4) + id_number[-4:]
        return id_number

    def validate_id_type(self, value):
        if value:
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

class ProfessionalQualificationsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfessionalQualifications
        fields = [
            'experience_level', 'skills', 'work_authorization', 'industry_experience',
            'min_salary', 'max_salary', 'availability', 'preferred_work_location', 'shift_preference',
            'willingness_to_relocate', 'overtime_availability', 'travel_willingness', 'software_proficiency',
            'typing_speed', 'driving_skills', 'equipment_experience', 'role_title', 'portfolio_url',
            'union_membership', 'reference', 'available_start_date', 'preferred_company_size',
            'preferred_industry', 'leadership_style', 'communication_style', 'motivation', 'has_driving_license'
        ]

    def validate_experience_level(self, value):
        if value:
            value = sanitize_string(value)
            if not value.strip():
                return ""
        return value

    def validate_work_authorization(self, value):
        if value:
            value = sanitize_string(value)
            if not value.strip():
                return ""
        return value

    def validate_industry_experience(self, value):
        if value:
            value = sanitize_string(value)
            if not value.strip():
                return ""
        return value

    def validate_availability(self, value):
        if value:
            value = sanitize_string(value)
            if not value.strip():
                return ""
        return value

    def validate_preferred_work_location(self, value):
        if value:
            value = sanitize_string(value)
            if not value.strip():
                return ""
        return value

    def validate_shift_preference(self, value):
        if value:
            value = sanitize_string(value)
            if not value.strip():
                return ""
        return value

    def validate_willingness_to_relocate(self, value):
        if value:
            value = sanitize_string(value)
            if not value.strip():
                return ""
        return value

    def validate_overtime_availability(self, value):
        if value:
            value = sanitize_string(value)
            if not value.strip():
                return ""
        return value

    def validate_travel_willingness(self, value):
        if value:
            value = sanitize_string(value)
            if not value.strip():
                return ""
        return value

    def validate_driving_skills(self, value):
        if value:
            value = sanitize_string(value)
            if not value.strip():
                return ""
        return value

    def validate_role_title(self, value):
        if value:
            value = sanitize_string(value)
            if not value.strip():
                return ""
        return value

    def validate_union_membership(self, value):
        if value:
            value = sanitize_string(value)
            if not value.strip():
                return ""
        return value

    def validate_preferred_company_size(self, value):
        if value:
            value = sanitize_string(value)
            if not value.strip():
                return ""
        return value

    def validate_leadership_style(self, value):
        if value:
            value = sanitize_string(value)
            if not value.strip():
                return ""
        return value

    def validate_communication_style(self, value):
        if value:
            value = sanitize_string(value)
            if not value.strip():
                return ""
        return value

    def validate_motivation(self, value):
        if value:
            value = sanitize_string(value)
            if not value.strip():
                return ""
        return value

    def validate_min_salary(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Minimum salary cannot be negative.")
        return value

    def validate_max_salary(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Maximum salary cannot be negative.")
        return value

class PhysicalAttributesSerializer(serializers.ModelSerializer):
    class Meta:
        model = PhysicalAttributes
        fields = [
            'weight', 'height', 'gender', 'hair_color', 'eye_color', 'body_type',
            'skin_tone', 'facial_hair', 'tattoos_visible', 'piercings_visible', 'physical_condition'
        ]

    def validate_gender(self, value):
        if value:
            value = sanitize_string(value)
            if not value.strip():
                return ""
        return value

    def validate_hair_color(self, value):
        if value:
            value = sanitize_string(value)
            if not value.strip():
                return ""
        return value

    def validate_eye_color(self, value):
        if value:
            value = sanitize_string(value)
            if not value.strip():
                return ""
        return value

    def validate_body_type(self, value):
        if value:
            value = sanitize_string(value)
            if not value.strip():
                return ""
        return value

    def validate_skin_tone(self, value):
        if value:
            value = sanitize_string(value)
            if not value.strip():
                return ""
        return value

    def validate_facial_hair(self, value):
        if value:
            value = sanitize_string(value)
            if not value.strip():
                return ""
        return value

    def validate_physical_condition(self, value):
        if value:
            value = sanitize_string(value)
            if not value.strip():
                return ""
        return value

    def validate_weight(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Weight cannot be negative.")
        return value

    def validate_height(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Height cannot be negative.")
        return value

class MedicalInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicalInfo
        fields = ['health_conditions', 'medications', 'disability_status', 'disability_type']

    def validate_disability_status(self, value):
        if value:
            value = sanitize_string(value)
            if not value.strip():
                return ""
        return value

    def validate_disability_type(self, value):
        if value:
            value = sanitize_string(value)
            if not value.strip():
                return "None"
        return value

class EducationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Education
        fields = [
            'education_level', 'degree_type', 'field_of_study', 'graduation_year',
            'gpa', 'institution_name', 'scholarships', 'academic_achievements',
            'certifications', 'online_courses'
        ]

    def validate_education_level(self, value):
        if value:
            value = sanitize_string(value)
            if not value.strip():
                return ""
        return value

    def validate_degree_type(self, value):
        if value:
            value = sanitize_string(value)
            if not value.strip():
                return ""
        return value

    def validate_field_of_study(self, value):
        if value:
            value = sanitize_string(value)
            if not value.strip():
                return ""
        return value

    def validate_graduation_year(self, value):
        if value:
            value = sanitize_string(value)
            if not value.strip():
                return ""
        return value

    def validate_institution_name(self, value):
        if value:
            value = sanitize_string(value)
            if not value.strip():
                return ""
        return value

class WorkExperienceSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkExperience
        fields = [
            'years_of_experience', 'employment_status', 'previous_employers',
            'projects', 'training', 'internship_experience'
        ]

    def validate_years_of_experience(self, value):
        if value:
            value = sanitize_string(value)
            if not value.strip():
                return ""
        return value

    def validate_employment_status(self, value):
        if value:
            value = sanitize_string(value)
            if not value.strip():
                return ""
        return value

    def validate_internship_experience(self, value):
        if value:
            value = sanitize_string(value)
            if not value.strip():
                return ""
        return value

class ContactInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactInfo
        fields = [
            'address', 'city', 'region', 'postal_code', 'residence_type',
            'residence_duration', 'housing_status', 'emergency_contact', 'emergency_phone'
        ]

    def validate_address(self, value):
        if value:
            value = sanitize_string(value)
            if not value.strip():
                return ""
        return value

    def validate_city(self, value):
        if value:
            value = sanitize_string(value)
            if not value.strip():
                return ""
        return value

    def validate_region(self, value):
        if value:
            value = sanitize_string(value)
            if not value.strip():
                return ""
        return value

    def validate_residence_type(self, value):
        if value:
            value = sanitize_string(value)
            if not value.strip():
                return ""
        return value

    def validate_residence_duration(self, value):
        if value:
            value = sanitize_string(value)
            if not value.strip():
                return ""
        return value

    def validate_housing_status(self, value):
        if value:
            value = sanitize_string(value)
            if not value.strip():
                return ""
        return value

    def validate_emergency_contact(self, value):
        if value:
            value = sanitize_string(value)
            if not value.strip():
                return ""
        return value

class PersonalInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PersonalInfo
        fields = [
            'marital_status', 'ethnicity', 'personality_type', 'work_preference',
            'hobbies', 'volunteer_experience', 'company_culture_preference', 'social_media_links',
            'social_media_handles', 'language_proficiency', 'special_skills', 'tools_experience',
            'award_recognitions'
        ]

    def validate_marital_status(self, value):
        if value:
            value = sanitize_string(value)
            if not value.strip():
                return ""
        return value

    def validate_ethnicity(self, value):
        if value:
            value = sanitize_string(value)
            if not value.strip():
                return ""
        return value

    def validate_personality_type(self, value):
        if value:
            value = sanitize_string(value)
            if not value.strip():
                return ""
        return value

    def validate_work_preference(self, value):
        if value:
            value = sanitize_string(value)
            if not value.strip():
                return ""
        return value

    def validate_volunteer_experience(self, value):
        if value:
            value = sanitize_string(value)
            if not value.strip():
                return ""
        return value

    def validate_company_culture_preference(self, value):
        if value:
            value = sanitize_string(value)
            if not value.strip():
                return ""
        return value

    def validate_social_media_links(self, value):
        sanitized_value = {}
        for platform, url in value.items():
            if url:
                sanitized_url = sanitize_string(url)
                if not (sanitized_url.startswith('http://') or sanitized_url.startswith('https://')):
                    raise serializers.ValidationError({platform: "Invalid URL. Must start with http:// or https://"})
                sanitized_value[platform] = sanitized_url
            else:
                sanitized_value[platform] = url
        return sanitized_value

class MediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Media
        fields = ['video', 'photo']

    def validate_photo(self, value):
        if not value:
            return value
        valid_image_extensions = ['.jpg', '.jpeg', '.png', '.gif']
        ext = os.path.splitext(value.name)[1].lower()
        if ext not in valid_image_extensions:
            raise serializers.ValidationError("Photo must be an image file (.jpg, .jpeg, .png, .gif).")
        if value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError("Photo file size must not exceed 5MB.")
        mime = magic.Magic(mime=True)
        mime_type = mime.from_buffer(value.read(2048))
        value.seek(0)
        valid_mime_types = ['image/jpeg', 'image/png', 'image/gif']
        if mime_type not in valid_mime_types:
            raise serializers.ValidationError("Invalid image file. Must be a valid image format (jpg, jpeg, png, gif).")
        return value

    def validate_video(self, value):
        if not value:
            return value
        valid_video_extensions = ['.mp4', '.avi', '.mov', '.mkv']
        ext = os.path.splitext(value.name)[1].lower()
        if ext not in valid_video_extensions:
            raise serializers.ValidationError("Video must be a video file (.mp4, .avi, .mov, .mkv).")
        if value.size > 50 * 1024 * 1024:
            raise serializers.ValidationError("Video file size must not exceed 50MB.")
        mime = magic.Magic(mime=True)
        mime_type = mime.from_buffer(value.read(2048))
        value.seek(0)
        valid_mime_types = ['video/mp4', 'video/avi', 'video/quicktime', 'video/x-matroska']
        if mime_type not in valid_mime_types:
            raise serializers.ValidationError("Invalid video file. Must be a valid video format (mp4, avi, mov, mkv).")
        return value

class ProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)
    age = serializers.IntegerField(read_only=True)
    identity_verification = IdentityVerificationSerializer(required=False)
    professional_qualifications = ProfessionalQualificationsSerializer(required=False)
    physical_attributes = PhysicalAttributesSerializer(required=False)
    medical_info = MedicalInfoSerializer(required=False)
    education = EducationSerializer(required=False)
    work_experience = WorkExperienceSerializer(required=False)
    contact_info = ContactInfoSerializer(required=False)
    personal_info = PersonalInfoSerializer(required=False)
    media = MediaSerializer(required=False)

    class Meta:
        model = Profile
        fields = [
            'id', 'name', 'email', 'birthdate', 'profession', 'nationality', 'age', 'location', 'created_at',
            'availability_status', 'verified', 'flagged', 'status',
            'identity_verification', 'professional_qualifications', 'physical_attributes',
            'medical_info', 'education', 'work_experience', 'contact_info',
            'personal_info', 'media'
        ]
        read_only_fields = ['id', 'age', 'created_at', 'verified', 'flagged', 'email']

    def to_representation(self, instance):
        representation = super(serializers.ModelSerializer, self).to_representation(instance)
        nested_serializers = [
            ('identity_verification', IdentityVerificationSerializer),
            ('professional_qualifications', ProfessionalQualificationsSerializer),
            ('physical_attributes', PhysicalAttributesSerializer),
            ('medical_info', MedicalInfoSerializer),
            ('education', EducationSerializer),
            ('work_experience', WorkExperienceSerializer),
            ('contact_info', ContactInfoSerializer),
            ('personal_info', PersonalInfoSerializer),
            ('media', MediaSerializer),
        ]
        file_fields = [
            ('media', 'photo'), ('media', 'video'),
            ('identity_verification', 'id_front'), ('identity_verification', 'id_back')
        ]
        for field_name, serializer_class in nested_serializers:
            related_instance = getattr(instance, field_name, None)
            if related_instance:
                serializer = serializer_class(related_instance)
                representation[field_name] = serializer.data
            else:
                serializer = serializer_class()
                empty_data = {}
                for field in serializer.fields.values():
                    if field.read_only:
                        continue
                    if isinstance(field, serializers.BooleanField):
                        empty_data[field.field_name] = False
                    elif isinstance(field, (serializers.IntegerField, serializers.FloatField, serializers.DecimalField)):
                        empty_data[field.field_name] = None
                    elif isinstance(field, serializers.ListField) or field.field_name in [
                        'skills', 'software_proficiency', 'equipment_experience', 'reference', 'preferred_industry',
                        'health_conditions', 'medications', 'scholarships', 'academic_achievements', 'certifications',
                        'online_courses', 'previous_employers', 'projects', 'training', 'hobbies', 'social_media_handles',
                        'language_proficiency', 'special_skills', 'tools_experience', 'award_recognitions'
                    ]:
                        empty_data[field.field_name] = []
                    elif isinstance(field, serializers.DictField) or field.field_name == 'social_media_links':
                        empty_data[field.field_name] = {}
                    else:
                        empty_data[field.field_name] = None
                representation[field_name] = empty_data
        for model_field, field in file_fields:
            if representation[model_field] is None:
                continue
            file_obj = None
            related_instance = getattr(instance, model_field, None)
            if related_instance:
                file_obj = getattr(related_instance, field, None)
            if file_obj and default_storage.exists(file_obj.name):
                representation[model_field][field] = file_obj.url
            else:
                if file_obj and related_instance:
                    setattr(related_instance, field, None)
                    related_instance.save()
                representation[model_field][field] = None
        if representation['identity_verification'] and representation['identity_verification']['id_number']:
            id_number = representation['identity_verification']['id_number']
            if len(id_number) > 4:
                representation['identity_verification']['id_number'] = '*' * (len(id_number) - 4) + id_number[-4:]
        return representation

    def validate_name(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Name cannot be blank.")
        return sanitize_string(value)

    def validate_birthdate(self, value):
        if value is None:
            raise serializers.ValidationError("Birthdate is required.")
        try:
            if value > date.today():
                raise serializers.ValidationError("Birthdate cannot be in the future.")
        except TypeError:
            raise serializers.ValidationError("Invalid date format. Use YYYY-MM-DD.")
        return value

    def validate_profession(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Profession cannot be blank.")
        return sanitize_string(value)

    def validate_nationality(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Nationality cannot be blank.")
        return sanitize_string(value)

    def validate_location(self, value):
        if value:
            value = sanitize_string(value)
            if not value.strip():
                return ""
        return value

    def validate_status(self, value):
        if value:
            value = sanitize_string(value)
            if not value.strip():
                return ""
        return value

    def validate(self, data):
        id_data = data.get('identity_verification', {})
        id_type = id_data.get('id_type')
        id_number = id_data.get('id_number')
        if id_type and id_number:
            if id_type == 'kebele_id':
                if not id_number.strip():
                    raise serializers.ValidationError({'identity_verification.id_number': 'Kebele ID must not be empty.'})
            elif id_type == 'national_id':
                if not re.match(r'^\d{12}$', id_number):
                    raise serializers.ValidationError({'identity_verification.id_number': 'National ID must be exactly 12 digits.'})
            elif id_type == 'passport':
                if not re.match(r'^E[P]?\d{7,8}$', id_number):
                    raise serializers.ValidationError({'identity_verification.id_number': 'Passport must start with "E" or "EP" followed by 7-8 digits.'})
            elif id_type == 'drivers_license':
                if not re.match(r'^[A-Za-z0-9]+$', id_number):
                    raise serializers.ValidationError({'identity_verification.id_number': 'Driver’s License must contain only letters and numbers.'})
        elif id_type and not id_number:
            raise serializers.ValidationError({'identity_verification.id_number': f'{id_type} requires a valid ID number.'})
        elif id_number and not id_type:
            raise serializers.ValidationError({'identity_verification.id_type': 'ID type must be specified when providing an ID number.'})
        prof_data = data.get('professional_qualifications', {})
        min_salary = prof_data.get('min_salary')
        max_salary = prof_data.get('max_salary')
        if min_salary is not None and max_salary is not None:
            if min_salary > max_salary:
                raise serializers.ValidationError({'professional_qualifications.min_salary': 'Minimum salary cannot be greater than maximum salary.'})
        contact_data = data.get('contact_info', {})
        postal_code = contact_data.get('postal_code')
        if postal_code:
            postal_pattern = r'^\d{4}$'
            if not re.match(postal_pattern, postal_code.strip()):
                raise serializers.ValidationError({'contact_info.postal_code': 'Postal code must be exactly 4 digits (e.g., "1234").'})
            if not contact_data.get('city') or not contact_data.get('region'):
                raise serializers.ValidationError({'contact_info.postal_code': 'City and region must be provided when postal code is set.'})
        return data

    def create(self, validated_data):
        user = self.context['request'].user
        nested_data = [
            ('identity_verification', IdentityVerification, IdentityVerificationSerializer),
            ('professional_qualifications', ProfessionalQualifications, ProfessionalQualificationsSerializer),
            ('physical_attributes', PhysicalAttributes, PhysicalAttributesSerializer),
            ('medical_info', MedicalInfo, MedicalInfoSerializer),
            ('education', Education, EducationSerializer),
            ('work_experience', WorkExperience, WorkExperienceSerializer),
            ('contact_info', ContactInfo, ContactInfoSerializer),
            ('personal_info', PersonalInfo, PersonalInfoSerializer),
            ('media', Media, MediaSerializer)
        ]
        nested_validated_data = {key: validated_data.pop(key, {}) for key, _, _ in nested_data}
        for key, model, serializer_class in nested_data:
            if nested_validated_data[key]:
                serializer = serializer_class(data=nested_validated_data[key])
                serializer.is_valid(raise_exception=True)
                nested_validated_data[key] = serializer.validated_data
        if Profile.objects.filter(user=user).exists():
            raise serializers.ValidationError({"error": "A profile already exists for this user."})
        try:
            with transaction.atomic():
                profile = Profile.objects.create(user=user, **validated_data)
                for key, model, _ in nested_data:
                    if nested_validated_data[key]:
                        model.objects.create(profile=profile, **nested_validated_data[key])
                return profile
        except (ValueError, IntegrityError) as e:
            raise serializers.ValidationError({"error": str(e) if isinstance(e, ValueError) else "A profile already exists for this user or a database constraint was violated."})

    def update(self, instance, validated_data):
        nested_data = [
            ('identity_verification', IdentityVerification, IdentityVerificationSerializer),
            ('professional_qualifications', ProfessionalQualifications, ProfessionalQualificationsSerializer),
            ('physical_attributes', PhysicalAttributes, PhysicalAttributesSerializer),
            ('medical_info', MedicalInfo, MedicalInfoSerializer),
            ('education', Education, EducationSerializer),
            ('work_experience', WorkExperience, WorkExperienceSerializer),
            ('contact_info', ContactInfo, ContactInfoSerializer),
            ('personal_info', PersonalInfo, PersonalInfoSerializer),
            ('media', Media, MediaSerializer)
        ]
        nested_validated_data = {key: validated_data.pop(key, {}) for key, _, _ in nested_data}
        file_fields = [
            ('media', 'photo'), ('media', 'video'),
            ('identity_verification', 'id_front'), ('identity_verification', 'id_back')
        ]
        for key, model, serializer_class in nested_data:
            model_instance = getattr(instance, key, None)
            if model_instance:
                for field_name, field_value in nested_validated_data[key].items():
                    if any(key == model_key and field_name == field for model_key, field in file_fields):
                        old_file = getattr(model_instance, field_name, None)
                        if old_file and field_value and old_file != field_value:
                            if default_storage.exists(old_file.name):
                                default_storage.delete(old_file.name)
                        if field_value:
                            upload_to = getattr(getattr(model_instance, field_name), 'field').upload_to
                            os.makedirs(os.path.join(default_storage.location, upload_to), exist_ok=True)
                            getattr(model_instance, field_name).save(field_value.name, field_value, save=False)
                        elif field_value is None and old_file:
                            if default_storage.exists(old_file.name):
                                default_storage.delete(old_file.name)
                            setattr(model_instance, field_name, None)
                    else:
                        setattr(model_instance, field_name, field_value)
                model_instance.save()
            else:
                model.objects.create(profile=instance, **nested_validated_data[key])
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance