"""
Comprehensive tests for the notification system.
Tests all notification endpoints, services, and functionality.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
import json

from .models import Notification
from .services import NotificationService

User = get_user_model()


class NotificationServiceTest(TestCase):
    """Test the NotificationService class."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            name='Test User'
        )
    
    def test_create_notification(self):
        """Test creating a basic notification."""
        notification = NotificationService.create_notification(
            user=self.user,
            title='Test Notification',
            message='This is a test notification',
            notification_type='info'
        )
        
        self.assertEqual(notification.user, self.user)
        self.assertEqual(notification.title, 'Test Notification')
        self.assertEqual(notification.message, 'This is a test notification')
        self.assertEqual(notification.notification_type, 'info')
        self.assertFalse(notification.read)
    
    def test_create_security_notification(self):
        """Test creating a security notification."""
        notification = NotificationService.create_security_notification(
            user=self.user,
            title='Security Alert',
            message='Suspicious login detected'
        )
        
        self.assertEqual(notification.notification_type, 'security')
        self.assertEqual(notification.title, 'Security Alert')
    
    def test_create_system_notification(self):
        """Test creating system notifications."""
        user2 = User.objects.create_user(
            email='test2@example.com',
            password='testpass123',
            name='Test User 2'
        )
        
        notifications = NotificationService.create_system_notification(
            title='System Maintenance',
            message='System will be down for maintenance',
            users=[self.user, user2]
        )
        
        self.assertEqual(len(notifications), 2)
        for notification in notifications:
            self.assertEqual(notification.notification_type, 'system')
            self.assertEqual(notification.title, 'System Maintenance')
    
    def test_mark_as_read(self):
        """Test marking notification as read."""
        notification = NotificationService.create_notification(
            user=self.user,
            title='Test Notification',
            message='This is a test notification'
        )
        
        # Initially unread
        self.assertFalse(notification.read)
        
        # Mark as read
        success = NotificationService.mark_as_read(notification.id, self.user)
        self.assertTrue(success)
        
        # Refresh from database
        notification.refresh_from_db()
        self.assertTrue(notification.read)
    
    def test_mark_all_as_read(self):
        """Test marking all notifications as read."""
        # Create multiple notifications
        for i in range(3):
            NotificationService.create_notification(
                user=self.user,
                title=f'Test Notification {i}',
                message=f'This is test notification {i}'
            )
        
        # Verify all are unread
        unread_count = Notification.objects.filter(user=self.user, read=False).count()
        self.assertEqual(unread_count, 3)
        
        # Mark all as read
        count = NotificationService.mark_all_as_read(self.user)
        self.assertEqual(count, 3)
        
        # Verify all are read
        unread_count = Notification.objects.filter(user=self.user, read=False).count()
        self.assertEqual(unread_count, 0)
    
    def test_delete_notification(self):
        """Test deleting a notification."""
        notification = NotificationService.create_notification(
            user=self.user,
            title='Test Notification',
            message='This is a test notification'
        )
        
        # Verify notification exists
        self.assertTrue(Notification.objects.filter(id=notification.id).exists())
        
        # Delete notification
        success = NotificationService.delete_notification(notification.id, self.user)
        self.assertTrue(success)
        
        # Verify notification is deleted
        self.assertFalse(Notification.objects.filter(id=notification.id).exists())
    
    def test_get_unread_count(self):
        """Test getting unread notification count."""
        # Create some notifications
        for i in range(3):
            NotificationService.create_notification(
                user=self.user,
                title=f'Test Notification {i}',
                message=f'This is test notification {i}'
            )
        
        # Clear cache to ensure fresh count
        from django.core.cache import cache
        cache.delete(f"unread_notifications_{self.user.id}")
        
        # Mark one as read
        notification = Notification.objects.filter(user=self.user).first()
        notification.read = True
        notification.save()
        
        # Clear cache again
        cache.delete(f"unread_notifications_{self.user.id}")
        
        # Get unread count
        unread_count = NotificationService.get_unread_count(self.user)
        self.assertEqual(unread_count, 2)
    
    def test_cleanup_old_notifications(self):
        """Test cleaning up old notifications."""
        # Create old notification by directly setting the created_at field
        old_notification = Notification.objects.create(
            user=self.user,
            title='Old Notification',
            message='This is an old notification'
        )
        # Manually set the created_at to be old
        old_notification.created_at = timezone.now() - timedelta(days=31)
        old_notification.save()
        
        # Create recent notification
        recent_notification = Notification.objects.create(
            user=self.user,
            title='Recent Notification',
            message='This is a recent notification'
        )
        # Manually set the created_at to be recent
        recent_notification.created_at = timezone.now() - timedelta(days=5)
        recent_notification.save()
        
        # Clean up notifications older than 30 days
        deleted_count = NotificationService.cleanup_old_notifications(30)
        self.assertEqual(deleted_count, 1)
        
        # Verify old notification is deleted
        self.assertFalse(Notification.objects.filter(id=old_notification.id).exists())
        
        # Verify recent notification still exists
        self.assertTrue(Notification.objects.filter(id=recent_notification.id).exists())


