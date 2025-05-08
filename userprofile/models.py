from django.db import models
from django.conf import settings
from django.utils import timezone
from dateutil.relativedelta import relativedelta

class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    name = models.CharField(max_length=255, help_text="Full name of the user")
    birthdate = models.DateField(null=True, blank=True, help_text="User's date of birth")
    weight = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="User's weight in kg"
    )
    height = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="User's height in cm"
    )
    gender = models.CharField(
        max_length=10,
        choices=[
            ('male', 'Male'),
            ('female', 'Female'),
            ('other', 'Other')
        ],
        null=True,
        blank=True
    )
    nationality = models.CharField(max_length=100, null=True, blank=True)
    languages = models.JSONField(default=list, help_text="List of languages spoken")
    profession = models.CharField(max_length=100, help_text="User's profession")
    skills = models.JSONField(default=list, help_text="List of user's skills")
    interests = models.JSONField(default=list, help_text="List of user's interests")
    bio = models.TextField(blank=True, null=True, help_text="User's biography")
    profile_picture = models.ImageField(
        upload_to='profile_pictures/',
        null=True,
        blank=True
    )
    cover_photo = models.ImageField(
        upload_to='cover_photos/',
        null=True,
        blank=True
    )
    social_links = models.JSONField(
        default=dict,
        help_text="Dictionary of social media links"
    )
    location = models.CharField(max_length=255, null=True, blank=True)
    timezone = models.CharField(max_length=50, null=True, blank=True)
    preferences = models.JSONField(
        default=dict,
        help_text="User preferences and settings"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def age(self):
        if self.birthdate:
            return relativedelta(timezone.now().date(), self.birthdate).years
        return None

    def __str__(self):
        return f"{self.name}'s Profile"

    class Meta:
        ordering = ['-created_at'] 