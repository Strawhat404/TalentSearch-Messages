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

User = get_user_model()

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
    name = models.CharField(max_length=100)
    birthdate = models.DateField(null=True, blank=True, help_text="Date of birth (required)")
    profession = models.CharField(max_length=100)
    nationality = models.CharField(max_length=50)
    location = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
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

    def save(self, *args, **kwargs):
        if not self.birthdate:
            raise ValidationError("Date of birth is required.")
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
    id_type = models.CharField(max_length=50, blank=True)
    id_number = models.CharField(max_length=50, blank=True)
    id_expiry_date = models.DateField(null=True, blank=True)
    id_front = models.ImageField(
        upload_to='id_fronts/',
        null=True,
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif'])]
    )
    id_back = models.ImageField(
        upload_to='id_backs/',
        null=True,
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif'])]
    )
    id_verified = models.BooleanField(default=False)

    def clean(self):
        # Sanitize id_type (id_number is skipped due to strict regex validation)
        if self.id_type:
            self.id_type = sanitize_string(self.id_type)

        # Existing validation
        if self.id_type and self.id_number:
            if self.id_type == 'kebele_id':
                if not self.id_number.strip():
                    raise ValidationError({
                        'id_number': 'Kebele ID must not be empty.'
                    })
            elif self.id_type == 'national_id':
                if not re.match(r'^\d{12}$', self.id_number):
                    raise ValidationError({
                        'id_number': 'National ID must be exactly 12 digits.'
                    })
            elif self.id_type == 'passport':
                if not re.match(r'^E[P]?\d{7,8}$', self.id_number):
                    raise ValidationError({
                        'id_number': 'Passport must start with "E" or "EP" followed by 7-8 digits.'
                    })
            elif self.id_type == 'drivers_license':
                if not re.match(r'^[A-Za-z0-9]+$', self.id_number):
                    raise ValidationError({
                        'id_number': "Driver's License must contain only letters and numbers."
                    })
        elif self.id_type and not self.id_number:
            raise ValidationError({
                'id_number': f'{self.id_type} requires a valid ID number.'
            })
        elif self.id_number and not self.id_type:
            raise ValidationError({
                'id_type': 'ID type must be specified when providing an ID number.'
            })
        if self.id_expiry_date and self.id_expiry_date < date.today():
            raise ValidationError({
                'id_expiry_date': 'ID expiry date cannot be in the past.'
            })

class ProfessionalQualifications(models.Model):
    profile = models.OneToOneField(Profile, on_delete=models.CASCADE, related_name='professional_qualifications')
    experience_level = models.CharField(max_length=50, blank=True)
    skills = models.JSONField(default=list)
    work_authorization = models.CharField(max_length=100, blank=True)
    industry_experience = models.CharField(max_length=100, blank=True)
    min_salary = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(0)])
    max_salary = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(0)])
    availability = models.CharField(max_length=50, blank=True)
    preferred_work_location = models.CharField(max_length=50, blank=True)
    shift_preference = models.CharField(max_length=50, blank=True)
    willingness_to_relocate = models.CharField(max_length=50, blank=True)
    overtime_availability = models.CharField(max_length=50, blank=True)
    travel_willingness = models.BooleanField(default=False, help_text="Are you willing to travel?")
    software_proficiency = models.JSONField(default=list)
    typing_speed = models.IntegerField(null=True, blank=True)
    driving_skills = models.CharField(max_length=100, blank=True)
    equipment_experience = models.JSONField(default=list)
    role_title = models.CharField(max_length=100, blank=True)
    portfolio_url = models.URLField(blank=True, null=True)
    union_membership = models.CharField(max_length=100, blank=True)
    reference = models.JSONField(default=list)
    available_start_date = models.DateField(null=True, blank=True)
    preferred_company_size = models.CharField(max_length=50, blank=True)
    preferred_industry = models.JSONField(default=list)
    leadership_style = models.CharField(max_length=50, blank=True)
    communication_style = models.CharField(max_length=50, blank=True)
    motivation = models.CharField(max_length=100, blank=True)
    has_driving_license = models.BooleanField(default=False)

    def clean(self):
        # Sanitize string fields
        if self.experience_level:
            self.experience_level = sanitize_string(self.experience_level)
        if self.work_authorization:
            self.work_authorization = sanitize_string(self.work_authorization)
        if self.industry_experience:
            self.industry_experience = sanitize_string(self.industry_experience)
        if self.availability:
            self.availability = sanitize_string(self.availability)
        if self.preferred_work_location:
            self.preferred_work_location = sanitize_string(self.preferred_work_location)
        if self.shift_preference:
            self.shift_preference = sanitize_string(self.shift_preference)
        if self.willingness_to_relocate:
            self.willingness_to_relocate = sanitize_string(self.willingness_to_relocate)
        if self.overtime_availability:
            self.overtime_availability = sanitize_string(self.overtime_availability)
        if self.driving_skills:
            self.driving_skills = sanitize_string(self.driving_skills)
        if self.role_title:
            self.role_title = sanitize_string(self.role_title)
        if self.union_membership:
            self.union_membership = sanitize_string(self.union_membership)
        if self.preferred_company_size:
            self.preferred_company_size = sanitize_string(self.preferred_company_size)
        if self.leadership_style:
            self.leadership_style = sanitize_string(self.leadership_style)
        if self.communication_style:
            self.communication_style = sanitize_string(self.communication_style)
        if self.motivation:
            self.motivation = sanitize_string(self.motivation)

        # Existing validation
        if self.min_salary is not None and self.max_salary is not None:
            if self.min_salary > self.max_salary:
                raise ValidationError({
                    'min_salary': 'Minimum salary cannot be greater than maximum salary.'
                })