class NotificationViewsTest(TestCase):
    """Test notification API views."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            name='Test User'
        )
        self.admin_user = User.objects.create_user(
            email='admin@example.com',
            password='adminpass123',
            name='Admin User',
            is_staff=True
        )
        
        # Create some test notifications
        self.notifications = []
        for i in range(3):
            notification = Notification.objects.create(
                user=self.user,
                title=f'Test Notification {i}',
                message=f'This is test notification {i}',
                notification_type='info'
            )
            self.notifications.append(notification)
    
    def test_list_notifications_authenticated(self):
        """Test getting notifications for authenticated user."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse('notifications'))
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)
    
    def test_list_notifications_unauthenticated(self):
        """Test getting notifications without authentication."""
        response = self.client.get(reverse('notifications'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_create_notification(self):
        """Test creating a notification."""
        self.client.force_authenticate(user=self.user)
        data = {
            'title': 'New Notification',
            'message': 'This is a new notification',
            'notification_type': 'info'
        }
        
        response = self.client.post(reverse('notifications'), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'New Notification')
    
    def test_get_notification_detail(self):
        """Test getting notification details."""
        self.client.force_authenticate(user=self.user)
        notification = self.notifications[0]
        
        response = self.client.get(reverse('notification-detail', args=[notification.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], notification.id)
    
    def test_mark_notification_as_read(self):
        """Test marking notification as read."""
        self.client.force_authenticate(user=self.user)
        notification = self.notifications[0]
        
        # Initially unread
        self.assertFalse(notification.read)
        
        response = self.client.post(reverse('notification-mark-read'), {
            'notification_id': notification.id
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Verify notification is marked as read
        notification.refresh_from_db()
        self.assertTrue(notification.read)
    
    def test_mark_all_notifications_as_read(self):
        """Test marking all notifications as read."""
        self.client.force_authenticate(user=self.user)
        
        # Verify all are unread initially
        unread_count = Notification.objects.filter(user=self.user, read=False).count()
        self.assertEqual(unread_count, 3)
        
        response = self.client.post(reverse('notification-mark-all-read'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)
        
        # Verify all are read
        unread_count = Notification.objects.filter(user=self.user, read=False).count()
        self.assertEqual(unread_count, 0)
    
    def test_get_unread_count(self):
        """Test getting unread notification count."""
        self.client.force_authenticate(user=self.user)
        
        # Clear cache to ensure fresh count
        from django.core.cache import cache
        cache.delete(f"unread_notifications_{self.user.id}")
        
        response = self.client.get(reverse('notification-unread-count'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['unread_count'], 3)
    
    def test_delete_notification(self):
        """Test deleting a notification using RESTful DELETE endpoint."""
        self.client.force_authenticate(user=self.user)
        notification = self.notifications[0]
        
        # Use the RESTful DELETE endpoint instead of POST
        response = self.client.delete(reverse('notification-detail', args=[notification.id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify notification is deleted
        self.assertFalse(Notification.objects.filter(id=notification.id).exists())
    
    def test_get_notification_stats(self):
        """Test getting notification statistics."""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.get(reverse('notification-stats'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.data
        self.assertEqual(data['total_count'], 3)
        self.assertEqual(data['unread_count'], 3)
        self.assertEqual(data['read_count'], 0)
        self.assertIn('info', data['by_type'])
        self.assertEqual(data['by_type']['info'], 3)
    
    def test_create_system_notification_admin(self):
        """Test creating system notification as admin."""
        self.client.force_authenticate(user=self.admin_user)
        
        data = {
            'title': 'System Maintenance',
            'message': 'System will be down for maintenance',
            'link': 'https://example.com/maintenance'
        }
        
        response = self.client.post(reverse('system-notification'), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Both admin and regular user get notified since they're both active users
        self.assertEqual(response.data['count'], 2)
    
    def test_create_system_notification_non_admin(self):
        """Test creating system notification as non-admin (should fail)."""
        self.client.force_authenticate(user=self.user)
        
        data = {
            'title': 'System Maintenance',
            'message': 'System will be down for maintenance'
        }
        
        response = self.client.post(reverse('system-notification'), data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_cleanup_notifications_admin(self):
        """Test cleaning up old notifications as admin."""
        self.client.force_authenticate(user=self.admin_user)
        
        # Create old notification
        old_notification = Notification.objects.create(
            user=self.user,
            title='Old Notification',
            message='This is an old notification'
        )
        # Manually set the created_at to be old
        old_notification.created_at = timezone.now() - timedelta(days=31)
        old_notification.save()
        
        response = self.client.post(reverse('notification-cleanup'), {'days': 30}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['deleted_count'], 1)
    
    def test_cleanup_notifications_non_admin(self):
        """Test cleaning up notifications as non-admin (should fail)."""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.post(reverse('notification-cleanup'), {'days': 30})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class NotificationIntegrationTest(TestCase):
    """Test notification integration with other parts of the system."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            name='Test User'
        )
    
    def test_login_creates_notification(self):
        """Test that login creates a notification."""
        # Login
        response = self.client.post(reverse('login'), {
            'email': 'test@example.com',
            'password': 'testpass123'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that notification was created
        notification = Notification.objects.filter(
            user=self.user,
            notification_type='security',
            title='Login Successful'
        ).first()
        
        self.assertIsNotNone(notification)
        self.assertIn('Successful login to your account', notification.message)
    
    def test_password_change_creates_notification(self):
        """Test that password change creates a notification."""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.post(reverse('change-password'), {
            'old_password': 'testpass123',
            'new_password': 'NewPass123!'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that notification was created
        notification = Notification.objects.filter(
            user=self.user,
            notification_type='security',
            title='Password Changed'
        ).first()
        
        self.assertIsNotNone(notification)
        self.assertIn('Your password has been changed successfully', notification.message)


class NotificationSecurityTest(TestCase):
    """Test notification security features."""
    
    def setUp(self):
        self.client = APIClient()
        self.user1 = User.objects.create_user(
            email='user1@example.com',
            password='testpass123',
            name='User 1'
        )
        self.user2 = User.objects.create_user(
            email='user2@example.com',
            password='testpass123',
            name='User 2'
        )
        
        # Create notifications for both users
        self.notification1 = Notification.objects.create(
            user=self.user1,
            title='User 1 Notification',
            message='This is user 1 notification'
        )
        self.notification2 = Notification.objects.create(
            user=self.user2,
            title='User 2 Notification',
            message='This is user 2 notification'
        )
    
    def test_user_cannot_access_other_user_notifications(self):
        """Test that users cannot access other users' notifications."""
        self.client.force_authenticate(user=self.user1)
        
        # Try to access user2's notification
        response = self.client.get(reverse('notification-detail', args=[self.notification2.id]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_user_cannot_mark_other_user_notification_as_read(self):
        """Test that users cannot mark other users' notifications as read."""
        self.client.force_authenticate(user=self.user1)
        
        response = self.client.post(reverse('notification-mark-read'), {
            'notification_id': self.notification2.id
        })
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Verify notification is still unread
        self.notification2.refresh_from_db()
        self.assertFalse(self.notification2.read)
    
    def test_user_cannot_delete_other_user_notification(self):
        """Test that users cannot delete other users' notifications using RESTful DELETE."""
        self.client.force_authenticate(user=self.user1)
        
        # Use the RESTful DELETE endpoint instead of POST
        response = self.client.delete(reverse('notification-detail', args=[self.notification2.id]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Verify notification still exists
        self.assertTrue(Notification.objects.filter(id=self.notification2.id).exists())
    
    def test_xss_prevention(self):
        """Test that XSS attacks are prevented."""
        self.client.force_authenticate(user=self.user1)
        
        data = {
            'title': '<script>alert("XSS")</script>Test Title',
            'message': 'Test message',
            'notification_type': 'info'
        }
        
        response = self.client.post(reverse('notifications'), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Get the created notification
        notification = Notification.objects.get(id=response.data['id'])
        
        # The title should be sanitized (no script tags)
        self.assertNotIn('<script>', notification.title)
        self.assertIn('Test Title', notification.title) 