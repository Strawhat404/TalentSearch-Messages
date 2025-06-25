from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid
from django.core.exceptions import ValidationError
import logging

logger = logging.getLogger(__name__)

class UserManager(BaseUserManager):
    def create_user(self, email=None, username=None, password=None, **extra_fields):
        if not email and not username:
            raise ValueError('Either Email or Username must be set')
        
        if email:
            email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email=None, username=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        if not email and not username:
            raise ValueError('Either Email or Username must be set for superuser')
        return self.create_user(email=email, username=username, password=password, **extra_fields)

class User(AbstractUser):
    username = models.CharField(max_length=150, unique=True, null=True, blank=True)
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True, null=True, blank=True)
    backup_email = models.EmailField(blank=True, null=True, help_text='Backup email for account recovery')
    phone_number = models.CharField(max_length=20, default="0000000000")
    last_password_change = models.DateTimeField(default=timezone.now)
    is_locked = models.BooleanField(default=False, help_text='Whether the account is locked due to failed attempts')
    lockout_until = models.DateTimeField(null=True, blank=True, help_text='When the account lockout expires')
    failed_login_attempts = models.IntegerField(default=0, help_text='Number of failed login attempts')
    last_failed_login = models.DateTimeField(null=True, blank=True, help_text='Timestamp of last failed login attempt')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    objects = UserManager()

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='custom_user_set',
        blank=True,
        help_text='The groups this user belongs to.',
        related_query_name='user'
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='custom_user_permissions_set',
        blank=True,
        help_text='Specific permissions for this user.',
        related_query_name='user'
    )

    def set_password(self, raw_password):
        """Set the user's password and update last_password_change timestamp."""
        super().set_password(raw_password)
        self.last_password_change = timezone.now()
        if self.pk:
            self.save(update_fields=['last_password_change'])
        else:
            self.save()

    def clean(self):
        super().clean()
        if not self.username and not self.email:
            raise ValidationError('Either username or email must be provided')

    class Meta:
        db_table = 'auth_user'

class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('info', 'Information'),
        ('warning', 'Warning'),
        ('alert', 'Alert'),
        ('system', 'System'),
        ('security', 'Security'),
        ('account', 'Account'),
        ('message', 'Message'),
        ('job', 'Job'),
        ('news', 'News'),
        ('comment', 'Comment'),
        ('like', 'Like'),
        ('rating', 'Rating'),
        ('rental', 'Rental'),
        ('advert', 'Advert'),
        ('profile', 'Profile'),
        ('verification', 'Verification'),
        ('payment', 'Payment'),
        ('support', 'Support'),
    )
    
    MAX_TITLE_LENGTH = 200
    MAX_MESSAGE_LENGTH = 2000
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=MAX_TITLE_LENGTH)
    message = models.TextField(max_length=MAX_MESSAGE_LENGTH)
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='info')
    read = models.BooleanField(default=False)
    link = models.URLField(blank=True, null=True, max_length=500)
    data = models.JSONField(blank=True, null=True, help_text="Additional data for the notification")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'read']),
            models.Index(fields=['user', 'notification_type']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.user.email}"
    
    @property
    def is_unread(self):
        """Check if notification is unread."""
        return not self.read
    
    def mark_as_read(self):
        """Mark notification as read."""
        if not self.read:
            self.read = True
            self.save(update_fields=['read'])
    
    def mark_as_unread(self):
        """Mark notification as unread."""
        if self.read:
            self.read = False
            self.save(update_fields=['read'])

class SecurityLog(models.Model):
    """Model to track security-related events"""
    user = models.ForeignKey(
        'User', 
        on_delete=models.CASCADE, 
        related_name='security_logs',
        null=True,
        blank=True
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
        
        if not self.pk:
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
    