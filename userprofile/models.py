# from django.db import models
# # from django.contrib.auth.models import User
# from django.core.validators import FileExtensionValidator
# from django.contrib.auth import get_user_model
# User = get_user_model()
# class Profile(models.Model):
#     id = models.AutoField(primary_key=True)  # Add id as primary key
#     user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
#     name = models.CharField(max_length=100, blank=False)
#     birthdate = models.DateField(null=True, blank=True)
#     weight = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
#     height = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
#     profession = models.CharField(max_length=100, blank=False)
#     location = models.CharField(max_length=100, blank=True)
#     gender = models.CharField(max_length=20, blank=True)
#     hair_color = models.CharField(max_length=50, blank=True)
#     eye_color = models.CharField(max_length=50, blank=True)
#     body_type = models.CharField(max_length=50, blank=True)
#     has_driving_license = models.BooleanField(default=False)
#     video = models.FileField(
#         upload_to='profile_videos/',
#         null=True,
#         blank=True,
#         validators=[FileExtensionValidator(allowed_extensions=['mp4', 'avi', 'mov', 'mkv'])]
#     )
#     photo = models.ImageField(
#         upload_to='profile_photos/',
#         null=True,
#         blank=True,
#         validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif'])]
#     )
#     created_at = models.DateTimeField(auto_now_add=True)
#     experience_level = models.CharField(max_length=50, blank=True)
#     skills = models.JSONField(default=list)
#     nationality = models.CharField(max_length=50, blank=True)
#     availability = models.CharField(max_length=50, blank=True)
#     education_level = models.CharField(max_length=50, blank=True)
#     languages = models.JSONField(default=list)
#     min_salary = models.IntegerField(null=True, blank=True)
#     max_salary = models.IntegerField(null=True, blank=True)
#     work_authorization = models.CharField(max_length=100, blank=True)
#     industry_experience = models.CharField(max_length=100, blank=True)
#     marital_status = models.CharField(max_length=50, blank=True)
#     ethnicity = models.CharField(max_length=50, blank=True)
#     disability_status = models.CharField(max_length=50, blank=True)
#     disability_type = models.CharField(max_length=50, blank=True, default="None")
#     landmark = models.CharField(max_length=100, blank=True)
#     availability_status = models.BooleanField(default=True)
#     health_conditions = models.JSONField(default=list)
#     medications = models.JSONField(default=list)
#     social_media_links = models.JSONField(default=dict)
#     years_of_experience = models.CharField(max_length=50, blank=True)
#     employment_status = models.CharField(max_length=50, blank=True)
#     previous_employers = models.JSONField(default=list)
#     projects = models.JSONField(default=list)
#     training = models.JSONField(default=list)
#     internship_experience = models.CharField(max_length=50, blank=True)
#     degree_type = models.CharField(max_length=50, blank=True)
#     field_of_study = models.CharField(max_length=100, blank=True)
#     certifications = models.JSONField(default=list)
#     online_courses = models.JSONField(default=list)
#     preferred_work_location = models.CharField(max_length=50, blank=True)
#     shift_preference = models.CharField(max_length=50, blank=True)
#     willingness_to_relocate = models.CharField(max_length=50, blank=True)
#     overtime_availability = models.CharField(max_length=50, blank=True)
#     travel_willingness = models.CharField(max_length=50, blank=True)
#     software_proficiency = models.JSONField(default=list)
#     typing_speed = models.IntegerField(null=True, blank=True)
#     driving_skills = models.CharField(max_length=100, blank=True)
#     equipment_experience = models.JSONField(default=list)
#     personality_type = models.CharField(max_length=50, blank=True)
#     work_preference = models.CharField(max_length=50, blank=True)
#     hobbies = models.JSONField(default=list)
#     volunteer_experience = models.CharField(max_length=50, blank=True)
#     company_culture_preference = models.CharField(max_length=100, blank=True)
#     id_type = models.CharField(max_length=50, blank=True)
#     id_number = models.CharField(max_length=50, blank=True)
#     id_expiry_date = models.DateField(null=True, blank=True)
#     id_front = models.ImageField(
#         upload_to='id_fronts/',
#         null=True,
#         blank=True,
#         validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif'])]
#     )
#     id_back = models.ImageField(
#         upload_to='id_backs/',
#         null=True,
#         blank=True,
#         validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif'])]
#     )
#     id_verified = models.BooleanField(default=False)
#     residence_type = models.CharField(max_length=50, blank=True)
#     address = models.CharField(max_length=200, blank=True)
#     city = models.CharField(max_length=100, blank=True)
#     region = models.CharField(max_length=100, blank=True)
#     postal_code = models.CharField(max_length=20, blank=True)
#     residence_duration = models.CharField(max_length=50, blank=True)
#     housing_status = models.CharField(max_length=50, blank=True)
#     emergency_contact = models.CharField(max_length=100, blank=True)
#     emergency_phone = models.CharField(max_length=20, blank=True)
#     skin_tone = models.CharField(max_length=50, blank=True)
#     facial_hair = models.CharField(max_length=50, blank=True)
#     tattoos_visible = models.BooleanField(default=False)
#     piercings_visible = models.BooleanField(default=False)
#     physical_condition = models.CharField(max_length=50, blank=True)
#     role_title = models.CharField(max_length=100, blank=True)
#     portfolio_url = models.URLField(blank=True, null=True)
#     social_media_handles = models.JSONField(default=list)
#     union_membership = models.CharField(max_length=100, blank=True)
#     reference = models.JSONField(default=list)
#     available_start_date = models.DateField(null=True, blank=True)
#     graduation_year = models.CharField(max_length=4, blank=True)
#     gpa = models.FloatField(null=True, blank=True)
#     institution_name = models.CharField(max_length=100, blank=True)
#     scholarships = models.JSONField(default=list)
#     academic_achievements = models.JSONField(default=list)
#     language_proficiency = models.JSONField(default=list)
#     special_skills = models.JSONField(default=list)
#     tools_experience = models.JSONField(default=list)
#     award_recognitions = models.JSONField(default=list)
#     preferred_company_size = models.CharField(max_length=50, blank=True)
#     preferred_industry = models.JSONField(default=list)
#     leadership_style = models.CharField(max_length=50, blank=True)
#     communication_style = models.CharField(max_length=50, blank=True)
#     motivation = models.CharField(max_length=100, blank=True)
#     verified = models.BooleanField(default=False)
#     flagged = models.BooleanField(default=False)
#     status = models.CharField(max_length=50, blank=True)
#
#     def save(self, *args, **kwargs):
#         if not self.name or self.name.strip() == "":
#             raise ValueError("Name cannot be blank.")
#         if not self.profession or self.profession.strip() == "":
#             raise ValueError("Profession cannot be blank.")
#         super().save(*args, **kwargs)
#
#     def __str__(self):
#         return self.name or f"Profile of {self.user.username}"
#
#     @property
#     def age(self):
#         if self.birthdate:
#             from datetime import date
#             today = date.today()
#             age = today.year - self.birthdate.year
#             if today.month < self.birthdate.month or (today.month == self.birthdate.month and today.day < self.birthdate.day):
#                 age -= 1
#             return age
#         return None
from django.db import models
from django.core.validators import FileExtensionValidator, MinValueValidator
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
import re
from django.core.validators import RegexValidator

