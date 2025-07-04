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

def validate_date_of_birth(value):
    """
    Custom validator for date of birth
    Ensures the person is between 18 and 100 years old
    """
    if value:
        if value > date.today():
            raise ValidationError('Date of birth cannot be in the future.')
        
        age = (date.today() - value).days // 365
        if age < 18:
            raise ValidationError('Must be at least 18 years old.')
        if age > 100:
            raise ValidationError('Age cannot exceed 100 years.')

def get_array_field():
    """Returns the appropriate field type based on the database backend"""
    if settings.DATABASES['default']['ENGINE'] == 'django.db.backends.postgresql':
        return ArrayField(models.CharField(max_length=20), default=list, blank=True)
    return models.JSONField(default=list, blank=True)

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

class CaseInsensitiveCharField(models.CharField):
    """
    A CharField that converts input to lowercase for case-insensitive storage
    """
    def to_python(self, value):
        value = super().to_python(value)
        if value is not None:
            return value.lower()
        return value

    def get_prep_value(self, value):
        value = super().get_prep_value(value)
        if value is not None:
            return value.lower()
        return value

class Profession(models.Model):
    id = models.CharField(max_length=50, primary_key=True)
    name = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Profession"
        verbose_name_plural = "Professions"

class ActorCategory(models.Model):
    id = models.CharField(max_length=50, primary_key=True)
    name = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Actor Category"
        verbose_name_plural = "Actor Categories"

class ModelCategory(models.Model):
    id = models.CharField(max_length=50, primary_key=True)
    name = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Model Category"
        verbose_name_plural = "Model Categories"

class PerformerCategory(models.Model):
    id = models.CharField(max_length=50, primary_key=True)
    name = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Performer Category"
        verbose_name_plural = "Performer Categories"

class InfluencerCategory(models.Model):
    id = models.CharField(max_length=50, primary_key=True)
    name = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Influencer Category"
        verbose_name_plural = "Influencer Categories"

class Skill(models.Model):
    id = models.CharField(max_length=50, primary_key=True)
    name = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Skill"
        verbose_name_plural = "Skills"

class MainSkill(models.Model):
    id = models.CharField(max_length=50, primary_key=True)
    name = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Main Skill"
        verbose_name_plural = "Main Skills"

