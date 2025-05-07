from django.db import models
import uuid
from django.conf import settings

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
    image = models.URLField(
        max_length=200,
        blank=True,
        null=True,
        help_text="URL to the advert's image"
    )
    title = models.CharField(
        max_length=200,
        help_text="Title of the advert"
    )
    video = models.URLField(
        max_length=200,
        blank=True,
        null=True,
        help_text="URL to the advert's video"
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

    def __str__(self):
        return self.title