User = get_user_model()
class Profile(models.Model):
    id = models.AutoField(primary_key=True)  # Add id as primary key
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    name = models.CharField(max_length=100, blank=False)
    birthdate = models.DateField(null=True, blank=True)
    weight = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    height = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    profession = models.CharField(max_length=100, blank=False)
    location = models.CharField(max_length=100, blank=True)
    gender = models.CharField(max_length=20, blank=True)
    hair_color = models.CharField(max_length=50, blank=True)
    eye_color = models.CharField(max_length=50, blank=True)
    body_type = models.CharField(max_length=50, blank=True)
    has_driving_license = models.BooleanField(default=False)
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
    created_at = models.DateTimeField(auto_now_add=True)
    experience_level = models.CharField(max_length=50, blank=True)
    skills = models.JSONField(default=list)
    nationality = models.CharField(max_length=50, blank=True)
    availability = models.CharField(max_length=50, blank=True)
    education_level = models.CharField(max_length=50, blank=True)
    languages = models.JSONField(default=list)
    min_salary = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(0)])
    max_salary = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(0)])
    work_authorization = models.CharField(max_length=100, blank=True)
    industry_experience = models.CharField(max_length=100, blank=True)
    marital_status = models.CharField(max_length=50, blank=True)
    ethnicity = models.CharField(max_length=50, blank=True)
    disability_status = models.CharField(max_length=50, blank=True)
    disability_type = models.CharField(max_length=50, blank=True, default="None")
    landmark = models.CharField(max_length=100, blank=True)
    availability_status = models.BooleanField(default=True)
    health_conditions = models.JSONField(default=list)
    medications = models.JSONField(default=list)
    social_media_links = models.JSONField(default=dict)
    years_of_experience = models.CharField(max_length=50, blank=True)
    employment_status = models.CharField(max_length=50, blank=True)
    previous_employers = models.JSONField(default=list)
    projects = models.JSONField(default=list)
    training = models.JSONField(default=list)
    internship_experience = models.CharField(max_length=50, blank=True)
    degree_type = models.CharField(max_length=50, blank=True)
    field_of_study = models.CharField(max_length=100, blank=True)
    certifications = models.JSONField(default=list)
    online_courses = models.JSONField(default=list)
    preferred_work_location = models.CharField(max_length=50, blank=True)
    shift_preference = models.CharField(max_length=50, blank=True)
    willingness_to_relocate = models.CharField(max_length=50, blank=True)
    overtime_availability = models.CharField(max_length=50, blank=True)
    travel_willingness = models.CharField(max_length=50, blank=True)
    software_proficiency = models.JSONField(default=list)
    typing_speed = models.IntegerField(null=True, blank=True)
    driving_skills = models.CharField(max_length=100, blank=True)
    equipment_experience = models.JSONField(default=list)
    personality_type = models.CharField(max_length=50, blank=True)
    work_preference = models.CharField(max_length=50, blank=True)
    hobbies = models.JSONField(default=list)
    volunteer_experience = models.CharField(max_length=50, blank=True)
    company_culture_preference = models.CharField(max_length=100, blank=True)
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
    residence_type = models.CharField(max_length=50, blank=True)
    address = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=100, blank=True)
    region = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    residence_duration = models.CharField(max_length=50, blank=True)
    housing_status = models.CharField(max_length=50, blank=True)
    emergency_contact = models.CharField(max_length=100, blank=True)
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )

    emergency_phone = models.CharField(validators=[phone_regex], max_length=17, blank=True)
    skin_tone = models.CharField(max_length=50, blank=True)
    facial_hair = models.CharField(max_length=50, blank=True)
    tattoos_visible = models.BooleanField(default=False)
    piercings_visible = models.BooleanField(default=False)
    physical_condition = models.CharField(max_length=50, blank=True)
    role_title = models.CharField(max_length=100, blank=True)
    portfolio_url = models.URLField(blank=True, null=True)
    social_media_handles = models.JSONField(default=list)
    union_membership = models.CharField(max_length=100, blank=True)
    reference = models.JSONField(default=list)
    available_start_date = models.DateField(null=True, blank=True)
    graduation_year = models.CharField(max_length=4, blank=True)
    gpa = models.FloatField(null=True, blank=True)
    institution_name = models.CharField(max_length=100, blank=True)
    scholarships = models.JSONField(default=list)
    academic_achievements = models.JSONField(default=list)
    language_proficiency = models.JSONField(default=list)
    special_skills = models.JSONField(default=list)
    tools_experience = models.JSONField(default=list)
    award_recognitions = models.JSONField(default=list)
    preferred_company_size = models.CharField(max_length=50, blank=True)
    preferred_industry = models.JSONField(default=list)
    leadership_style = models.CharField(max_length=50, blank=True)
    communication_style = models.CharField(max_length=50, blank=True)
    motivation = models.CharField(max_length=100, blank=True)
    verified = models.BooleanField(default=False)
    flagged = models.BooleanField(default=False)
    status = models.CharField(max_length=50, blank=True)

    def clean(self):
        """
        Validate id_number based on id_type.
        Raises ValidationError if id_number format does not match the selected id_type.
        For Kebele ID, only checks if id_number is non-empty.
        """
        if self.id_type and self.id_number:  # Only validate if both fields are provided
            if self.id_type == 'kebele_id':
                # Kebele ID: Only check if non-empty
                if not self.id_number.strip():
                    raise ValidationError({
                        'id_number': 'Kebele ID must not be empty.'
                    })
            elif self.id_type == 'national_id':
                # National ID (Fayda ID): Must be exactly 12 digits
                if not re.match(r'^\d{12}$', self.id_number):
                    raise ValidationError({
                        'id_number': 'National ID must be exactly 12 digits.'
                    })
            elif self.id_type == 'passport':
                # Passport: Starts with 'E' or 'EP' followed by 7-8 digits
                if not re.match(r'^E[P]?\d{7,8}$', self.id_number):
                    raise ValidationError({
                        'id_number': 'Passport must start with "E" or "EP" followed by 7-8 digits.'
                    })
            elif self.id_type == 'drivers_license':
                # Driver’s License: Alphanumeric, non-empty, max 50 characters
                if not re.match(r'^[A-Za-z0-9]+$', self.id_number):
                    raise ValidationError({
                        'id_number': 'Driver’s License must contain only letters and numbers.'
                    })
        elif self.id_type and not self.id_number:
            raise ValidationError({
                'id_number': f'{self.id_type} requires a valid ID number.'
            })
        elif self.id_number and not self.id_type:
            raise ValidationError({
                'id_type': 'ID type must be specified when providing an ID number.'
            })

        # Validate that min_salary is not greater than max_salary
        if self.min_salary is not None and self.max_salary is not None:
            if self.min_salary > self.max_salary:
                raise ValidationError({
                    'min_salary': 'Minimum salary cannot be greater than maximum salary.'
                })

    def save(self, *args, **kwargs):
        if not self.name or self.name.strip() == "":
            raise ValueError("Name cannot be blank.")
        if not self.profession or self.profession.strip() == "":
            raise ValueError("Profession cannot be blank.")
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name or f"Profile of {self.user.username}"

    @property
    def age(self):
        if self.birthdate:
            from datetime import date
            today = date.today()
            age = today.year - self.birthdate.year
            if today.month < self.birthdate.month or (today.month == self.birthdate.month and today.day < self.birthdate.day):
                age -= 1
            return age
        return None