class Profile(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    availability_status = models.BooleanField(default=True)
    verified = models.BooleanField(default=False)
    flagged = models.BooleanField(default=False)
    status = CaseInsensitiveCharField(max_length=50, blank=True)

    @property
    def name(self):
        """Get name from the related User model"""
        return self.user.name if self.user else ""

    def clean(self):
        # Sanitize string fields (removed name sanitization since it's from User model)
        if self.status:
            self.status = sanitize_string(self.status)

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name or f"Profile of {self.user.username}"

class BasicInformation(models.Model):
    profile = models.OneToOneField(Profile, on_delete=models.CASCADE, related_name='basic_information')
    
    # Populated fields (from JSON data)
    nationality = CaseInsensitiveCharField(max_length=100, null=True, blank=True, help_text="Nationality")
    gender = CaseInsensitiveCharField(max_length=20, null=True, blank=True, help_text="Gender")
    languages = models.JSONField(default=list, null=True, blank=True, help_text="Languages spoken")
    hair_color = CaseInsensitiveCharField(max_length=50, null=True, blank=True, help_text="Hair color")
    eye_color = CaseInsensitiveCharField(max_length=50, null=True, blank=True, help_text="Eye color")
    skin_tone = CaseInsensitiveCharField(max_length=50, null=True, blank=True, help_text="Skin tone")
    body_type = CaseInsensitiveCharField(max_length=50, null=True, blank=True, help_text="Body type")
    medical_condition = models.JSONField(default=list, null=True, blank=True, help_text="Medical conditions")
    medicine_type = models.JSONField(default=list, null=True, blank=True, help_text="Types of medicine")
    marital_status = CaseInsensitiveCharField(max_length=20, null=True, blank=True, help_text="Marital status")
    hobbies = models.JSONField(default=list, null=True, blank=True, help_text="Hobbies")
    
    # Input fields
    date_of_birth = models.DateField(
        null=True, 
        blank=True, 
        help_text="Date of birth (must be between 18-100 years old)",
        validators=[validate_date_of_birth]
    )
    height = models.DecimalField(
        max_digits=5, 
        decimal_places=1, 
        null=True,
        blank=True,
        help_text="Height in centimeters",
        validators=[
            MinValueValidator(100, message="Height must be at least 100 cm"),
            MaxValueValidator(300, message="Height cannot exceed 300 cm")
        ]
    )
    weight = models.DecimalField(
        max_digits=5, 
        decimal_places=1, 
        null=True,
        blank=True,
        help_text="Weight in kilograms",
        validators=[
            MinValueValidator(30, message="Weight must be at least 30 kg"),
            MaxValueValidator(500, message="Weight cannot exceed 500 kg")
        ]
    )
    emergency_contact_name = CaseInsensitiveCharField(max_length=100, null=True, blank=True, help_text="Emergency contact name")
    emergency_contact_phone = models.CharField(
        max_length=20, 
        null=True,
        blank=True,
        help_text="Emergency contact phone (must start with +251)",
        validators=[
            RegexValidator(
                regex=r'^\+251\d{9}$',
                message="Phone number must start with +251 followed by 9 digits"
            )
        ]
    )
    custom_hobby = CaseInsensitiveCharField(max_length=100, blank=True, help_text="Custom hobby")
    
    # Toggle fields
    driving_license = models.BooleanField(default=False, help_text="Has driving license")
    visible_piercings = models.BooleanField(default=False, help_text="Has visible piercings")
    visible_tattoos = models.BooleanField(default=False, help_text="Has visible tattoos")
    willing_to_travel = CaseInsensitiveCharField(
        max_length=3,
        null=True,
        blank=True,
        choices=[('Yes', 'Yes'), ('No', 'No')],
        help_text="Willingness to travel"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        # Sanitize string fields
        if self.nationality:
            self.nationality = sanitize_string(self.nationality)
        if self.gender:
            self.gender = sanitize_string(self.gender)
        if self.hair_color:
            self.hair_color = sanitize_string(self.hair_color)
        if self.eye_color:
            self.eye_color = sanitize_string(self.eye_color)
        if self.skin_tone:
            self.skin_tone = sanitize_string(self.skin_tone)
        if self.body_type:
            self.body_type = sanitize_string(self.body_type)
        if self.marital_status:
            self.marital_status = sanitize_string(self.marital_status)
        if self.emergency_contact_name:
            self.emergency_contact_name = sanitize_string(self.emergency_contact_name)
        if self.custom_hobby:
            self.custom_hobby = sanitize_string(self.custom_hobby)

        # Validate date of birth
        validate_date_of_birth(self.date_of_birth)

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Basic Information for {self.profile.user.username}"

    class Meta:
        verbose_name = "Basic Information"
        verbose_name_plural = "Basic Information"

class LocationInformation(models.Model):
    profile = models.OneToOneField(Profile, on_delete=models.CASCADE, related_name='location_information')
    
    # Populated fields (from JSON data)
    housing_status = CaseInsensitiveCharField(max_length=50, null=True, blank=True, help_text="Housing status")
    region = CaseInsensitiveCharField(max_length=100, null=True, blank=True, help_text="Region")
    duration = CaseInsensitiveCharField(max_length=50, null=True, blank=True, help_text="Duration of residence")
    city = CaseInsensitiveCharField(max_length=100, null=True, blank=True, help_text="City")
    country = models.CharField(max_length=2, null=True, blank=True, help_text="Country code")
    
    # Input fields
    address = CaseInsensitiveCharField(max_length=255, null=True, blank=True, help_text="Full address")
    specific_area = CaseInsensitiveCharField(max_length=100, null=True, blank=True, help_text="Specific area within the city")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        # Sanitize string fields
        if self.housing_status:
            self.housing_status = sanitize_string(self.housing_status)
        if self.region:
            self.region = sanitize_string(self.region)
        if self.duration:
            self.duration = sanitize_string(self.duration)
        if self.city:
            self.city = sanitize_string(self.city)
        if self.country:
            self.country = sanitize_string(self.country)
        if self.address:
            self.address = sanitize_string(self.address)
        if self.specific_area:
            self.specific_area = sanitize_string(self.specific_area)

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Location Information for {self.profile.user.username}"

    class Meta:
        verbose_name = "Location Information"
        verbose_name_plural = "Location Information"

class IdentityVerification(models.Model):
    profile = models.OneToOneField(Profile, on_delete=models.CASCADE, related_name='identity_verification')
    
    # From prepopulated data
    id_type = CaseInsensitiveCharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="Type of identification document (National ID, Passport, Driving License)"
    )
    
    # Input fields
    id_front = models.ImageField(
        upload_to='media/id_fronts/',
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif'])],
        help_text="Front photo of ID document",
        null=True,
        blank=True
    )
    id_back = models.ImageField(
        upload_to='media/id_backs/',
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif'])],
        help_text="Back photo of ID document",
        null=True,
        blank=True
    )
    
    # Additional fields for verification
    id_number = models.CharField(max_length=50, blank=True)
    id_expiry_date = models.DateField(null=True, blank=True)
    id_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        # Sanitize id_type
        if self.id_type:
            self.id_type = sanitize_string(self.id_type)

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Delete associated files
        if self.id_front:
            if os.path.isfile(self.id_front.path):
                os.remove(self.id_front.path)
        if self.id_back:
            if os.path.isfile(self.id_back.path):
                os.remove(self.id_back.path)
        super().delete(*args, **kwargs)

    def __str__(self):
        return f"ID Verification for {self.profile.user.username}"

    class Meta:
        verbose_name = "ID Verification"
        verbose_name_plural = "ID Verification"

class ProfessionsAndSkills(models.Model):
    profile = models.OneToOneField(Profile, on_delete=models.CASCADE, related_name='professions_and_skills')
    
    # Profession checkboxes (input fields)
    is_actor = models.BooleanField(default=False, help_text="Actor profession")
    is_model = models.BooleanField(default=False, help_text="Model profession")
    is_performer = models.BooleanField(default=False, help_text="Performer profession")
    is_host = models.BooleanField(default=False, help_text="Host profession")
    is_influencer = models.BooleanField(default=False, help_text="Influencer profession")
    is_voice_over = models.BooleanField(default=False, help_text="Voice Over profession")
    is_cameraman = models.BooleanField(default=False, help_text="Cameraman profession")
    is_presenter = models.BooleanField(default=False, help_text="Presenter profession")
    is_stuntman = models.BooleanField(default=False, help_text="Stuntman profession")
    
    # From prepopulated data
    professions = models.JSONField(
        default=list,
        help_text="Selected professions"
    )
    actor_category = models.JSONField(
        default=list,
        help_text="Selected actor categories"
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
    skills = models.JSONField(
        default=list,
        help_text="Selected skills"
    )
    main_skill = models.JSONField(
        default=list,
        help_text="Selected main skills"
    )
    
    # Input fields
    skill_description = models.TextField(
        blank=True,
        help_text="Detailed description of skills"
    )
    video_url = models.URLField(
        blank=True,
        help_text="URL to showcase video"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        # Sanitize text fields
        if self.skill_description:
            self.skill_description = sanitize_string(self.skill_description)

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Professions & Skills for {self.profile.user.username}"

    class Meta:
        verbose_name = "Professions & Skills"
        verbose_name_plural = "Professions & Skills"

class Experience(models.Model):
    profile = models.OneToOneField(Profile, on_delete=models.CASCADE, related_name='experience')
    
    # From prepopulated data
    experience_level = models.JSONField(
        default=list,
        help_text="Selected experience levels"
    )
    years = models.JSONField(
        default=list,
        help_text="Selected years of experience"
    )
    availability = models.JSONField(
        default=list,
        help_text="Selected availability options"
    )
    employment_status = models.JSONField(
        default=list,
        help_text="Selected employment statuses"
    )
    work_location = models.JSONField(
        default=list,
        help_text="Selected work locations"
    )
    shift = models.JSONField(
        default=list,
        help_text="Selected shift preferences"
    )
    
    # Input fields
    skill_videos_url = models.JSONField(
        default=list,
        blank=True,
        help_text="List of skill video URLs (not required)"
    )
    experience_description = models.TextField(
        blank=True,
        help_text="Detailed description of experience (not required)"
    )
    industry_experience = models.TextField(
        blank=True,
        help_text="Industry-specific experience details (not required)"
    )
    previous_employers = models.JSONField(
        default=list,
        blank=True,
        help_text="List of previous employers (not required)"
    )
    portfolio_url = models.URLField(
        blank=True,
        help_text="Portfolio URL"
    )
    training_workshops = models.TextField(
        blank=True,
        help_text="Training and workshops attended (not required)"
    )
    union_membership = models.TextField(
        blank=True,
        help_text="Union membership details (not required)"
    )
    certifications = models.JSONField(
        default=list,
        blank=True,
        help_text="List of certifications (not required)"
    )
    salary_range_min = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Minimum salary expectation (not required)"
    )
    salary_range_max = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Maximum salary expectation (not required)"
    )
    video_links = models.JSONField(
        default=list,
        blank=True,
        help_text="List of video links"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        # Sanitize text fields
        if self.experience_description:
            self.experience_description = sanitize_string(self.experience_description)
        if self.industry_experience:
            self.industry_experience = sanitize_string(self.industry_experience)
        if self.training_workshops:
            self.training_workshops = sanitize_string(self.training_workshops)
        if self.union_membership:
            self.union_membership = sanitize_string(self.union_membership)
        
        # Validate salary range
        if self.salary_range_min and self.salary_range_max:
            if self.salary_range_min > self.salary_range_max:
                raise ValidationError({
                    'salary_range_max': 'Maximum salary must be greater than minimum salary.'
                })

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Experience for {self.profile.user.username}"

    class Meta:
        verbose_name = "Experience"
        verbose_name_plural = "Experience"

class SocialMedia(models.Model):
    profile = models.OneToOneField(Profile, on_delete=models.CASCADE, related_name='social_media')
    
    # Input fields
    instagram_username = CaseInsensitiveCharField(max_length=100, blank=True, help_text="Instagram username")
    instagram_followers = models.PositiveIntegerField(default=0, help_text="Instagram followers count")
    facebook_username = CaseInsensitiveCharField(max_length=100, blank=True, help_text="Facebook username")
    facebook_followers = models.PositiveIntegerField(default=0, help_text="Facebook followers count")
    youtube_username = CaseInsensitiveCharField(max_length=100, blank=True, help_text="YouTube username")
    youtube_followers = models.PositiveIntegerField(default=0, help_text="YouTube followers count")
    tiktok_username = CaseInsensitiveCharField(max_length=100, blank=True, help_text="TikTok username")
    tiktok_followers = models.PositiveIntegerField(default=0, help_text="TikTok followers count")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        # Sanitize username fields
        if self.instagram_username:
            self.instagram_username = sanitize_string(self.instagram_username)
        if self.facebook_username:
            self.facebook_username = sanitize_string(self.facebook_username)
        if self.youtube_username:
            self.youtube_username = sanitize_string(self.youtube_username)
        if self.tiktok_username:
            self.tiktok_username = sanitize_string(self.tiktok_username)

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Social Media for {self.profile.user.username}"

    class Meta:
        verbose_name = "Social Media"
        verbose_name_plural = "Social Media"

class Headshot(models.Model):
    profile = models.OneToOneField(Profile, on_delete=models.CASCADE, related_name='headshot')
    
    # Input fields
    professional_headshot = models.ImageField(
        upload_to='media/headshots/',
        validators=[
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])
        ],
        help_text="Professional headshot. Must be JPG/PNG/JPEG format.",
        blank=True,
        null=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        # Validate image if provided
        if self.professional_headshot:
            self._validate_image(self.professional_headshot, 'professional_headshot')

    def _validate_image(self, image, field_name):
        """Validate image format and file size"""
        try:
            img = Image.open(image)
            
            # Check file size
            if image.size > 5 * 1024 * 1024:
                raise ValidationError({
                    field_name: 'Image file size must not exceed 5MB.'
                })
            
            return True
        except Exception as e:
            raise ValidationError({
                field_name: f'Error validating image: {str(e)}'
            })

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Delete associated files
        if self.professional_headshot:
            if os.path.isfile(self.professional_headshot.path):
                os.remove(self.professional_headshot.path)
        super().delete(*args, **kwargs)

    def __str__(self):
        return f"Headshot for {self.profile.user.username}"

    class Meta:
        verbose_name = "Headshot"
        verbose_name_plural = "Headshots"

class VerificationStatus(models.Model):
    profile = models.OneToOneField(Profile, on_delete=models.CASCADE, related_name='verification_status')
    is_verified = models.BooleanField(default=False)
    verification_type = CaseInsensitiveCharField(max_length=50)  # e.g., 'id', 'address', 'phone'
    verification_date = models.DateTimeField(auto_now_add=True)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    verification_method = CaseInsensitiveCharField(max_length=50)  # e.g., 'document', 'phone_call', 'email'
    verification_notes = models.TextField(blank=True)
    last_updated = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Sanitize string fields
        if self.verification_type:
            self.verification_type = sanitize_string(self.verification_type)
        if self.verification_method:
            self.verification_method = sanitize_string(self.verification_method)
        if self.verification_notes:
            self.verification_notes = sanitize_string(self.verification_notes)
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Verification Status for {self.profile.user.username}"

class VerificationAuditLog(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='verification_logs')
    previous_status = models.BooleanField()
    new_status = models.BooleanField()
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    changed_at = models.DateTimeField(auto_now_add=True)
    verification_type = CaseInsensitiveCharField(max_length=50)
    verification_method = CaseInsensitiveCharField(max_length=50)
    notes = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True)
    user_agent = models.TextField(blank=True)

    class Meta:
        ordering = ['-changed_at']
        verbose_name = 'Verification Audit Log'
        verbose_name_plural = 'Verification Audit Logs'

    def __str__(self):
        return f"Verification log for {self.profile.user.username} at {self.changed_at}"

