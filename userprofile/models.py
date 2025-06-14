from django.db import models
from django.core.validators import FileExtensionValidator, MinValueValidator, RegexValidator, MaxValueValidator
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
import re
from datetime import date
import bleach
import os
import json
from django.conf import settings
from PIL import Image, ExifTags
from django.core.files.storage import default_storage
from django.utils import timezone
import logging
from datetime import timedelta
from django.contrib.postgres.fields import ArrayField

User = get_user_model()

logger = logging.getLogger(__name__)

def get_array_field():
    """Returns the appropriate field type based on the database backend"""
    if settings.DATABASES['default']['ENGINE'] == 'django.db.backends.postgresql':
        return ArrayField(models.CharField(max_length=20), default=list, blank=True)
    return models.JSONField(default=list, blank=True)

# Choice Constants
HOUSING_STATUS_CHOICES = [
    ('owned', 'Owned'),
    ('rented', 'Rented'),
    ('living_with_family', 'Living with Family'),
    ('other', 'Other')
]

RESIDENCE_DURATION_CHOICES = [
    ('less_than_1_year', 'Less than 1 year'),
    ('1_to_3_years', '1 to 3 years'),
    ('3_to_5_years', '3 to 5 years'),
    ('more_than_5_years', 'More than 5 years')
]

# Helper function to sanitize strings (same as in serializers.py)
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

