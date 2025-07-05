import uuid
from django.db import models
from django.conf import settings
from feed_posts.models import FeedPost
from userprofile.models import Profile

class Comment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post = models.ForeignKey(
        FeedPost,
        on_delete=models.CASCADE,
        related_name='comments',
        db_column='post_id'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='comments',
        db_column='user_id',
        help_text="User who created the comment"
    )
    profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name='comments',
        db_column='profile_id',
        null=True,
        blank=True,
        help_text="Profile who created the comment"
    )
    content = models.TextField()
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies',
        db_column='parent_id'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    likes_count = models.IntegerField(default=0)
    dislikes_count = models.IntegerField(default=0)

    class Meta:
        db_table = 'feed_comments'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['post', 'created_at']),
            models.Index(fields=['parent', 'created_at']),
            models.Index(fields=['user', 'created_at']),
        ]

    def __str__(self):
        return f"Comment by {self.user} on {self.post}"

class CommentLike(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    comment = models.ForeignKey(
        Comment,
        on_delete=models.CASCADE,
        related_name='likes',
        db_column='comment_id'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='comment_likes',
        db_column='user_id',
        help_text="User who liked/disliked the comment"
    )
    profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name='comment_likes',
        db_column='profile_id',
        null=True,
        blank=True,
        help_text="Profile who liked/disliked the comment"
    )
    is_like = models.BooleanField(default=True)  # True for like, False for dislike
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'feed_comment_likes'
        unique_together = ('comment', 'user')
        indexes = [
            models.Index(fields=['comment', 'user']),
            models.Index(fields=['user', 'created_at']),
        ]

    def __str__(self):
        return f"{'Like' if self.is_like else 'Dislike'} by {self.user} on {self.comment}"
