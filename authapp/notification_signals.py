"""
Notification signals for automatic notification triggering.
This module contains Django signals that automatically create notifications
when certain events occur in the system.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .services import (
    notify_new_user_registration,
    notify_new_feed_posted,
    notify_new_job_posted,
    notify_new_rental_posted,
    notify_user_verified_by_admin,
    notify_user_rejected_by_admin,
    notify_rental_verification_status,
    notify_user_of_profile_verification
)

User = get_user_model()


@receiver(post_save, sender=User)
def handle_new_user_registration(sender, instance, created, **kwargs):
    """
    Signal handler for new user registration.
    Only triggers for newly created users, not updates.
    """
    if created:
        # Notify admins about new user registration
        notify_new_user_registration(instance)


# Jobs notifications
@receiver(post_save, sender='jobs.Job')
def handle_new_job_post(sender, instance, created, **kwargs):
    """
    Signal handler for new job posts.
    Only triggers for newly created jobs, not updates.
    """
    if created:
        notify_new_job_posted(instance)


# Rental Items notifications
@receiver(post_save, sender='rental_items.RentalItem')
def handle_new_rental_item(sender, instance, created, **kwargs):
    """
    Signal handler for new rental items.
    Only triggers for newly created items, not updates.
    """
    if created:
        notify_new_rental_posted(instance)


# Profile verification notifications
@receiver(post_save, sender='userprofile.VerificationStatus')
def handle_profile_verification(sender, instance, created, **kwargs):
    """
    Signal handler for profile verification status changes.
    """
    if created or instance.tracker.has_changed('is_verified'):
        # This would need to be enhanced to get the admin user who made the change
        # For now, we'll use a generic approach
        notify_user_of_profile_verification(
            user=instance.profile.user,
            verification_type=instance.verification_type,
            is_approved=instance.is_verified,
            admin_user=instance.verified_by if hasattr(instance, 'verified_by') else None
        )


# Note: For rental item approval/rejection, you'll need to add a field to track approval status
# and create a custom signal or use the existing approval field in the RentalItem model 