class Profile(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    name = models.CharField(max_length=100, blank=True)
    birthdate = models.DateField(null=True, blank=True, help_text="Date of birth (required)")
    profession = models.CharField(max_length=50)
    nationality = models.CharField(
        max_length=100,
        help_text="Nationality (required)"
    )
    location = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    availability_status = models.BooleanField(default=True)
    verified = models.BooleanField(default=False)
    flagged = models.BooleanField(default=False)
    status = models.CharField(max_length=50, blank=True)

    def clean(self):
        # Sanitize string fields
        if self.name:
            self.name = sanitize_string(self.name)
        if self.profession:
            self.profession = sanitize_string(self.profession)
        if self.nationality:
            self.nationality = sanitize_string(self.nationality)
        if self.location:
            self.location = sanitize_string(self.location)
        if self.status:
            self.status = sanitize_string(self.status)

        # Validate profession
        try:
            profession_choices = ProfessionChoices.objects.first()
            if profession_choices:
                valid_professions = [choice['code'] for choice in profession_choices.choices]
                if self.profession not in valid_professions:
                    raise ValidationError({
                        'profession': f'Invalid profession selected. Please choose from: {", ".join(valid_professions)}'
                    })
        except Exception as e:
            raise ValidationError({
                'profession': 'Error validating profession. Please try again.'
            })

        # Validate nationality
        try:
            nationality_choices = NationalityChoices.objects.first()
            if nationality_choices:
                valid_nationalities = [choice['code'] for choice in nationality_choices.choices]
                if self.nationality not in valid_nationalities:
                    raise ValidationError({
                        'nationality': f'Invalid nationality selected. Please choose from: {", ".join(valid_nationalities)}'
                    })
        except Exception as e:
            raise ValidationError({
                'nationality': 'Error validating nationality. Please try again.'
            })

        # Existing validations
        if self.birthdate:
            if self.birthdate > date.today():
                raise ValidationError({
                    'birthdate': 'Birthdate cannot be in the future.'
                })
            # Calculate age
            age = (date.today() - self.birthdate).days // 365
            if age < 18:
                raise ValidationError({
                    'birthdate': 'Must be at least 18 years old.'
                })
            if age > 100:
                raise ValidationError({
                    'birthdate': 'Age cannot exceed 100 years.'
                })

        if not self.location:
            raise ValidationError("Location is required.")

    def save(self, *args, **kwargs):
        if not self.birthdate:
            raise ValidationError("Date of birth is required.")
        if not self.nationality:
            raise ValidationError("Nationality is required.")
        if not self.profession:
            raise ValidationError("Profession is required.")
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name or f"Profile of {self.user.username}"

    @property
    def age(self):
        if self.birthdate:
            today = date.today()
            age = today.year - self.birthdate.year
            if today.month < self.birthdate.month or (today.month == self.birthdate.month and today.day < self.birthdate.day):
                age -= 1
            return age
        return None

class IdentityVerification(models.Model):
    profile = models.OneToOneField(Profile, on_delete=models.CASCADE, related_name='identity_verification')
    id_type = models.CharField(
        max_length=50,
        help_text="Type of identification document"
    )
    id_number = models.CharField(max_length=50, blank=True)
    id_expiry_date = models.DateField(null=True, blank=True)
    id_front = models.ImageField(
        upload_to='id_fronts/',
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif'])],
        help_text="Front photo of ID document (required)",
        null=True,
        blank=True
    )
    id_back = models.ImageField(
        upload_to='id_backs/',
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif'])],
        help_text="Back photo of ID document (required)",
        null=True,
        blank=True
    )
    id_verified = models.BooleanField(default=False)

    def clean(self):
        # Sanitize id_type
        if self.id_type:
            self.id_type = sanitize_string(self.id_type)

        # Validate id_type
        id_type_choices = IDTypeChoices.objects.first()
        if id_type_choices:
            valid_types = [choice['code'] for choice in id_type_choices.choices]
            if self.id_type not in valid_types:
                raise ValidationError({'id_type': f'Invalid ID type. Choose from: {", ".join(valid_types)}'})

    def save(self, *args, **kwargs):
        if not self.id_type:
            raise ValidationError("ID type is required.")
        super().save(*args, **kwargs)

class ProfessionalQualifications(models.Model):
    profile = models.OneToOneField(Profile, on_delete=models.CASCADE, related_name='professional_qualifications')
    professions = models.JSONField(
        default=list,
        help_text="Selected professions (minimum 1 required)"
    )
    actor_category = models.CharField(
        max_length=50,
        blank=True,
        help_text="Category of acting experience"
    )
    model_categories = models.JSONField(
        default=list,
        help_text="Selected model categories"
    )
    performer_categories = models.JSONField(
        default=list,
        help_text="Selected performer categories"
    )
    influencer_categories = models.JSONField(
        default=list,
        help_text="Selected influencer categories"
    )
    min_salary = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Minimum expected salary"
    )
    max_salary = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Maximum expected salary"
    )
    skills = models.JSONField(
        default=list,
        help_text="Selected skills"
    )
    skill_description = models.TextField(
        blank=True,
        help_text="Detailed description of skills (required for Stuntman)"
    )
    video_url = models.URLField(
        blank=True,
        help_text="URL to showcase video (required for Stuntman)"
    )
    main_skill = models.CharField(
        max_length=50,
        blank=True,
        help_text="Primary skill (required for stuntman)"
    )
    experience_level = models.CharField(
        max_length=50,
        help_text="Experience level (required)"
    )
    years_of_experience = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Years of experience (required)"
    )
    availability = models.CharField(
        max_length=50,
        help_text="Availability (required)"
    )
    employment_status = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Employment status (required)"
    )
    preferred_work_location = models.CharField(
        max_length=50,
        help_text="Preferred work location (required)"
    )
    shift_preference = models.CharField(
        max_length=50,
        help_text="Shift preference (required)"
    )
    willingness_to_relocate = models.BooleanField(default=False)
    overtime_availability = models.BooleanField(default=False)
    travel_willingness = models.BooleanField(default=False)
    software_proficiency = models.JSONField(default=list)
    typing_speed = models.IntegerField(null=True, blank=True)
    driving_skills = models.BooleanField(default=False)
    equipment_experience = models.JSONField(default=list)
    role_title = models.CharField(max_length=100)
    portfolio_url = models.URLField(blank=True, null=True)
    union_membership = models.BooleanField(default=False)
    reference = models.TextField(blank=True, null=True)
    available_start_date = models.DateField(null=True, blank=True)
    preferred_company_size = models.CharField(
        max_length=50,
        help_text="Preferred company size"
    )
    preferred_industry = models.CharField(
        max_length=50,
        help_text="Preferred industry"
    )
    leadership_style = models.CharField(
        max_length=50,
        help_text="Leadership style"
    )
    communication_style = models.CharField(
        max_length=50,
        help_text="Communication style"
    )
    motivation = models.CharField(
        max_length=50,
        help_text="Motivation"
    )
    has_driving_license = models.BooleanField(default=False)
    work_authorization = models.CharField(max_length=50)

    def clean(self):
        # Sanitize string fields
        if self.actor_category:
            self.actor_category = sanitize_string(self.actor_category)
        if self.skill_description:
            self.skill_description = sanitize_string(self.skill_description)
        if self.main_skill:
            self.main_skill = sanitize_string(self.main_skill)
        if self.experience_level:
            self.experience_level = sanitize_string(self.experience_level)
        if self.years_of_experience:
            self.years_of_experience = sanitize_string(self.years_of_experience)
        if self.availability:
            self.availability = sanitize_string(self.availability)
        if self.employment_status:
            self.employment_status = sanitize_string(self.employment_status)
        if self.preferred_work_location:
            self.preferred_work_location = sanitize_string(self.preferred_work_location)
        if self.shift_preference:
            self.shift_preference = sanitize_string(self.shift_preference)

        # Validate experience_level
        experience_level_choices = ExperienceLevelChoices.objects.first()
        if experience_level_choices:
            valid_levels = [choice['code'] for choice in experience_level_choices.choices]
            if self.experience_level not in valid_levels:
                raise ValidationError({'experience_level': f'Invalid experience level. Choose from: {", ".join(valid_levels)}'})

        # Validate years_of_experience
        years_choices = YearsChoices.objects.first()
        if years_choices:
            valid_years = [choice['code'] for choice in years_choices.choices]
            if self.years_of_experience and self.years_of_experience not in valid_years:
                raise ValidationError({'years_of_experience': f'Invalid years of experience. Choose from: {", ".join(valid_years)}'})

        # Validate availability
        availability_choices = AvailabilityChoices.objects.first()
        if availability_choices:
            valid_availability = [choice['code'] for choice in availability_choices.choices]
            if self.availability not in valid_availability:
                raise ValidationError({'availability': f'Invalid availability. Choose from: {", ".join(valid_availability)}'})

        # Validate employment_status
        employment_status_choices = EmploymentStatusChoices.objects.first()
        if employment_status_choices:
            valid_statuses = [choice['code'] for choice in employment_status_choices.choices]
            if self.employment_status and self.employment_status not in valid_statuses:
                raise ValidationError({'employment_status': f'Invalid employment status. Choose from: {", ".join(valid_statuses)}'})

        # Validate preferred_work_location
        work_location_choices = WorkLocationChoices.objects.first()
        if work_location_choices:
            valid_locations = [choice['code'] for choice in work_location_choices.choices]
            if self.preferred_work_location not in valid_locations:
                raise ValidationError({'preferred_work_location': f'Invalid work location. Choose from: {", ".join(valid_locations)}'})

        # Validate shift_preference
        shift_choices = ShiftChoices.objects.first()
        if shift_choices:
            valid_shifts = [choice['code'] for choice in shift_choices.choices]
            if self.shift_preference not in valid_shifts:
                raise ValidationError({'shift_preference': f'Invalid shift preference. Choose from: {", ".join(valid_shifts)}'})

    def save(self, *args, **kwargs):
        # Validate that at least one professional qualification is provided
        if not self.professions:
            raise ValidationError("At least one profession is required.")
        if not self.experience_level:
            raise ValidationError("Experience level is required.")
        if not self.availability:
            raise ValidationError("Availability is required.")
        if not self.preferred_work_location:
            raise ValidationError("Preferred work location is required.")
        if not self.shift_preference:
            raise ValidationError("Shift preference is required.")
        super().save(*args, **kwargs)

