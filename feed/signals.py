from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import FeedPost
import logging
from authapp.services import notify_new_feed_posted

@receiver(post_save, sender=FeedPost)
def trigger_feed_post_notification(sender, instance, created, **kwargs):
    if created:
        logger = logging.getLogger(__name__)
        logger.info(f"Triggering notification for new feed post ID: {instance.id}")
        notify_new_feed_posted(instance)