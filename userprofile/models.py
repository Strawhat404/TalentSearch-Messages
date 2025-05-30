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
    ID_TYPE_CHOICES = [
        ('kebele_id', 'Kebele ID'),
        ('national_id', 'National ID'),
        ('passport', 'Passport'),
        ('driving_license', 'Driving License')
    ]

    profile = models.OneToOneField(Profile, on_delete=models.CASCADE, related_name='identity_verification')
    id_type = models.CharField(
        max_length=50,
        choices=ID_TYPE_CHOICES,
        help_text="Type of identification document"
    )
    id_number = models.CharField(max_length=50, blank=True)
    id_expiry_date = models.DateField(null=True, blank=True)
    id_front = models.ImageField(
        upload_to='id_fronts/',
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif'])],
        help_text="Front photo of ID document"
    )
    id_back = models.ImageField(
        upload_to='id_backs/',
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif'])],
        help_text="Back photo of ID document"
    )
    id_verified = models.BooleanField(default=False)

    def clean(self):
        # Sanitize id_type
        if self.id_type:
            self.id_type = sanitize_string(self.id_type)

        # Validate ID number based on type
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
            elif self.id_type == 'driving_license':
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

    def save(self, *args, **kwargs):
        if not self.id_front:
            raise ValidationError("Front photo of ID is required.")
        if not self.id_back:
            raise ValidationError("Back photo of ID is required.")
        super().save(*args, **kwargs)