class PhysicalAttributes(models.Model):
    profile = models.OneToOneField(Profile, on_delete=models.CASCADE, related_name='physical_attributes')
    weight = models.DecimalField(
        max_digits=5, 
        decimal_places=1, 
        help_text="Weight in kilograms (required)",
        null=False,
        blank=False,
        default=30,
        validators=[
            MinValueValidator(30, message="Weight must be at least 30 kg"),
            MaxValueValidator(500, message="Weight cannot exceed 500 kg")
        ]
    )
    height = models.DecimalField(
        max_digits=5, 
        decimal_places=1, 
        help_text="Height in centimeters (required)",
        null=False,
        blank=False,
        default=100,
        validators=[
            MinValueValidator(100, message="Height must be at least 100 cm"),
            MaxValueValidator(300, message="Height cannot exceed 300 cm")
        ]
    )
    gender = models.CharField(
        max_length=20,
        help_text="Gender (required)"
    )
    hair_color = models.CharField(
        max_length=50,
        help_text="Hair color (required)"
    )
    eye_color = models.CharField(
        max_length=50,
        help_text="Eye color (required)"
    )
    body_type = models.CharField(
        max_length=50,
        help_text="Body type (required)"
    )
    skin_tone = models.CharField(
        max_length=50,
        help_text="Skin tone (required)"
    )
    facial_hair = models.CharField(max_length=50, blank=True)
    tattoos_visible = models.BooleanField(default=False)
    piercings_visible = models.BooleanField(default=False)
    physical_condition = models.CharField(max_length=50, blank=True)

    def clean(self):
        # Sanitize string fields
        if self.gender:
            self.gender = sanitize_string(self.gender)
        if self.hair_color:
            self.hair_color = sanitize_string(self.hair_color)
        if self.eye_color:
            self.eye_color = sanitize_string(self.eye_color)
        if self.body_type:
            self.body_type = sanitize_string(self.body_type)
        if self.skin_tone:
            self.skin_tone = sanitize_string(self.skin_tone)
        if self.facial_hair:
            self.facial_hair = sanitize_string(self.facial_hair)
        if self.physical_condition:
            self.physical_condition = sanitize_string(self.physical_condition)
        # Validate gender
        gender_choices = GenderChoices.objects.first()
        if gender_choices:
            valid_genders = [choice['code'] for choice in gender_choices.choices]
            if self.gender not in valid_genders:
                raise ValidationError({'gender': f'Invalid gender. Choose from: {", ".join(valid_genders)}'})

        # Existing validations
        if self.height is not None:
            if self.height < 100:  # Minimum height 100 cm
                raise ValidationError({
                    'height': 'Height must be at least 100 cm.'
                })
        if self.weight is not None:
            if self.weight < 30:  # Minimum weight 30 kg
                raise ValidationError({
                    'weight': 'Weight must be at least 30 kg.'
                })

    def save(self, *args, **kwargs):
        if self.weight is None:
            raise ValidationError("Weight is required.")
        if self.height is None:
            raise ValidationError("Height is required.")
        if not self.gender:
            raise ValidationError("Gender is required.")
        if not self.hair_color:
            raise ValidationError("Hair color is required.")
        if not self.eye_color:
            raise ValidationError("Eye color is required.")
        if not self.body_type:
            raise ValidationError("Body type is required.")
        if not self.skin_tone:
            raise ValidationError("Skin tone is required.")
        super().save(*args, **kwargs)

