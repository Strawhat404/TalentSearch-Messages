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