class PhysicalAttributes(models.Model):
    profile = models.OneToOneField(Profile, on_delete=models.CASCADE, related_name='physical_attributes')
    weight = models.DecimalField(
        max_digits=5, 
        decimal_places=1, 
        help_text="Weight in kilograms (required)",
        validators=[
            MinValueValidator(30, message="Weight must be at least 30 kg"),
            MaxValueValidator(500, message="Weight cannot exceed 500 kg")
        ]
    )
    height = models.DecimalField(
        max_digits=5, 
        decimal_places=1, 
        help_text="Height in centimeters (required)",
        validators=[
            MinValueValidator(100, message="Height must be at least 100 cm"),
            MaxValueValidator(300, message="Height cannot exceed 300 cm")
        ]
    )
    gender = models.CharField(max_length=20, blank=True)
    hair_color = models.CharField(max_length=50, blank=True)
    eye_color = models.CharField(max_length=50, blank=True)
    body_type = models.CharField(max_length=50, blank=True)
    skin_tone = models.CharField(max_length=50, blank=True)
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

    def save(self, *args, **kwargs):
        self.full_clean()  # This will call clean() and validate all fields
        super().save(*args, **kwargs)

class MedicalInfo(models.Model):
    profile = models.OneToOneField(Profile, on_delete=models.CASCADE, related_name='medical_info')
    health_conditions = models.JSONField(default=list)
    medications = models.JSONField(default=list)
    disability_status = models.CharField(max_length=50, blank=True)
    disability_type = models.CharField(max_length=50, blank=True, default="None")

    def clean(self):
        # Sanitize string fields
        if self.disability_status:
            self.disability_status = sanitize_string(self.disability_status)
        if self.disability_type:
            self.disability_type = sanitize_string(self.disability_type)

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
    HOUSING_STATUS_CHOICES = [
        ('own', 'Own'),
        ('rent', 'Rent'),
        ('live_with_family', 'Live with Family'),
        ('other', 'Other')
    ]

    DURATION_CHOICES = [
        ('less_than_1', '<1 year'),
        ('1_to_3', '1-3 years'),
        ('3_to_5', '3-5 years'),
        ('5_to_10', '5-10 years'),
        ('more_than_10', '>10 years')
    ]

    profile = models.OneToOneField(Profile, on_delete=models.CASCADE, related_name='contact_info')
    address = models.CharField(max_length=200, help_text="Address (required)")
    specific_area = models.CharField(max_length=200, help_text="Specific area (required)")
    city = models.CharField(max_length=100, help_text="City (required)")
    region = models.CharField(max_length=50, help_text="Region (required)")
    country = models.CharField(max_length=2, help_text="Country (required)")
    housing_status = models.CharField(
        max_length=50,
        choices=HOUSING_STATUS_CHOICES,
        help_text="Housing status (required)"
    )
    residence_duration = models.CharField(
        max_length=50,
        choices=DURATION_CHOICES,
        help_text="Duration of residence (required)"
    )
    emergency_contact = models.CharField(
        max_length=100,
        help_text="Emergency contact name (required)"
    )
    emergency_phone = models.CharField(
        max_length=17,
        help_text="Emergency contact phone number starting with +251 followed by 9 digits (required)",
        validators=[
            RegexValidator(
                regex=r'^\+251\d{9}$',
                message="Phone number must start with +251 followed by exactly 9 digits."
            )
        ]
    )

    def clean(self):
        # Validate city based on selected region
        if self.region and self.city:
            try:
                location_data = LocationData.objects.get(region_id=self.region)
                valid_cities = {city['id']: city['name'] for city in location_data.cities}
                if self.city not in valid_cities:
                    raise ValidationError({
                        'city': f'Invalid city for the selected region. Please choose from: {", ".join(valid_cities.values())}'
                    })
            except LocationData.DoesNotExist:
                raise ValidationError({
                    'region': 'Invalid region selected.'
                })

        # Validate country
        if self.country:
            try:
                with open(os.path.join(settings.BASE_DIR, 'data', 'countries.json'), 'r') as f:
                    countries_data = json.load(f)
                    valid_countries = {country['id']: country['name'] for country in countries_data['countries']}
                    if self.country not in valid_countries:
                        raise ValidationError({
                            'country': f'Invalid country selected. Please choose from: {", ".join(valid_countries.values())}'
                        })
            except (FileNotFoundError, json.JSONDecodeError):
                raise ValidationError({
                    'country': 'Error validating country. Please try again.'
                })

    def save(self, *args, **kwargs):
        if not self.address:
            raise ValidationError("Address is required.")
        if not self.specific_area:
            raise ValidationError("Specific area is required.")
        if not self.city:
            raise ValidationError("City is required.")
        if not self.region:
            raise ValidationError("Region is required.")
        if not self.country:
            raise ValidationError("Country is required.")
        if not self.housing_status:
            raise ValidationError("Housing status is required.")
        if not self.residence_duration:
            raise ValidationError("Duration of residence is required.")
        if not self.emergency_contact:
            raise ValidationError("Emergency contact name is required.")
        if not self.emergency_phone:
            raise ValidationError("Emergency contact phone is required.")
        super().save(*args, **kwargs)