class MedicalInfo(models.Model):
    profile = models.OneToOneField(Profile, on_delete=models.CASCADE, related_name='medical_info')
    health_conditions = models.JSONField(
        default=list,
        help_text="List of health conditions (required)"
    )
    medications = models.JSONField(
        default=list,
        help_text="List of medications (required)"
    )
    disability_status = models.CharField(max_length=50, blank=True)
    disability_type = models.CharField(max_length=50, blank=True, default="None")

    def clean(self):
        # Sanitize string fields
        if self.disability_status:
            self.disability_status = sanitize_string(self.disability_status)
        if self.disability_type:
            self.disability_type = sanitize_string(self.disability_type)

    def save(self, *args, **kwargs):
        if not self.health_conditions:
            raise ValidationError("At least one health condition is required.")
        if not self.medications:
            raise ValidationError("At least one medication is required.")
        super().save(*args, **kwargs)

class Education(models.Model):
    profile = models.OneToOneField(Profile, on_delete=models.CASCADE, related_name='education')
    education_level = models.CharField(max_length=50, blank=True)
    degree_type = models.CharField(max_length=50, blank=True)
    field_of_study = models.CharField(max_length=100, blank=True)
    graduation_year = models.CharField(max_length=4, blank=True)
    gpa = models.FloatField(null=True, blank=True)
    institution_name = models.CharField(max_length=100, blank=True)
    scholarships = models.JSONField(default=list)
    academic_achievements = models.JSONField(default=list)
    certifications = models.JSONField(default=list)
    online_courses = models.JSONField(default=list)

    def clean(self):
        # Sanitize string fields
        if self.education_level:
            self.education_level = sanitize_string(self.education_level)
        if self.degree_type:
            self.degree_type = sanitize_string(self.degree_type)
        if self.field_of_study:
            self.field_of_study = sanitize_string(self.field_of_study)
        if self.graduation_year:
            self.graduation_year = sanitize_string(self.graduation_year)
        if self.institution_name:
            self.institution_name = sanitize_string(self.institution_name)

class WorkExperience(models.Model):
    profile = models.OneToOneField(Profile, on_delete=models.CASCADE, related_name='work_experience')
    years_of_experience = models.CharField(max_length=50, blank=True)
    employment_status = models.CharField(max_length=50, blank=True)
    previous_employers = models.JSONField(default=list)
    projects = models.JSONField(default=list)
    training = models.JSONField(default=list)
    internship_experience = models.CharField(max_length=50, blank=True)

    def clean(self):
        # Sanitize string fields
        if self.years_of_experience:
            self.years_of_experience = sanitize_string(self.years_of_experience)
        if self.employment_status:
            self.employment_status = sanitize_string(self.employment_status)
        if self.internship_experience:
            self.internship_experience = sanitize_string(self.internship_experience)