class ProfessionalQualifications(models.Model):
    ACTOR_CATEGORY_CHOICES = [
        ('amateur', 'Amateur'),
        ('professional', 'Professional'),
        ('stage', 'Stage'),
        ('screen', 'Screen')
    ]

    PROFESSION_CHOICES = [
        ('actor', 'Actor'),
        ('model', 'Model'),
        ('performer', 'Performer'),
        ('host', 'Host'),
        ('influencer', 'Influencer'),
        ('voice_over', 'Voice Over'),
        ('cameraman', 'Cameraman'),
        ('presenter', 'Presenter'),
        ('stuntman', 'Stuntman')
    ]

    EXPERIENCE_LEVEL_CHOICES = [
        ('entry', 'Entry'),
        ('mid_level', 'Mid-Level'),
        ('senior', 'Senior')
    ]

    YEARS_CHOICES = [
        ('0_1', '0-1'),
        ('1_3', '1-3'),
        ('3_5', '3-5'),
        ('5_plus', '5+')
    ]

    AVAILABILITY_CHOICES = [
        ('part_time', 'Part-Time'),
        ('full_time', 'Full-Time'),
        ('contract', 'Contract'),
        ('freelance', 'Freelance')
    ]

    EMPLOYMENT_STATUS_CHOICES = [
        ('unemployed', 'Unemployed'),
        ('employed', 'Employed'),
        ('freelancer', 'Freelancer')
    ]

    WORK_LOCATION_CHOICES = [
        ('hybrid', 'Hybrid'),
        ('onsite', 'Onsite'),
        ('remote', 'Remote')
    ]

    SHIFT_CHOICES = [
        ('day', 'Day'),
        ('night', 'Night'),
        ('rotational', 'Rotational')
    ]

    WORK_AUTHORIZATION_CHOICES = [
        ('authorized', 'Authorized'),
        ('unauthorized', 'Unauthorized')
    ]

    profile = models.OneToOneField(Profile, on_delete=models.CASCADE, related_name='professional_qualifications')
    professions = models.JSONField(
        default=list,
        help_text="Selected professions (minimum 1 required)"
    )
    actor_category = models.CharField(
        max_length=50,
        choices=ACTOR_CATEGORY_CHOICES,
        blank=True,
        help_text="Category of acting experience"
    )
    # New fields for multi-select categories
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
        choices=EXPERIENCE_LEVEL_CHOICES,
        help_text="Experience level (required)"
    )
    years_of_experience = models.CharField(
        max_length=50,
        choices=YEARS_CHOICES,
        help_text="Years of experience (required)"
    )
    availability = models.CharField(
        max_length=50,
        choices=AVAILABILITY_CHOICES,
        help_text="Availability (required)"
    )
    employment_status = models.CharField(
        max_length=50,
        choices=EMPLOYMENT_STATUS_CHOICES,
        help_text="Employment status (required)"
    )
    preferred_work_location = models.CharField(
        max_length=50,
        choices=WORK_LOCATION_CHOICES,
        help_text="Preferred work location (required)"
    )
    shift_preference = models.CharField(
        max_length=50,
        choices=SHIFT_CHOICES,
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
    preferred_company_size = models.CharField(max_length=50, choices=COMPANY_SIZE_CHOICES)
    preferred_industry = models.CharField(max_length=50, choices=INDUSTRY_CHOICES)
    leadership_style = models.CharField(max_length=50, choices=LEADERSHIP_STYLE_CHOICES)
    communication_style = models.CharField(max_length=50, choices=COMMUNICATION_STYLE_CHOICES)
    motivation = models.CharField(max_length=50, choices=MOTIVATION_CHOICES)
    has_driving_license = models.BooleanField(default=False)
    work_authorization = models.CharField(max_length=50, choices=WORK_AUTHORIZATION_CHOICES)

    # New and updated fields
    skill_videos_url = models.JSONField(
        default=list,
        help_text="URLs of skill videos (optional)"
    )
    experience_description = models.TextField(
        blank=True,
        help_text="Detailed description of experience (optional)"
    )
    industry_experience = models.TextField(
        blank=True,
        help_text="Description of industry experience (optional)"
    )
    previous_employers = models.JSONField(
        default=list,
        help_text="List of previous employers (optional)"
    )
    training_workshops = models.JSONField(
        default=list,
        help_text="List of training and workshops (optional)"
    )
    certifications = models.JSONField(
        default=list,
        help_text="List of certifications (optional)"
    )
    min_salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    max_salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    video_links = models.JSONField(
        default=list,
        help_text="Video links (required for Voice Over)"
    )

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

        # Validate that at least one profession is selected
        if not self.professions or len(self.professions) < 1:
            raise ValidationError({
                'professions': 'At least one profession must be selected.'
            })

        # Validate that all selected professions are valid
        valid_professions = [choice[0] for choice in self.PROFESSION_CHOICES]
        for profession in self.professions:
            if profession not in valid_professions:
                raise ValidationError({
                    'professions': f'Invalid profession selected: {profession}'
                })

        # Validate that at least one professional qualification is provided
        has_skills = bool(self.skills and len(self.skills) > 0)
        has_software = bool(self.software_proficiency and len(self.software_proficiency) > 0)
        has_equipment = bool(self.equipment_experience and len(self.equipment_experience) > 0)
        has_role = bool(self.role_title and self.role_title.strip())
        has_industry = bool(self.industry_experience and self.industry_experience.strip())
        has_experience = bool(self.experience_level and self.experience_level.strip())

        if not any([has_skills, has_software, has_equipment, has_role, has_industry, has_experience]):
            raise ValidationError(
                "At least one of the following must be provided: skills, software proficiency, "
                "equipment experience, role title, industry experience, or experience level."
            )

        # Validate required experience fields
        if not self.experience_level:
            raise ValidationError({
                'experience_level': 'Experience level is required.'
            })
        if not self.years_of_experience:
            raise ValidationError({
                'years_of_experience': 'Years of experience is required.'
            })
        if not self.availability:
            raise ValidationError({
                'availability': 'Availability is required.'
            })
        if not self.employment_status:
            raise ValidationError({
                'employment_status': 'Employment status is required.'
            })
        if not self.preferred_work_location:
            raise ValidationError({
                'preferred_work_location': 'Preferred work location is required.'
            })
        if not self.shift_preference:
            raise ValidationError({
                'shift_preference': 'Shift preference is required.'
            })

        # Sanitize new fields
        if self.experience_description:
            self.experience_description = sanitize_string(self.experience_description)
        if self.industry_experience:
            self.industry_experience = sanitize_string(self.industry_experience)
        if self.union_membership:
            self.union_membership = sanitize_string(self.union_membership)

        # Validate portfolio URL for Cameraman
        if 'cameraman' in self.professions and not self.portfolio_url:
            raise ValidationError({
                'portfolio_url': 'Portfolio URL is required for Cameraman'
            })

        # Validate video links for Voice Over
        if 'voice_over' in self.professions and not self.video_links:
            raise ValidationError({
                'video_links': 'Video links are required for Voice Over'
            })

        # Validate salary range
        if self.min_salary is not None and self.max_salary is not None:
            if self.min_salary > self.max_salary:
                raise ValidationError({
                    'min_salary': 'Minimum salary cannot be greater than maximum salary.'
                })

        # Validate that all selected categories exist in their respective JSON files
        try:
            with open(os.path.join(settings.BASE_DIR, 'userprofile', 'data', 'model_categories.json'), 'r') as f:
                valid_model_categories = [cat['id'] for cat in json.load(f)['model_categories']]
                for category in self.model_categories:
                    if category not in valid_model_categories:
                        raise ValidationError({
                            'model_categories': f'Invalid model category: {category}'
                        })
        except (FileNotFoundError, json.JSONDecodeError):
            pass

        try:
            with open(os.path.join(settings.BASE_DIR, 'userprofile', 'data', 'performer_categories.json'), 'r') as f:
                valid_performer_categories = [cat['id'] for cat in json.load(f)['performer_categories']]
                for category in self.performer_categories:
                    if category not in valid_performer_categories:
                        raise ValidationError({
                            'performer_categories': f'Invalid performer category: {category}'
                        })
        except (FileNotFoundError, json.JSONDecodeError):
            pass

        try:
            with open(os.path.join(settings.BASE_DIR, 'userprofile', 'data', 'influencer_categories.json'), 'r') as f:
                valid_influencer_categories = [cat['id'] for cat in json.load(f)['influencer_categories']]
                for category in self.influencer_categories:
                    if category not in valid_influencer_categories:
                        raise ValidationError({
                            'influencer_categories': f'Invalid influencer category: {category}'
                        })
        except (FileNotFoundError, json.JSONDecodeError):
            pass

        try:
            with open(os.path.join(settings.BASE_DIR, 'userprofile', 'data', 'skills.json'), 'r') as f:
                valid_skills = [skill['id'] for skill in json.load(f)['skills']]
                for skill in self.skills:
                    if skill not in valid_skills:
                        raise ValidationError({
                            'skills': f'Invalid skill: {skill}'
                        })
        except (FileNotFoundError, json.JSONDecodeError):
            pass

    def save(self, *args, **kwargs):
        # Validate that at least one professional qualification is provided
        has_skills = bool(self.skills and len(self.skills) > 0)
        has_software = bool(self.software_proficiency and len(self.software_proficiency) > 0)
        has_equipment = bool(self.equipment_experience and len(self.equipment_experience) > 0)
        has_role = bool(self.role_title and self.role_title.strip())
        has_industry = bool(self.industry_experience and self.industry_experience.strip())
        has_experience = bool(self.experience_level and self.experience_level.strip())

        if not any([has_skills, has_software, has_equipment, has_role, has_industry, has_experience]):
            raise ValidationError(
                "At least one of the following must be provided: skills, software proficiency, "
                "equipment experience, role title, industry experience, or experience level."
            )
        super().save(*args, **kwargs)

class PhysicalAttributes(models.Model):
    profile = models.OneToOneField(Profile, on_delete=models.CASCADE, related_name='physical_attributes')
    weight = models.DecimalField(
        max_digits=5, 
        decimal_places=1, 
        null=True,
        blank=True,
        help_text="Weight in kilograms (required)"
    )
    height = models.DecimalField(
        max_digits=5, 
        decimal_places=1, 
        null=True,
        blank=True,
        help_text="Height in centimeters (required)"
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

    def __str__(self):
        return f"{self.profile.user.username}'s Contact Info"

class PersonalInfo(models.Model):
    SOCIAL_MEDIA_CHOICES = [
        ('instagram', 'Instagram'),
        ('facebook', 'Facebook'),
        ('youtube', 'YouTube'),
        ('tiktok', 'TikTok'),
        ('twitter', 'Twitter'),
        ('linkedin', 'LinkedIn'),
        ('snapchat', 'Snapchat'),
        ('pinterest', 'Pinterest'),
        ('other', 'Other')
    ]

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
    social_media = models.JSONField(
        default=list,
        help_text="List of social media accounts with usernames and followers"
    )
    other_social_media = models.JSONField(
        default=list,
        help_text="List of other social media platforms not in the predefined list"
    )
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

        # Validate social media data
        if not self.social_media and not self.other_social_media:
            raise ValidationError({
                'social_media': 'At least one social media account is required.'
            })

        # Validate social media structure
        for platform in self.social_media:
            if not isinstance(platform, dict):
                raise ValidationError({
                    'social_media': 'Invalid social media data structure.'
                })
            
            required_fields = ['platform', 'username', 'followers']
            for field in required_fields:
                if field not in platform:
                    raise ValidationError({
                        'social_media': f'Missing required field: {field}'
                    })
            
            if platform['platform'] not in [choice[0] for choice in self.SOCIAL_MEDIA_CHOICES]:
                raise ValidationError({
                    'social_media': f'Invalid platform: {platform["platform"]}'
                })
            
            if not isinstance(platform['followers'], (int, str)) or not str(platform['followers']).isdigit():
                raise ValidationError({
                    'social_media': 'Followers must be a number'
                })

        # Validate other social media structure
        for platform in self.other_social_media:
            if not isinstance(platform, dict):
                raise ValidationError({
                    'other_social_media': 'Invalid social media data structure.'
                })
            
            required_fields = ['platform_name', 'username', 'followers']
            for field in required_fields:
                if field not in platform:
                    raise ValidationError({
                        'other_social_media': f'Missing required field: {field}'
                    })
            
            if not isinstance(platform['followers'], (int, str)) or not str(platform['followers']).isdigit():
                raise ValidationError({
                    'other_social_media': 'Followers must be a number'
                })

    def save(self, *args, **kwargs):
        # Ensure at least one social media account exists
        if not self.social_media and not self.other_social_media:
            raise ValidationError("At least one social media account is required.")
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