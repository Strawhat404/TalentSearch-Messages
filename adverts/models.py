from django.db import models
import uuid
from django.conf import settings
import logging
from django.utils import timezone
from django.db.models import Q

logger = logging.getLogger(__name__)


class AdvertManager(models.Manager):
    """
    Custom manager for Advert model with methods for filtering based on user authentication status
    """
    
    def for_public(self):
        """
        Return only published adverts that are currently running for public access
        """
        now = timezone.now()
        
        # Show published adverts that are currently running
        # This includes:
        # 1. Adverts with no date restrictions (run_from and run_to are null)
        # 2. Adverts that are currently within their date range
        # 3. Adverts that have started but no end date
        # 4. Adverts that have an end date but no start date (and haven't ended)
        
        return self.filter(
            status='published'
        ).filter(
            Q(run_from__isnull=True, run_to__isnull=True) |  # No date restrictions
            Q(run_from__isnull=True, run_to__gte=now) |      # No start date, but hasn't ended
            Q(run_from__lte=now, run_to__isnull=True) |      # Has started, no end date
            Q(run_from__lte=now, run_to__gte=now)            # Currently within date range
        )
    
    def for_authenticated_user(self, user):
        """
        Return all adverts for authenticated users
        """
        return self.all()
    
    def for_user(self, user):
        """
        Return appropriate queryset based on user authentication status
        """
        if user and user.is_authenticated:
            return self.for_authenticated_user(user)
        return self.for_public()


class Advert(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
        ('expired', 'Expired'),
    )

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique identifier for the advert"
    )
    image = models.ImageField(
        upload_to='adverts/images/',
        blank=True,
        null=True,
        help_text="Image for the advert"
    )
    title = models.CharField(
        max_length=200,
        help_text="Title of the advert"
    )
    video = models.FileField(
        upload_to='adverts/videos/',
        blank=True,
        null=True,
        help_text="Video for the advert"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Date and time when the advert was created"
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Detailed description of the advert"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='adverts',
        null=True,
        help_text="User who created the advert"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Date and time when the advert was last updated"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        help_text="Current status of the advert (e.g., Draft, Published)"
    )
    location = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Location or region for the advert"
    )
    run_from = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Start date and time for the advert campaign"
    )
    run_to = models.DateTimeField(
        blank=True,
        null=True,
        help_text="End date and time for the advert campaign"
    )

    # Use custom manager
    objects = AdvertManager()

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Advert'
        verbose_name_plural = 'Adverts'