class ContactInfo(models.Model):
    profile = models.OneToOneField(Profile, on_delete=models.CASCADE, related_name='contact_info')
    address = models.CharField(max_length=255)
    specific_area = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    region = models.CharField(max_length=100)
    country = models.CharField(max_length=2)
    housing_status = models.CharField(max_length=50, choices=HOUSING_STATUS_CHOICES)
    residence_duration = models.CharField(max_length=50, choices=RESIDENCE_DURATION_CHOICES)
    emergency_contact = models.CharField(max_length=100)
    emergency_phone = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.profile.user.username}'s Contact Info"

    def get_country_choices(self):
        try:
            with open(os.path.join(settings.BASE_DIR, 'userprofile', 'data', 'countries.json'), 'r') as f:
                countries_data = json.load(f)
                return countries_data['countries']
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def clean(self):
        if self.region and self.city:
            try:
                # Case-insensitive region lookup
                location_data = LocationData.objects.get(region_id__iexact=self.region)
                # Case-insensitive city validation
                valid_cities = {city['id'].lower(): city['name'] for city in location_data.cities}
                if self.city.lower() not in valid_cities:
                    raise ValidationError({
                        'city': f'Invalid city for the selected region. Please choose from: {", ".join(valid_cities.values())}'
                    })
            except LocationData.DoesNotExist:
                raise ValidationError({
                    'region': 'Invalid region selected.'
                })

        if self.country:
            try:
                with open(os.path.join(settings.BASE_DIR, 'userprofile', 'data', 'countries.json'), 'r') as f:
                    countries_data = json.load(f)
                    valid_countries = {country['id'].lower(): country['name'] for country in countries_data['countries']}
                    if self.country.lower() not in valid_countries:
                        raise ValidationError({
                            'country': f'Invalid country selected. Please choose from: {", ".join(valid_countries.values())}'
                        })
            except (FileNotFoundError, json.JSONDecodeError):
                raise ValidationError({
                    'country': 'Error validating country. Please try again.'
                })

        if self.housing_status:
            valid_statuses = {status[0].lower(): status[1] for status in HOUSING_STATUS_CHOICES}
            if self.housing_status.lower() not in valid_statuses:
                raise ValidationError({
                    'housing_status': f'Invalid housing status. Please choose from: {", ".join(valid_statuses.values())}'
                })

        if self.residence_duration:
            valid_durations = {duration[0].lower(): duration[1] for duration in RESIDENCE_DURATION_CHOICES}
            if self.residence_duration.lower() not in valid_durations:
                raise ValidationError({
                    'residence_duration': f'Invalid residence duration. Please choose from: {", ".join(valid_durations.values())}'
                })

