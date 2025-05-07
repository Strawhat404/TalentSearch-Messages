from django.db import models
from django.conf import settings
from taggit.managers import TaggableManager

class News(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    )
    title = models.CharField(max_length=255, help_text="Enter a concise news title (max 255 characters).")
    content = models.TextField(help_text="Provide the full news content.")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, help_text="User who created the news.")
    created_at = models.DateTimeField(auto_now_add=True, help_text="Auto-set creation date.")
    updated_at = models.DateTimeField(auto_now=True, help_text="Auto-set update date.")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', help_text="Current status of the news.")
    image_gallery = models.ManyToManyField('NewsImage', blank=True, help_text="Select images for the gallery.")
    tags = TaggableManager(blank=True, help_text="Add relevant tags for categorization.")

    def __str__(self):
        return self.title

class NewsImage(models.Model):
    image = models.ImageField(upload_to='news_images/', help_text="Upload an image for the news gallery.")
    caption = models.CharField(max_length=255, blank=True, help_text="Optional caption for the image.")

    def __str__(self):
        return self.caption or str(self.image)