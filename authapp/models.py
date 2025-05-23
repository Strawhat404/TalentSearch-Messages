from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)

class User(AbstractUser):
    name = models.CharField(max_length=255, default='Unknown User')
    username = None  # Remove the username field
    email = models.EmailField(unique=True)  # Use email as the unique identifier
    last_password_change = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD = 'email'  # Use email as the username field
    REQUIRED_FIELDS = ['name']  # Remove username from required fields

    objects = UserManager()  # Use the custom user manager

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='custom_user_set',  # Change this to a unique name
        blank=True,
        help_text='The groups this user belongs to.',
        related_query_name='user'
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='custom_user_permissions_set',  # Change this to a unique name
        blank=True,
        help_text='Specific permissions for this user.',
        related_query_name='user'
    )

    def set_password(self, raw_password):
        """Set the user's password and update last_password_change timestamp."""
        super().set_password(raw_password)
        self.last_password_change = timezone.now()
        if self.pk:  # Only update specific fields if the user exists
            self.save(update_fields=['last_password_change'])
        else:  # Otherwise save everything
            self.save()

    class Meta:
        db_table = 'auth_user'

class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('info', 'Information'),
        ('warning', 'Warning'),
        ('alert', 'Alert'),
    )
    
    # Maximum lengths for title and message
    MAX_TITLE_LENGTH = 200  # Reasonable length for a notification title
    MAX_MESSAGE_LENGTH = 2000  # Reasonable length for a notification message
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=MAX_TITLE_LENGTH)
    message = models.TextField(max_length=MAX_MESSAGE_LENGTH)
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='info')
    read = models.BooleanField(default=False)
    link = models.URLField(blank=True, null=True, max_length=500)  # Added max_length for URL field
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.title} - {self.user.email}"