from django.db import models
import uuid
from django.conf import settings
import os
import logging

logger = logging.getLogger(__name__)

def feed_post_upload_path(instance, filename):
    return f'feed_posts/media/{filename}'

class FeedPost(models.Model):
    MEDIA_TYPE_CHOICES = (
        ('image', 'Image'),
        ('video', 'Video'),
    )

    PROJECT_TYPE_CHOICES = (
        ('Film', 'Film'),
        ('TV', 'TV'),
        ('Commercial', 'Commercial'),
        ('Theater', 'Theater'),
        ('Music', 'Music'),
        ('Other', 'Other'),
    )

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique identifier for the post"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='feed_posts',
        help_text="User who created the post"
    )
    content = models.TextField(
        help_text="Content of the post"
    )
    media_type = models.CharField(
        max_length=10,
        choices=MEDIA_TYPE_CHOICES,
        help_text="Type of media (image or video)"
    )
    media_url = models.FileField(
        upload_to=feed_post_upload_path,
        help_text="Media file for the post (image or video)"
    )
    project_title = models.CharField(
        max_length=200,
        help_text="Title of the project"
    )
    project_type = models.CharField(
        max_length=20,
        choices=PROJECT_TYPE_CHOICES,
        help_text="Type of project"
    )
    location = models.CharField(
        max_length=200,
        help_text="Location of the project"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Date and time when the post was created"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Date and time when the post was last updated"
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies',
        help_text='Parent post for replies (null for top-level posts)'
    )

    def __str__(self):
        return f"{self.user.username}'s post - {self.project_title}"

    def save(self, *args, **kwargs):
        if self.pk and FeedPost.objects.filter(pk=self.pk).exists():
            old_instance = FeedPost.objects.get(pk=self.pk)
            if old_instance.media_url and old_instance.media_url != self.media_url:
                try:
                    if os.path.isfile(old_instance.media_url.path):
                        os.remove(old_instance.media_url.path)
                except Exception as e:
                    logger.error(f"Error deleting old media file: {e}")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.media_url:
            try:
                if os.path.isfile(self.media_url.path):
                    os.remove(self.media_url.path)
            except Exception as e:
                logger.error(f"Error deleting media file: {e}")
        super().delete(*args, **kwargs)

class UserFollow(models.Model):
    follower = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='following',
        help_text='The user who is following.'
    )
    following = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='followers',
        help_text='The user being followed.'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('follower', 'following')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.follower} follows {self.following}" 