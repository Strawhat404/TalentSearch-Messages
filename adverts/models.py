from django.db import models
import uuid
from django.conf import settings
import os
import logging

logger = logging.getLogger(__name__)

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

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if self.pk and Advert.objects.filter(pk=self.pk).exists():
            old_instance = Advert.objects.get(pk=self.pk)
            if old_instance.image and old_instance.image != self.image:
                try:
                    if os.path.isfile(old_instance.image.path):
                        os.remove(old_instance.image.path)
                except Exception as e:
                    logger.error(f"Error deleting old image: {e}")
        super().save(*args, **kwargs)