class PersonalInfo(models.Model):
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ]
    MARITAL_STATUS_CHOICES = [
        ('single', 'Single'),
        ('married', 'Married'),
        ('divorced', 'Divorced'),
        ('widowed', 'Widowed'),
    ]
    ID_TYPE_CHOICES = [
        ('passport', 'Passport'),
        ('national_id', 'National ID'),
        ('drivers_license', 'Driver\'s License'),
    ]
    LANGUAGE_CHOICES = [
        ('english', 'English'),
        ('amharic', 'Amharic'),
        ('oromo', 'Oromo'),
        ('tigrinya', 'Tigrinya'),
        ('somali', 'Somali'),
        ('afar', 'Afar'),
        ('other', 'Other'),
    ]
    HOBBY_CHOICES = [
        ('reading', 'Reading'),
        ('sports', 'Sports'),
        ('music', 'Music'),
        ('travel', 'Travel'),
        ('cooking', 'Cooking'),
        ('photography', 'Photography'),
        ('art', 'Art'),
        ('dancing', 'Dancing'),
        ('gaming', 'Gaming'),
        ('fitness', 'Fitness'),
        ('other', 'Other'),
    ]
    SOCIAL_MEDIA_CHOICES = [
        ('facebook', 'Facebook'),
        ('instagram', 'Instagram'),
        ('twitter', 'Twitter'),
        ('linkedin', 'LinkedIn'),
        ('tiktok', 'TikTok'),
        ('youtube', 'YouTube'),
        ('other', 'Other'),
    ]

    profile = models.OneToOneField(Profile, on_delete=models.CASCADE, related_name='personal_info')
    first_name = models.CharField(max_length=100, null=True, blank=True)
    last_name = models.CharField(max_length=100, null=True, blank=True)
    date_of_birth = models.DateField(null=False, blank=False)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, null=False, blank=False)
    marital_status = models.CharField(max_length=20, choices=MARITAL_STATUS_CHOICES, null=False, blank=False)
    nationality = models.CharField(max_length=100, null=False, blank=False)
    id_type = models.CharField(max_length=20, choices=ID_TYPE_CHOICES, null=False, blank=False)
    id_number = models.CharField(max_length=50, null=False, blank=False)
    hobbies = models.JSONField(default=list, null=False, blank=False)
    language_proficiency = models.JSONField(default=list, null=False, blank=False)
    social_media = models.JSONField(default=dict, null=False, blank=False)
    custom_hobby = models.CharField(max_length=100, blank=False, null=False, default='')
    custom_language = models.CharField(max_length=100, blank=True, null=True)
    custom_social_media = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    class Meta:
        verbose_name = "Personal Information"
        verbose_name_plural = "Personal Information"

    def save(self, *args, **kwargs):
        if not self.first_name:
            raise ValidationError("First name is required.")
        if not self.last_name:
            raise ValidationError("Last name is required.")
        if not self.date_of_birth:
            raise ValidationError("Date of birth is required.")
        if not self.gender:
            raise ValidationError("Gender is required.")
        if not self.marital_status:
            raise ValidationError("Marital status is required.")
        if not self.nationality:
            raise ValidationError("Nationality is required.")
        if not self.id_type:
            raise ValidationError("ID type is required.")
        if not self.id_number:
            raise ValidationError("ID number is required.")
        if not self.hobbies:
            raise ValidationError("At least one hobby is required.")
        if not self.language_proficiency:
            raise ValidationError("At least one language proficiency is required.")
        if not self.social_media:
            raise ValidationError("At least one social media account is required.")
        super().save(*args, **kwargs)

