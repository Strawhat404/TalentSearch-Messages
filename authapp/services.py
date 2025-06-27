"""
Notification Service for handling system notifications.
This service provides utilities for creating and managing notifications
across the application.
"""

from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.cache import cache
from django.db import transaction
from typing import List, Optional, Dict, Any
import logging
from datetime import timedelta

from .models import Notification

User = get_user_model()
logger = logging.getLogger(__name__)


class NotificationService:
    """
    Service class for handling system notifications.
    Provides methods for creating, managing, and sending notifications.
    """
    
    # Notification type constants
    NOTIFICATION_TYPES = {
        'SYSTEM': 'system',
        'SECURITY': 'security', 
        'ACCOUNT': 'account',
        'MESSAGE': 'message',
        'JOB': 'job',
        'NEWS': 'news',
        'COMMENT': 'comment',
        'LIKE': 'like',
        'RATING': 'rating',
        'RENTAL': 'rental',
        'ADVERT': 'advert',
        'PROFILE': 'profile',
        'VERIFICATION': 'verification',
        'PAYMENT': 'payment',
        'SUPPORT': 'support',
    }
    
    @classmethod
    def create_notification(
        cls,
        user: User,
        title: str,
        message: str,
        notification_type: str = 'info',
        link: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> Notification:
        """
        Create a new notification for a user.
        
        Args:
            user: The user to send the notification to
            title: Notification title
            message: Notification message
            notification_type: Type of notification (info, warning, alert, system, etc.)
            link: Optional link for the notification
            data: Optional additional data to store with the notification
            
        Returns:
            Created notification object
        """
        try:
            with transaction.atomic():
                notification = Notification.objects.create(
                    user=user,
                    title=title,
                    message=message,
                    notification_type=notification_type,
                    link=link
                )
                
                # Update user's unread notification count in cache
                cls._update_unread_count(user)
                
                logger.info(f"Created notification for user {user.email}: {title}")
                return notification
                
        except Exception as e:
            logger.error(f"Error creating notification for user {user.email}: {str(e)}")
            raise
    
    @classmethod
    def create_system_notification(
        cls,
        title: str,
        message: str,
        users: Optional[List[User]] = None,
        link: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> List[Notification]:
        """
        Create system notifications for multiple users or all users.
        
        Args:
            title: Notification title
            message: Notification message
            users: List of users to notify (if None, notify all active users)
            link: Optional link for the notification
            data: Optional additional data
            
        Returns:
            List of created notifications
        """
        if users is None:
            users = User.objects.filter(is_active=True)
        
        notifications = []
        for user in users:
            try:
                notification = cls.create_notification(
                    user=user,
                    title=title,
                    message=message,
                    notification_type=cls.NOTIFICATION_TYPES['SYSTEM'],
                    link=link,
                    data=data
                )
                notifications.append(notification)
            except Exception as e:
                logger.error(f"Error creating system notification for user {user.email}: {str(e)}")
                continue
        
        logger.info(f"Created {len(notifications)} system notifications")
        return notifications
    
    @classmethod
    def create_security_notification(
        cls,
        user: User,
        title: str,
        message: str,
        link: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> Notification:
        """
        Create a security-related notification.
        
        Args:
            user: The user to notify
            title: Notification title
            message: Notification message
            link: Optional link
            data: Optional additional data
            
        Returns:
            Created notification
        """
        return cls.create_notification(
            user=user,
            title=title,
            message=message,
            notification_type=cls.NOTIFICATION_TYPES['SECURITY'],
            link=link,
            data=data
        )
    
    @classmethod
    def create_account_notification(
        cls,
        user: User,
        title: str,
        message: str,
        link: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> Notification:
        """
        Create an account-related notification.
        
        Args:
            user: The user to notify
            title: Notification title
            message: Notification message
            link: Optional link
            data: Optional additional data
            
        Returns:
            Created notification
        """
        return cls.create_notification(
            user=user,
            title=title,
            message=message,
            notification_type=cls.NOTIFICATION_TYPES['ACCOUNT'],
            link=link,
            data=data
        )
    
    @classmethod
    def mark_as_read(cls, notification_id: int, user: User) -> bool:
        """
        Mark a notification as read.
        
        Args:
            notification_id: ID of the notification
            user: The user who owns the notification
            
        Returns:
            True if successful, False otherwise
        """
        try:
            notification = Notification.objects.get(id=notification_id, user=user)
            if not notification.read:
                notification.read = True
                notification.save()
                cls._update_unread_count(user)
                logger.info(f"Marked notification {notification_id} as read for user {user.email}")
            return True
        except Notification.DoesNotExist:
            logger.warning(f"Notification {notification_id} not found for user {user.email}")
            return False
        except Exception as e:
            logger.error(f"Error marking notification {notification_id} as read: {str(e)}")
            return False
    
    @classmethod
    def mark_all_as_read(cls, user: User) -> int:
        """
        Mark all notifications as read for a user.
        
        Args:
            user: The user whose notifications to mark as read
            
        Returns:
            Number of notifications marked as read
        """
        try:
            count = Notification.objects.filter(user=user, read=False).update(read=True)
            cls._update_unread_count(user)
            logger.info(f"Marked {count} notifications as read for user {user.email}")
            return count
        except Exception as e:
            logger.error(f"Error marking all notifications as read for user {user.email}: {str(e)}")
            return 0
    
    @classmethod
    def delete_notification(cls, notification_id: int, user: User) -> bool:
        """
        Delete a notification.
        
        Args:
            notification_id: ID of the notification
            user: The user who owns the notification
            
        Returns:
            True if successful, False otherwise
        """
        try:
            notification = Notification.objects.get(id=notification_id, user=user)
            notification.delete()
            cls._update_unread_count(user)
            logger.info(f"Deleted notification {notification_id} for user {user.email}")
            return True
        except Notification.DoesNotExist:
            logger.warning(f"Notification {notification_id} not found for user {user.email}")
            return False
        except Exception as e:
            logger.error(f"Error deleting notification {notification_id}: {str(e)}")
            return False
    
    @classmethod
    def get_unread_count(cls, user: User) -> int:
        """
        Get the number of unread notifications for a user.
        
        Args:
            user: The user to get count for
            
        Returns:
            Number of unread notifications
        """
        cache_key = f"unread_notifications_{user.id}"
        count = cache.get(cache_key)
        
        if count is None:
            count = Notification.objects.filter(user=user, read=False).count()
            cache.set(cache_key, count, 300)  # Cache for 5 minutes
        
        return count
    
    @classmethod
    def _update_unread_count(cls, user: User) -> None:
        """
        Update the cached unread notification count for a user.
        
        Args:
            user: The user to update count for
        """
        cache_key = f"unread_notifications_{user.id}"
        count = Notification.objects.filter(user=user, read=False).count()
        cache.set(cache_key, count, 300)  # Cache for 5 minutes
    
    @classmethod
    def get_recent_notifications(cls, user: User, limit: int = 10) -> List[Notification]:
        """
        Get recent notifications for a user.
        
        Args:
            user: The user to get notifications for
            limit: Maximum number of notifications to return
            
        Returns:
            List of recent notifications
        """
        return Notification.objects.filter(user=user).order_by('-created_at')[:limit]
    
    @classmethod
    def cleanup_old_notifications(cls, days: int = 30) -> int:
        """
        Clean up old notifications.
        
        Args:
            days: Number of days to keep notifications
            
        Returns:
            Number of notifications deleted
        """
        cutoff_date = timezone.now() - timedelta(days=days)
        count = Notification.objects.filter(created_at__lt=cutoff_date).count()
        if count > 0:
            Notification.objects.filter(created_at__lt=cutoff_date).delete()
            logger.info(f"Cleaned up {count} old notifications")
        return count


# Convenience functions for common notification types
def notify_user_login(user: User, ip_address: str = None, device_info: str = None):
    """Notify user of successful login."""
    message = f"Successful login to your account"
    if ip_address:
        message += f" from IP: {ip_address}"
    if device_info:
        message += f" using {device_info}"
    
    NotificationService.create_security_notification(
        user=user,
        title="Login Successful",
        message=message
    )


def notify_user_logout(user: User, ip_address: str = None):
    """Notify user of logout."""
    message = "You have been logged out of your account"
    if ip_address:
        message += f" from IP: {ip_address}"
    
    NotificationService.create_security_notification(
        user=user,
        title="Logout Successful",
        message=message
    )


def notify_password_change(user: User, ip_address: str = None):
    """Notify user of password change."""
    message = "Your password has been changed successfully"
    if ip_address:
        message += f" from IP: {ip_address}"
    
    NotificationService.create_security_notification(
        user=user,
        title="Password Changed",
        message=message
    )


def notify_suspicious_activity(user: User, activity_type: str, ip_address: str = None):
    """Notify user of suspicious activity."""
    message = f"Suspicious {activity_type} detected on your account"
    if ip_address:
        message += f" from IP: {ip_address}"
    
    NotificationService.create_security_notification(
        user=user,
        title="Suspicious Activity Detected",
        message=message
    )


def notify_account_verification(user: User, verification_type: str):
    """Notify user of account verification."""
    NotificationService.create_account_notification(
        user=user,
        title="Account Verification",
        message=f"Your {verification_type} has been verified successfully."
    )


def notify_new_message(user: User, sender_name: str):
    """Notify user of new message."""
    NotificationService.create_notification(
        user=user,
        title="New Message",
        message=f"You have received a new message from {sender_name}",
        notification_type=NotificationService.NOTIFICATION_TYPES['MESSAGE']
    )


def notify_job_application_update(user: User, job_title: str, status: str):
    """Notify user of job application update."""
    NotificationService.create_notification(
        user=user,
        title="Job Application Update",
        message=f"Your application for '{job_title}' has been {status}",
        notification_type=NotificationService.NOTIFICATION_TYPES['JOB']
    )


def notify_new_comment(user: User, content_type: str, author_name: str):
    """Notify user of new comment."""
    NotificationService.create_notification(
        user=user,
        title="New Comment",
        message=f"{author_name} commented on your {content_type}",
        notification_type=NotificationService.NOTIFICATION_TYPES['COMMENT']
    )


def notify_new_like(user: User, content_type: str, liker_name: str):
    """Notify user of new like."""
    NotificationService.create_notification(
        user=user,
        title="New Like",
        message=f"{liker_name} liked your {content_type}",
        notification_type=NotificationService.NOTIFICATION_TYPES['LIKE']
    )


def notify_new_user_registration(user: User):
    """
    Notify admins when a new user registers.
    This should be called after a new user is successfully created.
    """
    # Get all admin users
    admin_users = User.objects.filter(is_staff=True, is_active=True)
    
    # Create notification for each admin
    for admin in admin_users:
        NotificationService.create_system_notification(
            title="New User Registration",
            message=f"A new user, {user.username or user.email}, has registered.",
            users=[admin],
            data={
                'new_user_id': user.id,
                'new_user_email': user.email,
                'new_user_username': user.username,
                'registration_date': user.date_joined.isoformat()
            }
        )


def notify_user_reported(reported_user: User, reporter_user: User, reason: str):
    """
    Notify admins when a user is reported by another user.
    """
    # Get all admin users
    admin_users = User.objects.filter(is_staff=True, is_active=True)
    
    # Create notification for each admin
    for admin in admin_users:
        NotificationService.create_system_notification(
            title="User Reported",
            message=f"User {reported_user.username or reported_user.email} was reported for {reason}.",
            users=[admin],
            data={
                'reported_user_id': reported_user.id,
                'reported_user_email': reported_user.email,
                'reported_user_username': reported_user.username,
                'reporter_user_id': reporter_user.id,
                'reporter_user_email': reporter_user.email,
                'reporter_user_username': reporter_user.username,
                'report_reason': reason,
                'report_date': timezone.now().isoformat()
            }
        )


def notify_new_feed_posted(feed_post):
    """
    Notify relevant users when a new feed post is created.
    This could notify followers, users with similar interests, etc.
    """
    # For now, notify all active users (you can customize this logic)
    # In a real implementation, you might want to notify only followers or users with similar interests
    active_users = User.objects.filter(is_active=True).exclude(id=feed_post.user.id)
    
    # Limit to first 100 users to avoid performance issues
    # In production, you might want to use a queue system for this
    for user in active_users[:100]:
        NotificationService.create_notification(
            user=user,
            title="New Feed Posted",
            message=f"{feed_post.user.username or feed_post.user.email} posted a new feed: '{feed_post.project_title}'.",
            notification_type=NotificationService.NOTIFICATION_TYPES['NEWS'],
            data={
                'feed_post_id': str(feed_post.id),
                'feed_post_title': feed_post.project_title,
                'feed_post_type': feed_post.project_type,
                'author_id': feed_post.user.id,
                'author_username': feed_post.user.username,
                'author_email': feed_post.user.email
            }
        )


def notify_new_job_posted(job):
    """
    Notify relevant users when a new job is posted.
    """
    # Notify all active users (you can customize this based on job requirements)
    active_users = User.objects.filter(is_active=True).exclude(id=job.user_id.id)
    
    # Limit to first 100 users to avoid performance issues
    for user in active_users[:100]:
        NotificationService.create_notification(
            user=user,
            title="New Job Posted",
            message=f"{job.user_id.username or job.user_id.email} posted a new job: '{job.job_title}'.",
            notification_type=NotificationService.NOTIFICATION_TYPES['JOB'],
            data={
                'job_id': job.id,
                'job_title': job.job_title,
                'company_name': job.company_name,
                'project_type': job.project_type,
                'talents': job.talents,
                'poster_id': job.user_id.id,
                'poster_username': job.user_id.username,
                'poster_email': job.user_id.email
            }
        )


def notify_new_rental_posted(rental_item):
    """
    Notify relevant users when a new rental item is posted.
    """
    # Notify all active users (you can customize this based on rental category)
    active_users = User.objects.filter(is_active=True).exclude(id=rental_item.user.id)
    
    # Limit to first 100 users to avoid performance issues
    for user in active_users[:100]:
        NotificationService.create_notification(
            user=user,
            title="New Rental Item",
            message=f"{rental_item.user.username or rental_item.user.email} listed a new rental: '{rental_item.name}'.",
            notification_type=NotificationService.NOTIFICATION_TYPES['RENTAL'],
            data={
                'rental_item_id': str(rental_item.id),
                'rental_item_name': rental_item.name,
                'rental_item_type': rental_item.type,
                'rental_item_category': rental_item.category,
                'daily_rate': str(rental_item.daily_rate),
                'lister_id': rental_item.user.id,
                'lister_username': rental_item.user.username,
                'lister_email': rental_item.user.email
            }
        )


def notify_user_verified_by_admin(user: User, admin_user: User, verification_type: str = "account"):
    """
    Notify user when they are verified by an admin.
    """
    NotificationService.create_account_notification(
        user=user,
        title="User Verified",
        message=f"User {user.username or user.email} has been verified by {admin_user.username or admin_user.email}.",
        data={
            'verification_type': verification_type,
            'verified_by_id': admin_user.id,
            'verified_by_username': admin_user.username,
            'verified_by_email': admin_user.email,
            'verification_date': timezone.now().isoformat()
        }
    )


def notify_user_rejected_by_admin(user: User, admin_user: User, reason: str = "", verification_type: str = "account"):
    """
    Notify user when they are rejected by an admin.
    """
    message = f"User {user.username or user.email} has been rejected by {admin_user.username or admin_user.email}."
    if reason:
        message += f" Reason: {reason}"
    
    NotificationService.create_account_notification(
        user=user,
        title="User Rejected",
        message=message,
        data={
            'verification_type': verification_type,
            'rejected_by_id': admin_user.id,
            'rejected_by_username': admin_user.username,
            'rejected_by_email': admin_user.email,
            'rejection_reason': reason,
            'rejection_date': timezone.now().isoformat()
        }
    )


def notify_rental_verification_status(rental_item, admin_user: User, is_approved: bool, reason: str = ""):
    """
    Notify user when their rental item is verified or rejected by admin.
    """
    if is_approved:
        title = "Rental Item Approved"
        message = f"Your rental item '{rental_item.name}' has been approved by {admin_user.username or admin_user.email}."
    else:
        title = "Rental Item Rejected"
        message = f"Your rental item '{rental_item.name}' has been rejected by {admin_user.username or admin_user.email}."
        if reason:
            message += f" Reason: {reason}"
    
    NotificationService.create_notification(
        user=rental_item.user,
        title=title,
        message=message,
        notification_type=NotificationService.NOTIFICATION_TYPES['RENTAL'],
        data={
            'rental_item_id': str(rental_item.id),
            'rental_item_name': rental_item.name,
            'is_approved': is_approved,
            'reviewed_by_id': admin_user.id,
            'reviewed_by_username': admin_user.username,
            'reviewed_by_email': admin_user.email,
            'review_reason': reason,
            'review_date': timezone.now().isoformat()
        }
    )


# Additional utility functions for admin notifications
def notify_admins_of_system_event(event_type: str, event_details: str, data: dict = None):
    """
    Generic function to notify all admins of system events.
    """
    # Get all admin users
    admin_users = User.objects.filter(is_staff=True, is_active=True)
    
    for admin in admin_users:
        NotificationService.create_system_notification(
            title=f"System Event: {event_type}",
            message=event_details,
            users=[admin],
            data=data or {}
        )


def notify_user_of_profile_verification(user: User, verification_type: str, is_approved: bool, admin_user: User = None, reason: str = ""):
    """
    Notify user when their profile verification is processed.
    """
    if is_approved:
        title = "Profile Verification Approved"
        message = f"Your {verification_type} verification has been approved."
        if admin_user:
            message += f" by {admin_user.username or admin_user.email}"
    else:
        title = "Profile Verification Rejected"
        message = f"Your {verification_type} verification has been rejected."
        if admin_user:
            message += f" by {admin_user.username or admin_user.email}"
        if reason:
            message += f" Reason: {reason}"
    
    NotificationService.create_account_notification(
        user=user,
        title=title,
        message=message,
        data={
            'verification_type': verification_type,
            'is_approved': is_approved,
            'reviewed_by_id': admin_user.id if admin_user else None,
            'reviewed_by_username': admin_user.username if admin_user else None,
            'reviewed_by_email': admin_user.email if admin_user else None,
            'review_reason': reason,
            'review_date': timezone.now().isoformat()
        }
    ) 