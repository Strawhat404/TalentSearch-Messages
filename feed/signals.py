from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import FeedPost, FeedLike, Comment
import logging
from authapp.services import notify_new_feed_posted, notify_new_like, notify_new_comment
logger = logging.getLogger(__name__)

@receiver(post_save, sender=FeedPost)
def trigger_feed_post_notification(sender, instance, created, **kwargs):
    if created:
        logger = logging.getLogger(__name__)
        logger.info(f"Triggering notification for new feed post ID: {instance.id}")
        notify_new_feed_posted(instance)
@receiver(post_save, sender=FeedLike)
def trigger_like_notification(sender, instance, created, **kwargs):
    if created:
        logger.info(f"Triggering notification for new like on post ID: {instance.post.id}")
        # Notify the post author
        post_author = instance.post.profile.user
        author_name = instance.profile.name or instance.profile.user.email
        notify_new_like(user=post_author, content_type="feed post", author_name=author_name)

@receiver(post_save, sender=Comment)
def trigger_comment_notification(sender, instance, created, **kwargs):
    if created:
        logger.info(f"Triggering notification for new comment on post ID: {instance.post.id}")
        # Notify the post author if the comment is not from the author
        post_author = instance.post.profile.user
        if instance.profile.user != post_author:
            author_name = instance.profile.name or instance.profile.user.email
            notify_new_comment(user=post_author, content_type="feed post", author_name=author_name)