class Media(models.Model):
    profile = models.OneToOneField(Profile, on_delete=models.CASCADE, related_name='media')
    video = models.FileField(
        upload_to='profile_videos/',
        null=True,
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['mp4', 'avi', 'mov', 'mkv'])]
    )
    photo = models.ImageField(
        upload_to='profile_photos/',
        validators=[
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png']),
            MinValueValidator(800, message="Image width must be at least 800 pixels"),
            MaxValueValidator(2000, message="Image width must not exceed 2000 pixels")
        ],
        help_text="Professional headshot (required). Must be JPG/PNG format, minimum 800px width, maximum 2000px width.",
        blank=True,
        null=True
    )
    natural_photo_1 = models.ImageField(
        upload_to='natural_photos/',
        null=True,
        blank=True,
        validators=[
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png']),
            MinValueValidator(800, message="Image width must be at least 800 pixels"),
            MaxValueValidator(2000, message="Image width must not exceed 2000 pixels")
        ],
        help_text="First natural photo (required). Must be JPG/PNG format, minimum 800px width, maximum 2000px width."
    )
    natural_photo_2 = models.ImageField(
        upload_to='natural_photos/',
        null=True,
        blank=True,
        validators=[
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png']),
            MinValueValidator(800, message="Image width must be at least 800 pixels"),
            MaxValueValidator(2000, message="Image width must not exceed 2000px width")
        ],
        help_text="Second natural photo (required). Must be JPG/PNG format, minimum 800px width, maximum 2000px width."
    )
    photo_processed = models.BooleanField(default=False)
    natural_photo_1_processed = models.BooleanField(default=False)
    natural_photo_2_processed = models.BooleanField(default=False)
    last_cleanup = models.DateTimeField(null=True, blank=True)

    def _process_image(self, image_field, field_name):
        """Process image: resize, optimize, and add watermark if needed"""
        try:
            # Open image
            img = Image.open(image_field)
            
            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            
            # Resize if needed while maintaining aspect ratio
            if img.width > 2000:
                ratio = 2000 / img.width
                new_size = (2000, int(img.height * ratio))
                img = img.resize(new_size, Image.Resampling.LANCZOS)
            
            # Optimize image
            if img.format == 'JPEG':
                img.save(image_field.path, 'JPEG', quality=85, optimize=True)
            elif img.format == 'PNG':
                img.save(image_field.path, 'PNG', optimize=True)
            
            # Update processed flag
            setattr(self, f'{field_name}_processed', True)
            
            return True
        except Exception as e:
            logger.error(f"Error processing image {field_name}: {str(e)}")
            return False

    def _validate_image(self, image, field_name):
        """Enhanced image validation including metadata and content checks"""
        try:
            # Basic validation
            img = Image.open(image)
            width, height = img.size
            
            # Check dimensions
            if width < 800 or width > 2000:
                raise ValidationError({
                    field_name: f'Image width must be between 800 and 2000 pixels. Current width: {width}px'
                })
            
            # Check aspect ratio
            aspect_ratio = width / height
            if not (0.6 <= aspect_ratio <= 0.8):
                raise ValidationError({
                    field_name: 'Image aspect ratio should be approximately 3:4.'
                })
            
            # Check file size
            if image.size > 5 * 1024 * 1024:
                raise ValidationError({
                    field_name: 'Image file size must not exceed 5MB.'
                })
            
            # Check image quality
            if img.format == 'JPEG':
                quality = img.info.get('quality', 0)
                if quality < 80:
                    raise ValidationError({
                        field_name: 'Image quality must be at least 80%.'
                    })
            
            # Check metadata
            try:
                exif = img._getexif()
                if exif:
                    for tag_id in exif:
                        tag = ExifTags.TAGS.get(tag_id, tag_id)
                        if tag in ['DateTime', 'DateTimeOriginal', 'DateTimeDigitized']:
                            # Check if image is too old (e.g., more than 5 years)
                            image_date = exif[tag_id]
                            if isinstance(image_date, str):
                                from datetime import datetime
                                try:
                                    image_date = datetime.strptime(image_date, '%Y:%m:%d %H:%M:%S')
                                    if image_date < (timezone.now() - timedelta(days=5*365)):
                                        raise ValidationError({
                                            field_name: 'Image appears to be more than 5 years old. Please provide a recent photo.'
                                        })
                                except ValueError:
                                    pass
            except Exception as e:
                logger.warning(f"Error reading EXIF data: {str(e)}")
            
            return True
        except Exception as e:
            logger.error(f"Error validating image {field_name}: {str(e)}")
            raise ValidationError({
                field_name: f'Error validating image: {str(e)}'
            })

    def clean(self):
        """Validate all images before saving"""
        # Validate headshot
        if self.photo:
            self._validate_image(self.photo, 'photo')
        
        # Validate natural photos
        if self.natural_photo_1:
            self._validate_image(self.natural_photo_1, 'natural_photo_1')
        else:
            raise ValidationError({
                'natural_photo_1': 'First natural photo is required.'
            })
            
        if self.natural_photo_2:
            self._validate_image(self.natural_photo_2, 'natural_photo_2')
        else:
            raise ValidationError({
                'natural_photo_2': 'Second natural photo is required.'
            })

    def save(self, *args, **kwargs):
        """Process and save images"""
        self.clean()
        
        # Process images if not already processed
        if self.photo and not self.photo_processed:
            self._process_image(self.photo, 'photo')
        
        if self.natural_photo_1 and not self.natural_photo_1_processed:
            self._process_image(self.natural_photo_1, 'natural_photo_1')
        
        if self.natural_photo_2 and not self.natural_photo_2_processed:
            self._process_image(self.natural_photo_2, 'natural_photo_2')
        
        # Cleanup old files if needed
        self._cleanup_old_files()
        
        super().save(*args, **kwargs)

    def _cleanup_old_files(self):
        """Clean up old and unused files"""
        if self.last_cleanup and (timezone.now() - self.last_cleanup) < timedelta(days=1):
            return  # Only cleanup once per day
        
        try:
            # Get all media directories
            media_dirs = ['profile_photos/', 'natural_photos/', 'profile_videos/']
            
            for directory in media_dirs:
                # List all files in directory
                files = default_storage.listdir(directory)[1]
                
                for file in files:
                    file_path = os.path.join(directory, file)
                    
                    # Check if file is older than 30 days
                    try:
                        file_stat = default_storage.stat(file_path)
                        file_time = timezone.datetime.fromtimestamp(file_stat.st_mtime)
                        
                        if (timezone.now() - file_time) > timedelta(days=30):
                            # Check if file is not associated with any profile
                            if not Media.objects.filter(
                                photo=file_path
                            ).exists() and not Media.objects.filter(
                                natural_photo_1=file_path
                            ).exists() and not Media.objects.filter(
                                natural_photo_2=file_path
                            ).exists():
                                # Delete the file
                                default_storage.delete(file_path)
                                logger.info(f"Deleted old file: {file_path}")
                    except Exception as e:
                        logger.error(f"Error processing file {file_path}: {str(e)}")
            
            self.last_cleanup = timezone.now()
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")

    def delete(self, *args, **kwargs):
        """Clean up files when model is deleted"""
        try:
            # Delete associated files
            if self.photo:
                default_storage.delete(self.photo.path)
            if self.natural_photo_1:
                default_storage.delete(self.natural_photo_1.path)
            if self.natural_photo_2:
                default_storage.delete(self.natural_photo_2.path)
            if self.video:
                default_storage.delete(self.video.path)
        except Exception as e:
            logger.error(f"Error deleting files: {str(e)}")
        
        super().delete(*args, **kwargs)