class NaturalPhotos(models.Model):
    profile = models.OneToOneField(Profile, on_delete=models.CASCADE, related_name='natural_photos')
    
    # Input fields
    natural_photo_1 = models.ImageField(
        upload_to='media/natural_photos/',
        validators=[
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])
        ],
        help_text="First natural photo. Must be JPG/PNG/JPEG format.",
        blank=True,
        null=True
    )
    natural_photo_2 = models.ImageField(
        upload_to='media/natural_photos/',
        validators=[
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])
        ],
        help_text="Second natural photo. Must be JPG/PNG/JPEG format.",
        blank=True,
        null=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        # Validate images if provided
        if self.natural_photo_1:
            self._validate_image(self.natural_photo_1, 'natural_photo_1')
        if self.natural_photo_2:
            self._validate_image(self.natural_photo_2, 'natural_photo_2')

    def _validate_image(self, image, field_name):
        """Validate image format and file size"""
        try:
            with Image.open(image) as img:
                # Check image format
                if img.format not in ['JPEG', 'PNG']:
                    raise ValidationError(f"{field_name} must be in JPEG or PNG format.")
                
                # Check file size (5MB limit)
                if image.size > 5 * 1024 * 1024:
                    raise ValidationError(f"{field_name} file size must not exceed 5MB.")
                
        except Exception as e:
            if isinstance(e, ValidationError):
                raise e
            raise ValidationError(f"Invalid {field_name} image format.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Delete associated files
        if self.natural_photo_1:
            if os.path.isfile(self.natural_photo_1.path):
                os.remove(self.natural_photo_1.path)
        if self.natural_photo_2:
            if os.path.isfile(self.natural_photo_2.path):
                os.remove(self.natural_photo_2.path)
        super().delete(*args, **kwargs)

    def __str__(self):
        return f"Natural Photos for {self.profile.user.username}"

    class Meta:
        verbose_name = "Natural Photos"
        verbose_name_plural = "Natural Photos"