class PersonalInfo(models.Model):
    profile = models.OneToOneField(Profile, on_delete=models.CASCADE, related_name='personal_info')
    marital_status = models.CharField(max_length=50, blank=True)
    ethnicity = models.CharField(max_length=50, blank=True)
    personality_type = models.CharField(max_length=50, blank=True)
    work_preference = models.CharField(max_length=50, blank=True)
    hobbies = models.JSONField(default=list)
    custom_hobby = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Custom hobby (required)"
    )
    volunteer_experience = models.CharField(max_length=50, blank=True)
    company_culture_preference = models.CharField(max_length=100, blank=True)
    social_media_links = models.JSONField(default=dict)
    social_media_handles = models.JSONField(default=list)
    language_proficiency = models.JSONField(default=list)
    special_skills = models.JSONField(default=list)
    tools_experience = models.JSONField(default=list)
    award_recognitions = models.JSONField(default=list)

    def clean(self):
        # Sanitize string fields
        if self.marital_status:
            self.marital_status = sanitize_string(self.marital_status)
        if self.ethnicity:
            self.ethnicity = sanitize_string(self.ethnicity)
        if self.personality_type:
            self.personality_type = sanitize_string(self.personality_type)
        if self.work_preference:
            self.work_preference = sanitize_string(self.work_preference)
        if self.volunteer_experience:
            self.volunteer_experience = sanitize_string(self.volunteer_experience)
        if self.company_culture_preference:
            self.company_culture_preference = sanitize_string(self.company_culture_preference)

        # Existing validations
        if self.custom_hobby:
            # Validate hobby length
            if len(self.custom_hobby.strip()) < 2:
                raise ValidationError({
                    'custom_hobby': 'Custom hobby must be at least 2 characters long.'
                })
            if len(self.custom_hobby.strip()) > 50:
                raise ValidationError({
                    'custom_hobby': 'Custom hobby cannot exceed 50 characters.'
                })
            # Check for duplicate hobbies
            if self.custom_hobby.strip().lower() in [h.lower() for h in self.hobbies]:
                raise ValidationError({
                    'custom_hobby': 'This hobby already exists in your list.'
                })

    def save(self, *args, **kwargs):
        if not self.custom_hobby:
            raise ValidationError("Custom hobby is required.")
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
        null=True,
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif'])]
    )

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
        verbose_name = 'Location Data'
        verbose_name_plural = 'Location Data'