class VerificationStatus(models.Model):
    profile = models.OneToOneField(Profile, on_delete=models.CASCADE, related_name='verification_status')
    is_verified = models.BooleanField(default=False)
    verification_type = models.CharField(max_length=50)  # e.g., 'id', 'address', 'phone'
    verification_date = models.DateTimeField(auto_now_add=True)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    verification_method = models.CharField(max_length=50)  # e.g., 'document', 'phone_call', 'email'
    verification_notes = models.TextField(blank=True)
    last_updated = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if self.is_verified:
            # Create audit log
            VerificationAuditLog.objects.create(
                profile=self.profile,
                previous_status=False,
                new_status=True,
                changed_by=self.verified_by,
                verification_type=self.verification_type,
                verification_method=self.verification_method,
                notes=self.verification_notes
            )
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Verification Status for {self.profile.name}"

class VerificationAuditLog(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='verification_logs')
    previous_status = models.BooleanField()
    new_status = models.BooleanField()
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    changed_at = models.DateTimeField(auto_now_add=True)
    verification_type = models.CharField(max_length=50)
    verification_method = models.CharField(max_length=50)
    notes = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True)
    user_agent = models.TextField(blank=True)

    class Meta:
        ordering = ['-changed_at']
        verbose_name = 'Verification Audit Log'
        verbose_name_plural = 'Verification Audit Logs'

    def __str__(self):
        return f"Verification Log for {self.profile.name} at {self.changed_at}"

class LocationData(models.Model):
    region_id = models.CharField(max_length=50, unique=True)
    region_name = models.CharField(max_length=100)
    cities = models.JSONField()

    def __str__(self):
        return self.region_name

    class Meta:
        verbose_name = "Location Data"
        verbose_name_plural = "Location Data"

class ChoiceData(models.Model):
    choice_type = models.CharField(max_length=50, unique=True)
    choices = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.choice_type} Choices"

    class Meta:
        verbose_name = 'Choice Data'
        verbose_name_plural = 'Choice Data'

class ProfessionalChoices(models.Model):
    company_sizes = models.JSONField(default=list)
    industries = models.JSONField(default=list)
    leadership_styles = models.JSONField(default=list)
    communication_styles = models.JSONField(default=list)
    motivations = models.JSONField(default=list)

    class Meta:
        verbose_name = 'Professional Choices'
        verbose_name_plural = 'Professional Choices'

    def __str__(self):
        return "Professional Choices"

class GenderChoices(models.Model):
    choices = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "Gender Choices"

class MaritalStatusChoices(models.Model):
    choices = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "Marital Status Choices"

class HousingStatusChoices(models.Model):
    choices = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "Housing Status Choices"

class DurationChoices(models.Model):
    choices = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "Duration Choices"

class IDTypeChoices(models.Model):
    choices = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "ID Type Choices"

class ActorCategoryChoices(models.Model):
    choices = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "Actor Category Choices"

class SkillsChoices(models.Model):
    choices = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "Skills Choices"

class ExperienceLevelChoices(models.Model):
    choices = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "Experience Level Choices"

class YearsChoices(models.Model):
    choices = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "Years Choices"

class AvailabilityChoices(models.Model):
    choices = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "Availability Choices"

class EmploymentStatusChoices(models.Model):
    choices = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "Employment Status Choices"

class WorkLocationChoices(models.Model):
    choices = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "Work Location Choices"

class ShiftChoices(models.Model):
    choices = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "Shift Choices"

class NationalityChoices(models.Model):
    choices = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "Nationality Choices"