from django.db import models
import uuid
from django.conf import settings
from feed_posts.models import FeedPost
from userprofile.models import Profile

class FeedLike(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique identifier for the like"
    )
    post = models.ForeignKey(
        FeedPost,
        on_delete=models.CASCADE,
        related_name='likes',
        help_text="The post that was liked"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='feed_likes',
        help_text="User who liked the post"
    )
    profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name='feed_likes',
        null=True,
        blank=True,
        help_text="Profile who liked the post"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When the post was liked"
    )

    class Meta:
        unique_together = ('post', 'user')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} liked {self.post.project_title}"
