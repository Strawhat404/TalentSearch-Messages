from rest_framework import serializers
from .models import (
    Profile, IdentityVerification, ProfessionalQualifications, PhysicalAttributes,
    MedicalInfo, Education, WorkExperience, ContactInfo, PersonalInfo, Media, VerificationStatus, VerificationAuditLog, LocationData,
    HOUSING_STATUS_CHOICES, RESIDENCE_DURATION_CHOICES
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

# --- Load static choice lists once -------------------------------------------------
DATA_DIR = os.path.join(settings.BASE_DIR, 'userprofile', 'data')

def _safe_load(list_name, filename, key):
    try:
        with open(os.path.join(DATA_DIR, filename), 'r') as _f:
            return json.load(_f)[key]
    except Exception:
        return []

ALLOWED_LANGUAGES          = _safe_load('languages',            'languages.json',            'languages')
PHYSICAL_DATA              = _safe_load('physical_attributes',  'physical_attributes.json',  None)
# when key is None we returned full dict; handle fallback
if isinstance(PHYSICAL_DATA, dict):
    HAIR_COLORS   = PHYSICAL_DATA.get('hair_colors', [])
    EYE_COLORS    = PHYSICAL_DATA.get('eye_colors', [])
    SKIN_TONES    = PHYSICAL_DATA.get('skin_tones', [])
    BODY_TYPES    = PHYSICAL_DATA.get('body_types', [])
else:
    HAIR_COLORS = EYE_COLORS = SKIN_TONES = BODY_TYPES = []

MEDICAL_DATA = _safe_load('medical_info', 'medical_info.json', None)
if isinstance(MEDICAL_DATA, dict):
    KNOWN_MED_CONDITIONS = MEDICAL_DATA.get('disability_statuses', []) + MEDICAL_DATA.get('medical_conditions', []) if MEDICAL_DATA else []
    KNOWN_MEDICINE_TYPES = MEDICAL_DATA.get('medicine_types', [])
else:
    KNOWN_MED_CONDITIONS = KNOWN_MEDICINE_TYPES = []

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

class ActorCategorySerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()
    description = serializers.CharField()

class ProfessionalQualificationsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfessionalQualifications
        fields = [
            'id', 'main_skill', 'model_categories', 'performer_categories', 'professions',
            'skill_description', 'video_url', 'experience_level', 'work_authorization',
            'availability', 'preferred_work_location', 'shift_preference', 'role_title',
            'preferred_company_size', 'preferred_industry', 'leadership_style',
            'communication_style', 'motivation', 'min_salary', 'max_salary'
        ]
        read_only_fields = ['id']

    def validate(self, data):
        # Validate required fields
        if not data.get('professions'):
            raise serializers.ValidationError({"professions": "At least one profession is required."})
        if not data.get('experience_level'):
            raise serializers.ValidationError({"experience_level": "Experience level is required."})
        if not data.get('work_authorization'):
            raise serializers.ValidationError({"work_authorization": "Work authorization is required."})
        if not data.get('availability'):
            raise serializers.ValidationError({"availability": "Availability is required."})
        if not data.get('preferred_work_location'):
            raise serializers.ValidationError({"preferred_work_location": "Preferred work location is required."})
        if not data.get('shift_preference'):
            raise serializers.ValidationError({"shift_preference": "Shift preference is required."})

        # Validate salary range if provided
        min_salary = data.get('min_salary')
        max_salary = data.get('max_salary')
        if min_salary is not None and max_salary is not None:
            if min_salary > max_salary:
                raise serializers.ValidationError({"min_salary": "Minimum salary cannot be greater than maximum salary."})

        # Validate that main_skill is one of the selected skills
        if data.get('main_skill') and data.get('skills'):
            if data['main_skill'] not in data['skills']:
                raise serializers.ValidationError({
                    'main_skill': 'Main skill must be one of the selected skills'
                })

        # travel_willingness must be present per consultant
        if 'travel_willingness' not in data:
            raise serializers.ValidationError({"travel_willingness": "Willingness to travel must be specified (true/false)."})

        return data

class PhysicalAttributesSerializer(serializers.ModelSerializer):
    class Meta:
        model = PhysicalAttributes
        fields = [
            'id', 'height', 'weight', 'gender', 'hair_color', 'eye_color',
            'body_type', 'skin_tone', 'facial_hair', 'tattoos_visible',
            'piercings_visible', 'physical_condition'
        ]
        read_only_fields = ['id']

    def validate(self, data):
        # Validate required fields
        if not data.get('height'):
            raise serializers.ValidationError({"height": "Height is required."})
        if not data.get('weight'):
            raise serializers.ValidationError({"weight": "Weight is required."})
        if not data.get('gender'):
            raise serializers.ValidationError({"gender": "Gender is required."})
        if not data.get('hair_color'):
            raise serializers.ValidationError({"hair_color": "Hair color is required."})
        if not data.get('eye_color'):
            raise serializers.ValidationError({"eye_color": "Eye color is required."})
        if not data.get('body_type'):
            raise serializers.ValidationError({"body_type": "Body type is required."})
        if not data.get('skin_tone'):
            raise serializers.ValidationError({"skin_tone": "Skin tone is required."})

        # Validate height and weight if provided
        height = data.get('height')
        if height is not None:
            if height < 100 or height > 300:
                raise serializers.ValidationError({
                    'height': 'Height must be between 100 and 300 centimeters.'
                })

        weight = data.get('weight')
        if weight is not None:
            if weight < 30 or weight > 500:
                raise serializers.ValidationError({
                    'weight': 'Weight must be between 30 and 500 kilograms.'
                })

        # Membership validation using static lists
        if data.get('hair_color') and data['hair_color'] not in HAIR_COLORS:
            raise serializers.ValidationError({'hair_color': 'Invalid hair color.'})
        if data.get('eye_color') and data['eye_color'] not in EYE_COLORS:
            raise serializers.ValidationError({'eye_color': 'Invalid eye color.'})
        if data.get('skin_tone') and data['skin_tone'] not in SKIN_TONES:
            raise serializers.ValidationError({'skin_tone': 'Invalid skin tone.'})
        if data.get('body_type') and data['body_type'] not in BODY_TYPES:
            raise serializers.ValidationError({'body_type': 'Invalid body type.'})

        return data

class MedicalInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicalInfo
        fields = [
            'id', 'health_conditions', 'medications', 'disability_status',
            'disability_type'
        ]
        read_only_fields = ['id']

    def validate(self, data):
        # Validate required fields
        if not data.get('health_conditions'):
            raise serializers.ValidationError({"health_conditions": "Health conditions are required."})
        if not data.get('medications'):
            raise serializers.ValidationError({"medications": "Medications are required."})

        # Membership checks
        invalid_conditions = [c for c in data.get('health_conditions', []) if c not in KNOWN_MED_CONDITIONS]
        if invalid_conditions:
            raise serializers.ValidationError({'health_conditions': f'Invalid condition(s): {", ".join(invalid_conditions)}'})

        invalid_meds = [m for m in data.get('medications', []) if m not in KNOWN_MEDICINE_TYPES]
        if invalid_meds:
            raise serializers.ValidationError({'medications': f'Invalid medication type(s): {", ".join(invalid_meds)}'})

        return data

class EducationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Education
        fields = [
            'id', 'education_level', 'degree_type', 'field_of_study',
            'graduation_year', 'gpa', 'institution_name', 'scholarships',
            'academic_achievements', 'certifications', 'online_courses'
        ]
        read_only_fields = ['id']

    def validate(self, data):
        # Validate required fields
        if not data.get('education_level'):
            raise serializers.ValidationError({"education_level": "Education level is required."})
        if not data.get('institution_name'):
            raise serializers.ValidationError({"institution_name": "Institution name is required."})

        # Validate graduation year if provided
        graduation_year = data.get('graduation_year')
        if graduation_year:
            try:
                year = int(graduation_year)
                current_year = date.today().year
                if year < 1900 or year > current_year:
                    raise serializers.ValidationError({
                        'graduation_year': f'Graduation year must be between 1900 and {current_year}.'
                    })
            except ValueError:
                raise serializers.ValidationError({
                    'graduation_year': 'Graduation year must be a valid year.'
                })

        # Validate GPA if provided
        gpa = data.get('gpa')
        if gpa is not None:
            if gpa < 0 or gpa > 4.0:
                raise serializers.ValidationError({
                    'gpa': 'GPA must be between 0 and 4.0.'
                })

        return data

class WorkExperienceSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkExperience
        fields = [
            'id', 'years_of_experience', 'employment_status', 'previous_employers',
            'projects', 'training', 'internship_experience'
        ]
        read_only_fields = ['id']

    def validate(self, data):
        # Validate required fields
        if not data.get('years_of_experience'):
            raise serializers.ValidationError({"years_of_experience": "Years of experience is required."})
        if not data.get('employment_status'):
            raise serializers.ValidationError({"employment_status": "Employment status is required."})

        # Validate previous employers if provided
        previous_employers = data.get('previous_employers', [])
        if previous_employers:
            for employer in previous_employers:
                if not isinstance(employer, dict):
                    raise serializers.ValidationError({
                        'previous_employers': 'Each employer must be a dictionary.'
                    })
                if 'name' not in employer:
                    raise serializers.ValidationError({
                        'previous_employers': 'Each employer must have a name.'
                    })
                if 'position' not in employer:
                    raise serializers.ValidationError({
                        'previous_employers': 'Each employer must have a position.'
                    })
                if 'duration' not in employer:
                    raise serializers.ValidationError({
                        'previous_employers': 'Each employer must have a duration.'
                    })

        # Validate projects if provided
        projects = data.get('projects', [])
        if projects:
            for project in projects:
                if not isinstance(project, dict):
                    raise serializers.ValidationError({
                        'projects': 'Each project must be a dictionary.'
                    })
                if 'name' not in project:
                    raise serializers.ValidationError({
                        'projects': 'Each project must have a name.'
                    })
                if 'description' not in project:
                    raise serializers.ValidationError({
                        'projects': 'Each project must have a description.'
                    })
                if 'duration' not in project:
                    raise serializers.ValidationError({
                        'projects': 'Each project must have a duration.'
                    })

        # Validate training if provided
        training = data.get('training', [])
        if training:
            for item in training:
                if not isinstance(item, dict):
                    raise serializers.ValidationError({
                        'training': 'Each training item must be a dictionary.'
                    })
                if 'name' not in item:
                    raise serializers.ValidationError({
                        'training': 'Each training item must have a name.'
                    })
                if 'institution' not in item:
                    raise serializers.ValidationError({
                        'training': 'Each training item must have an institution.'
                    })
                if 'duration' not in item:
                    raise serializers.ValidationError({
                        'training': 'Each training item must have a duration.'
                    })

        return data

class ContactInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactInfo
        fields = [
            'id', 'address', 'city', 'region', 'country', 'specific_area',
            'emergency_contact', 'emergency_phone', 'housing_status',
            'residence_duration'
        ]
        read_only_fields = ['id']

    def validate(self, data):
        # Validate required fields
        if not data.get('address'):
            raise serializers.ValidationError({"address": "Address is required."})
        if not data.get('city'):
            raise serializers.ValidationError({"city": "City is required."})
        if not data.get('region'):
            raise serializers.ValidationError({"region": "Region is required."})
        if not data.get('country'):
            raise serializers.ValidationError({"country": "Country is required."})
        if not data.get('emergency_contact'):
            raise serializers.ValidationError({"emergency_contact": "Emergency contact is required."})
        if not data.get('emergency_phone'):
            raise serializers.ValidationError({"emergency_phone": "Emergency phone is required."})
        if not data.get('housing_status'):
            raise serializers.ValidationError({"housing_status": "Housing status is required."})
        if not data.get('residence_duration'):
            raise serializers.ValidationError({"residence_duration": "Residence duration is required."})

        # Validate phone number format
        emergency_phone = data.get('emergency_phone')
        if emergency_phone:
            if not re.match(r'^\+251[0-9]{9}$', emergency_phone):
                raise serializers.ValidationError({
                    'emergency_phone': 'Phone must start with +251 followed by 9 digits.'
                })

        # Validate housing status
        housing_status = data.get('housing_status')
        if housing_status:
            valid_statuses = [choice[0] for choice in HOUSING_STATUS_CHOICES]
            if housing_status not in valid_statuses:
                raise serializers.ValidationError({
                    'housing_status': f'Invalid housing status. Must be one of: {", ".join(valid_statuses)}'
                })

        # Validate residence duration
        residence_duration = data.get('residence_duration')
        if residence_duration:
            valid_durations = [choice[0] for choice in RESIDENCE_DURATION_CHOICES]
            if residence_duration not in valid_durations:
                raise serializers.ValidationError({
                    'residence_duration': f'Invalid residence duration. Must be one of: {", ".join(valid_durations)}'
                })

        return data

class PersonalInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PersonalInfo
        fields = [
            'id', 'first_name', 'last_name', 'date_of_birth', 'gender', 'marital_status',
            'nationality', 'id_type', 'id_number', 'hobbies', 'language_proficiency',
            'social_media', 'custom_hobby', 'custom_language', 'custom_social_media',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate(self, data):
        # Validate required fields
        if not data.get('date_of_birth'):
            raise serializers.ValidationError({"date_of_birth": "Date of birth is required."})
        if not data.get('gender'):
            raise serializers.ValidationError({"gender": "Gender is required."})
        if not data.get('marital_status'):
            raise serializers.ValidationError({"marital_status": "Marital status is required."})
        if not data.get('nationality'):
            raise serializers.ValidationError({"nationality": "Nationality is required."})
        if not data.get('hobbies'):
            raise serializers.ValidationError({"hobbies": "At least one hobby is required."})
        if not data.get('language_proficiency'):
            raise serializers.ValidationError({"language_proficiency": "At least one language proficiency is required."})
        if not data.get('custom_hobby'):
            raise serializers.ValidationError({"custom_hobby": "Custom hobby is required."})
        
        # Validate social media accounts
        social_media = data.get('social_media', {})
        if not social_media:
            raise serializers.ValidationError({"social_media": "At least one social media account is required."})
        
        # Validate ID number based on ID type
        id_type = data.get('id_type')
        id_number = data.get('id_number')
        if id_type and id_number:
            if id_type == 'national_id':
                if not re.match(r'^\d{12}$', id_number):
                    raise serializers.ValidationError({'id_number': 'National ID must be exactly 12 digits.'})
            elif id_type == 'passport':
                if not re.match(r'^E[P]?\d{7,8}$', id_number):
                    raise serializers.ValidationError({'id_number': 'Passport must start with "E" or "EP" followed by 7-8 digits.'})
            elif id_type == 'drivers_license':
                if not re.match(r'^[A-Za-z0-9]+$', id_number):
                    raise serializers.ValidationError({'id_number': "Driver's License must contain only letters and numbers."})
        elif id_type and not id_number:
            raise serializers.ValidationError({'id_number': f'{id_type} requires a valid ID number.'})
        elif id_number and not id_type:
            raise serializers.ValidationError({'id_type': 'ID type must be specified when providing an ID number.'})

        # Validate languages membership
        invalid_langs = [lng for lng in data.get('language_proficiency', []) if lng not in ALLOWED_LANGUAGES]
        if invalid_langs:
            raise serializers.ValidationError({'language_proficiency': f'Invalid language codes: {", ".join(invalid_langs)}'})

        return data

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

    def validate(self, data):
        # Validate required fields
        if not data.get('birthdate'):
            raise serializers.ValidationError({"birthdate": "Date of birth is required."})
        if not data.get('profession'):
            raise serializers.ValidationError({"profession": "Profession is required."})
        if not data.get('nationality'):
            raise serializers.ValidationError({"nationality": "Nationality is required."})
        if not data.get('location'):
            raise serializers.ValidationError({"location": "Location is required."})

        # Validate nested data
        personal_info = data.get('personal_info', {})
        if personal_info:
            if not personal_info.get('social_media'):
                raise serializers.ValidationError({"personal_info.social_media": "At least one social media account is required."})
            if not personal_info.get('marital_status'):
                raise serializers.ValidationError({"personal_info.marital_status": "Marital status is required."})
            if not personal_info.get('hobbies'):
                raise serializers.ValidationError({"personal_info.hobbies": "At least one hobby is required."})
            if not personal_info.get('language_proficiency'):
                raise serializers.ValidationError({"personal_info.language_proficiency": "At least one language proficiency is required."})

        professional_qualifications = data.get('professional_qualifications', {})
        if professional_qualifications:
            if not professional_qualifications.get('professions'):
                raise serializers.ValidationError({"professional_qualifications.professions": "At least one profession is required."})
            if not professional_qualifications.get('experience_level'):
                raise serializers.ValidationError({"professional_qualifications.experience_level": "Experience level is required."})
            if not professional_qualifications.get('work_authorization'):
                raise serializers.ValidationError({"professional_qualifications.work_authorization": "Work authorization is required."})
            if not professional_qualifications.get('availability'):
                raise serializers.ValidationError({"professional_qualifications.availability": "Availability is required."})
            if not professional_qualifications.get('preferred_work_location'):
                raise serializers.ValidationError({"professional_qualifications.preferred_work_location": "Preferred work location is required."})
            if not professional_qualifications.get('shift_preference'):
                raise serializers.ValidationError({"professional_qualifications.shift_preference": "Shift preference is required."})

        contact_info = data.get('contact_info', {})
        if contact_info:
            if not contact_info.get('address'):
                raise serializers.ValidationError({"contact_info.address": "Address is required."})
            if not contact_info.get('city'):
                raise serializers.ValidationError({"contact_info.city": "City is required."})
            if not contact_info.get('region'):
                raise serializers.ValidationError({"contact_info.region": "Region is required."})
            if not contact_info.get('country'):
                raise serializers.ValidationError({"contact_info.country": "Country is required."})
            if not contact_info.get('emergency_contact'):
                raise serializers.ValidationError({"contact_info.emergency_contact": "Emergency contact is required."})
            if not contact_info.get('emergency_phone'):
                raise serializers.ValidationError({"contact_info.emergency_phone": "Emergency phone is required."})

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
        
        # Extract nested data and remove them from validated_data to avoid unknown field errors
        nested_validated_data = {}
        for key, _, serializer_class in nested_data:
            nested_payload = validated_data.pop(key, None)  # remove from validated_data
            if nested_payload is not None:
                serializer = serializer_class(data=nested_payload)
                serializer.is_valid(raise_exception=True)
                nested_validated_data[key] = serializer.validated_data
            else:
                nested_validated_data[key] = {}

        if Profile.objects.filter(user=user).exists():
            raise serializers.ValidationError({"error": "A profile already exists for this user."})

        try:
            with transaction.atomic():
                # Create the profile
                profile = Profile.objects.create(user=user, **validated_data)
                
                # Create nested objects
                for key, model, _ in nested_data:
                    if nested_validated_data[key]:
                        model.objects.create(profile=profile, **nested_validated_data[key])
                
                return profile
        except (ValueError, IntegrityError) as e:
            raise serializers.ValidationError({
                "error": str(e) if isinstance(e, ValueError) else "A profile already exists for this user or a database constraint was violated."
            })

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