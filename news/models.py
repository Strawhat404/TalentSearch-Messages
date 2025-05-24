from django.db import models
from django.conf import settings
from taggit.managers import TaggableManager
import os
import logging
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from django.utils.html import strip_tags
from django.core.validators import MinLengthValidator, MaxLengthValidator, FileExtensionValidator
import bleach

logger = logging.getLogger(__name__)

class News(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    )

    # Define valid status transitions
    STATUS_TRANSITIONS = {
        'draft': ['published', 'archived'],
        'published': ['archived'],
        'archived': ['draft', 'published'],
    }

    title = models.CharField(max_length=255, help_text="Enter a concise news title (max 255 characters).")
    content = models.TextField(
        help_text="Provide the full news content.",
        validators=[
            MinLengthValidator(10, message="Content must be at least 10 characters long."),
            MaxLengthValidator(50000, message="Content cannot exceed 50,000 characters.")
        ]
    )
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, help_text="User who created the news.")
    created_at = models.DateTimeField(auto_now_add=True, help_text="Auto-set creation date.")
    updated_at = models.DateTimeField(auto_now=True, help_text="Auto-set update date.")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', help_text="Current status of the news.")
    image_gallery = models.ManyToManyField('NewsImage', blank=True, help_text="Select images for the gallery.")
    tags = TaggableManager(blank=True, help_text="Add relevant tags for categorization.")

    def __str__(self):
        return self.title

    def clean(self):
        """
        Validate the news instance
        """
        # Clean and sanitize content
        if self.content:
            # First strip HTML tags
            clean_content = strip_tags(self.content)
            # Then sanitize using bleach
            self.content = bleach.clean(
                clean_content,
                strip=True,
                strip_comments=True,
                tags=[],  # No HTML tags allowed
                attributes={},
                protocols=[]
            )

        # Validate status transition
        if self.pk:  # Only check transitions for existing instances
            old_instance = News.objects.get(pk=self.pk)
            if old_instance.status != self.status:
                if self.status not in self.STATUS_TRANSITIONS[old_instance.status]:
                    raise ValidationError({
                        'status': f'Cannot transition from {old_instance.status} to {self.status}. '
                                f'Valid transitions are: {", ".join(self.STATUS_TRANSITIONS[old_instance.status])}'
                    })

    def save(self, *args, **kwargs):
        self.full_clean()  # Run validation before saving
        super().save(*args, **kwargs)

class NewsImage(models.Model):
    # Maximum file size: 5MB
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB in bytes
    # Maximum dimensions
    MAX_WIDTH = 1920
    MAX_HEIGHT = 1080
    # Allowed file types
    ALLOWED_EXTENSIONS = ['jpg', 'jpeg', 'png', 'gif', 'webp']

    image = models.ImageField(
        upload_to='news_images/',
        help_text="Upload an image for the news gallery.",
        validators=[
            FileExtensionValidator(
                allowed_extensions=ALLOWED_EXTENSIONS,
                message=f"Only {', '.join(ALLOWED_EXTENSIONS)} files are allowed."
            )
        ]
    )
    caption = models.CharField(max_length=255, blank=True, help_text="Optional caption for the image.")

    def __str__(self):
        return self.caption or str(self.image)

    def clean(self):
        """
        Validate the image
        """
        if self.image:
            # Check file size
            if self.image.size > self.MAX_FILE_SIZE:
                raise ValidationError({
                    'image': f'Image size must be no more than {self.MAX_FILE_SIZE/1024/1024}MB'
                })

            # Check image dimensions
            from PIL import Image
            img = Image.open(self.image)
            width, height = img.size
            if width > self.MAX_WIDTH or height > self.MAX_HEIGHT:
                raise ValidationError({
                    'image': f'Image dimensions must be no larger than {self.MAX_WIDTH}x{self.MAX_HEIGHT} pixels'
                })

            # Validate image content
            try:
                img.verify()  # Verify it's a valid image
            except Exception as e:
                raise ValidationError({
                    'image': f'Invalid image file: {str(e)}'
                })

    def save(self, *args, **kwargs):
        if self.pk and NewsImage.objects.filter(pk=self.pk).exists():
            old_instance = NewsImage.objects.get(pk=self.pk)
            if old_instance.image and old_instance.image != self.image:
                try:
                    if os.path.isfile(old_instance.image.path):
                        os.remove(old_instance.image.path)
                except Exception as e:
                    logger.error(f"Error deleting old news image: {e}")
        
        self.full_clean()  # Run validation before saving
        super().save(*args, **kwargs)

@receiver(post_delete, sender=NewsImage)
def delete_news_image_file(sender, instance, **kwargs):
    if instance.image and os.path.isfile(instance.image.path):
        os.remove(instance.image.path)