from django.db.models.signals import pre_delete
from django.dispatch import receiver
from .models import FeedPost
import os
import logging

logger = logging.getLogger(__name__)

@receiver(pre_delete, sender=FeedPost)
def delete_feed_post_files(sender, instance, **kwargs):
    """
    Signal to delete associated media files when a feed post is deleted
    """
    if instance.media_url:
        try:
            if os.path.isfile(instance.media_url.path):
                os.remove(instance.media_url.path)
        except Exception as e:
            logger.error(f"Error deleting media file for feed post {instance.id}: {e}") 