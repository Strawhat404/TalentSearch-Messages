import uuid
from django.db import models
from django.conf import settings
from feed_comments.models import Comment

class CommentReaction(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    comment = models.ForeignKey(
        Comment,
        on_delete=models.CASCADE,
        related_name='reactions',
        db_column='comment_id'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='comment_reactions',
        db_column='user_id'
    )
    is_dislike = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'comment_reactions'
        unique_together = ('comment', 'user')
        indexes = [
            models.Index(fields=['comment', 'user']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['comment', 'is_dislike']),
        ]

    def __str__(self):
        reaction_type = "Dislike" if self.is_dislike else "Like"
        return f"{reaction_type} by {self.user} on {self.comment}"

    def save(self, *args, **kwargs):
        # Update comment's like/dislike counts
        comment = self.comment
        if self.is_dislike:
            comment.dislikes_count += 1
            comment.likes_count = max(0, comment.likes_count - 1)
        else:
            comment.likes_count += 1
            comment.dislikes_count = max(0, comment.dislikes_count - 1)
        comment.save()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Update comment's like/dislike counts before deletion
        comment = self.comment
        if self.is_dislike:
            comment.dislikes_count = max(0, comment.dislikes_count - 1)
        else:
            comment.likes_count = max(0, comment.likes_count - 1)
        comment.save()
        super().delete(*args, **kwargs)
