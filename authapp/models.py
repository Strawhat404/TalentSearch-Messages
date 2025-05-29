from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid
from django.core.exceptions import ValidationError
import logging

logger = logging.getLogger(__name__)

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
    backup_email = models.EmailField(blank=True, null=True, help_text='Backup email for account recovery')
    phone_number = models.CharField(max_length=20, blank=True, null=True, help_text='Phone number for account recovery')
    last_password_change = models.DateTimeField(default=timezone.now)
    is_locked = models.BooleanField(default=False, help_text='Whether the account is locked due to failed attempts')
    lockout_until = models.DateTimeField(null=True, blank=True, help_text='When the account lockout expires')
    failed_login_attempts = models.IntegerField(default=0, help_text='Number of failed login attempts')
    last_failed_login = models.DateTimeField(null=True, blank=True, help_text='Timestamp of last failed login attempt')

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

class SecurityLog(models.Model):
    """Model to track security-related events"""
    user = models.ForeignKey(
        'User', 
        on_delete=models.CASCADE, 
        related_name='security_logs',
        null=True,  # Make it nullable
        blank=True  # Allow blank in forms
    )
    email = models.EmailField()
    event_type = models.CharField(max_length=50)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    details = models.JSONField(default=dict)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'event_type', 'created_at']),
            models.Index(fields=['email', 'created_at']),
        ]

    def __str__(self):
        return f"{self.event_type} for {self.email} at {self.created_at}"

    def save(self, *args, **kwargs):
        # Ensure email is set from user if not provided
        if not self.email and self.user:
            self.email = self.user.email
        super().save(*args, **kwargs)

class PasswordResetToken(models.Model):
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='password_reset_tokens')
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = 'Password Reset Token'
        verbose_name_plural = 'Password Reset Tokens'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['user', 'created_at']),
        ]

    def __str__(self):
        return f"Reset token for {self.user.email}"

    def clean(self):
        if self.expires_at <= timezone.now():
            raise ValidationError("Expiration time must be in the future")
        
        # Check for existing valid tokens
        if not self.pk:  # Only check for new tokens
            existing_tokens = PasswordResetToken.objects.filter(
                user=self.user,
                used=False,
                expires_at__gt=timezone.now()
            )
            if existing_tokens.exists():
                raise ValidationError("User already has an active reset token")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at

    @property
    def is_valid(self):
        return not self.used and not self.is_expired

    def invalidate(self):
        """Invalidate the token and log the action"""
        self.used = True
        self.save()
        logger.info(f"Password reset token invalidated for user {self.user.email}")

class PasswordResetOTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)