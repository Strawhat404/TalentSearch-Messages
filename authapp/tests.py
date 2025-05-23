from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from .models import Notification
from django.urls import reverse
from django.core import mail
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from .utils import password_reset_token_generator
from django.utils import timezone
from datetime import timedelta
from django.test.utils import freeze_time
import time_machine
from django.conf import settings
from django.utils.crypto import get_random_string
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework_simplejwt.tokens import AccessToken
from datetime import datetime
from rest_framework.test import APITestCase
import time

User = get_user_model()

class UserModelTest(TestCase):
    def setUp(self):
        self.user_data = {
            'email': 'test@example.com',
            'password': 'testpass123',
            'name': 'Test User'
        }
        self.user = User.objects.create_user(**self.user_data)

    def test_create_user(self):
        """Test user creation with required fields"""
        self.assertEqual(self.user.email, self.user_data['email'])
        self.assertEqual(self.user.name, self.user_data['name'])
        self.assertTrue(self.user.check_password(self.user_data['password']))
        self.assertFalse(self.user.is_staff)
        self.assertFalse(self.user.is_superuser)

    def test_create_superuser(self):
        """Test superuser creation"""
        admin_data = {
            'email': 'admin@example.com',
            'password': 'adminpass123',
            'name': 'Admin User'
        }
        admin = User.objects.create_superuser(**admin_data)
        self.assertEqual(admin.email, admin_data['email'])
        self.assertEqual(admin.name, admin_data['name'])
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)

    def test_user_str(self):
        """Test user string representation"""
        self.assertEqual(str(self.user), self.user.email)

class NotificationModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            name='Test User'
        )
        self.notification = Notification.objects.create(
            user=self.user,
            title='Test Notification',
            message='This is a test notification',
            notification_type='info'
        )

    def test_notification_creation(self):
        """Test notification creation with required fields"""
        self.assertEqual(self.notification.user, self.user)
        self.assertEqual(self.notification.title, 'Test Notification')
        self.assertEqual(self.notification.message, 'This is a test notification')
        self.assertEqual(self.notification.notification_type, 'info')
        self.assertFalse(self.notification.read)

    def test_notification_str(self):
        """Test notification string representation"""
        expected_str = f"Test Notification - {self.user.email}"
        self.assertEqual(str(self.notification), expected_str)

class AuthViewsTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.register_url = reverse('register')
        self.login_url = reverse('login')
        self.admin_login_url = reverse('admin-login')
        self.forgot_password_url = reverse('forgot-password')
        self.reset_password_url = reverse('reset-password')
        
        # Create test user
        self.user_data = {
            'email': 'test@example.com',
            'password': 'testpass123',
            'name': 'Test User'
        }
        self.user = User.objects.create_user(**self.user_data)
        
        # Create admin user
        self.admin_data = {
            'email': 'admin@example.com',
            'password': 'adminpass123',
            'name': 'Admin User'
        }
        self.admin = User.objects.create_superuser(**self.admin_data)

    def test_register_user(self):
        """Test user registration"""
        data = {
            'email': 'newuser@example.com',
            'password': 'newpass123',
            'name': 'New User'
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('token', response.data)
        self.assertEqual(response.data['email'], data['email'])
        self.assertEqual(response.data['name'], data['name'])

    def test_login_user(self):
        """Test user login"""
        data = {
            'email': self.user_data['email'],
            'password': self.user_data['password']
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
        self.assertEqual(response.data['user']['email'], self.user_data['email'])

    def test_admin_login(self):
        """Test admin login"""
        data = {
            'email': self.admin_data['email'],
            'password': self.admin_data['password']
        }
        response = self.client.post(self.admin_login_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
        self.assertEqual(response.data['role'], 'admin')

    def test_forgot_password(self):
        """Test forgot password flow"""
        data = {'email': self.user_data['email']}
        response = self.client.post(self.forgot_password_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.user_data['email']])

    def test_reset_password(self):
        """Test password reset"""
        # Generate token
        token = password_reset_token_generator.make_token(self.user)
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        
        data = {
            'uid': uid,
            'token': token,
            'new_password': 'newpass123'
        }
        response = self.client.post(self.reset_password_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify new password works
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newpass123'))

    def test_reset_password_invalid_token(self):
        """Test password reset with invalid token"""
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        data = {
            'uid': uid,
            'token': 'invalid-token',
            'new_password': 'newpass123'
        }
        response = self.client.post(self.reset_password_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'Invalid or expired token')

    def test_reset_password_expired_token(self):
        """Test password reset with expired token"""
        # Generate token
        current_time = timezone.now()
        with time_machine.travel(current_time):
            token = password_reset_token_generator.make_token(self.user)
            uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        
        # Travel 25 hours into the future
        future_time = current_time + timedelta(hours=25)
        with time_machine.travel(future_time):
            data = {
                'uid': uid,
                'token': token,
                'new_password': 'newpass123'
            }
            response = self.client.post(self.reset_password_url, data)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(response.data['error'], 'Invalid or expired token')

    def test_reset_password_missing_fields(self):
        """Test password reset with missing required fields"""
        # Test missing token
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        data = {
            'uid': uid,
            'new_password': 'newpass123'
        }
        response = self.client.post(self.reset_password_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'UID, token, and new password are required')

        # Test missing password
        token = password_reset_token_generator.make_token(self.user)
        data = {
            'uid': uid,
            'token': token
        }
        response = self.client.post(self.reset_password_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'UID, token, and new password are required')

    def test_reset_password_invalid_uid(self):
        """Test password reset with invalid user ID"""
        token = password_reset_token_generator.make_token(self.user)
        data = {
            'uid': 'invalid-uid',
            'token': token,
            'new_password': 'newpass123'
        }
        response = self.client.post(self.reset_password_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'Invalid or expired token')

    def test_reset_password_nonexistent_user(self):
        """Test password reset for non-existent user"""
        # Generate token for non-existent user ID
        nonexistent_uid = urlsafe_base64_encode(force_bytes(99999))  # Assuming this ID doesn't exist
        token = password_reset_token_generator.make_token(self.user)  # Using valid token format
        data = {
            'uid': nonexistent_uid,
            'token': token,
            'new_password': 'newpass123'
        }
        response = self.client.post(self.reset_password_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'Invalid or expired token')

    def test_forgot_password_nonexistent_email(self):
        """Test forgot password with non-existent email"""
        data = {'email': 'nonexistent@example.com'}
        response = self.client.post(self.forgot_password_url, data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['error'], 'User with this email does not exist')

    def test_forgot_password_missing_email(self):
        """Test forgot password with missing email"""
        data = {}
        response = self.client.post(self.forgot_password_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'Email is required')

    def test_forgot_password_invalid_email_format(self):
        """Test forgot password with invalid email format"""
        data = {'email': 'invalid-email'}
        response = self.client.post(self.forgot_password_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

class NotificationViewsTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            name='Test User'
        )
        self.notification_url = reverse('notifications')
        
        # Create some notifications
        self.notifications = [
            Notification.objects.create(
                user=self.user,
                title=f'Test Notification {i}',
                message=f'This is test notification {i}',
                notification_type='info'
            ) for i in range(3)
        ]

    def test_get_notifications_authenticated(self):
        """Test getting notifications for authenticated user"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.notification_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_get_notifications_unauthenticated(self):
        """Test getting notifications without authentication"""
        response = self.client.get(self.notification_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

class PasswordResetTokenTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            name='Test User'
        )
        self.client = APIClient()
        self.notifications_url = reverse('notifications')

    def test_token_expiration(self):
        """Test that password reset tokens expire after 24 hours"""
        # Generate a token with current time
        current_time = timezone.now()
        with time_machine.travel(current_time):
            token = password_reset_token_generator.make_token(self.user)
            # Verify token is valid initially
            self.assertTrue(password_reset_token_generator.check_token(self.user, token))
        
        # Travel 25 hours into the future and verify token is expired
        future_time = current_time + timedelta(hours=25)
        with time_machine.travel(future_time):
            self.assertFalse(password_reset_token_generator.check_token(self.user, token))

    def test_token_invalidation_after_password_change(self):
        """Test that tokens are invalidated after password change"""
        # Get a token
        current_time = timezone.now()
        with time_machine.travel(current_time):
            response = self.client.post(reverse('token_obtain_pair'), {
                'email': self.user.email,
                'password': 'testpass123'
            })
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            token = response.data['access']

        # Change password
        self.user.set_password('newpassword123')
        self.user.save()

        # Try to use the old token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get(self.notifications_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        error_msg = str(response.data).lower()
        self.assertTrue(
            'token is invalid due to password change' in error_msg or 'token is expired' in error_msg,
            f"Unexpected error message: {error_msg}"
        )

    def test_token_for_new_user(self):
        """Test token generation for a new user who has never logged in"""
        new_user = User.objects.create_user(
            email='new@example.com',
            password='newpass123',
            name='New User'
        )
        # Verify new user has no last_login
        self.assertIsNone(new_user.last_login)
        
        # Generate and verify token
        token = password_reset_token_generator.make_token(new_user)
        self.assertTrue(password_reset_token_generator.check_token(new_user, token))

    def test_invalid_token_scenarios(self):
        """Test various invalid token scenarios"""
        # Generate valid token
        valid_token = password_reset_token_generator.make_token(self.user)
        
        # Test with wrong user
        other_user = User.objects.create_user(
            email='other@example.com',
            password='otherpass123',
            name='Other User'
        )
        self.assertFalse(password_reset_token_generator.check_token(other_user, valid_token))
        
        # Test with invalid token format
        self.assertFalse(password_reset_token_generator.check_token(self.user, 'invalid-token'))
        
        # Test with empty token
        self.assertFalse(password_reset_token_generator.check_token(self.user, ''))

    def test_token_reuse_prevention(self):
        """Test that using a token invalidates it for future use"""
        # Generate token
        token = password_reset_token_generator.make_token(self.user)
        
        # First use of token (simulating password reset)
        self.assertTrue(password_reset_token_generator.check_token(self.user, token))
        self.user.set_password('newpassword123')
        self.user.save()
        
        # Second use of same token should fail
        self.assertFalse(password_reset_token_generator.check_token(self.user, token))

class SecurityTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            name='Test User'
        )
        self.client = APIClient()
        self.notifications_url = reverse('notifications')
        # Do not force_authenticate or set session; rely only on JWT for authentication in these tests.

    def test_password_reset_token_expiration(self):
        """Test that password reset tokens expire after 24 hours"""
        # Request password reset
        response = self.client.post(reverse('forgot-password'), {
            'email': self.user.email
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Get token from email
        from django.core.mail import outbox
        self.assertTrue(len(outbox) > 0)
        token = outbox[0].body.split('token=')[1].split()[0]
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        
        # Try to reset password with valid token
        response = self.client.post(reverse('reset-password'), {
            'uid': uid,
            'token': token,
            'new_password': 'newpass123'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Generate new token and try to use it after expiration
        token = password_reset_token_generator.make_token(self.user)
        with time_machine.travel(timezone.now() + timedelta(hours=25)):
            response = self.client.post(reverse('reset-password'), {
                'uid': uid,
                'token': token,
                'new_password': 'newpass123'
            })
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn('expired', response.data['error'].lower())

    def test_token_authentication_expiration(self):
        """Test that authentication tokens expire after a short time"""
        # Set token lifetime to 1 second
        original_lifetime = settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME']
        settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'] = timedelta(seconds=1)

        try:
            # Get token at current time
            current_time = timezone.now()
            with time_machine.travel(current_time, tick=False):  # Don't let time tick
                response = self.client.post(reverse('token_obtain_pair'), {
                    'email': self.user.email,
                    'password': 'testpass123'
                })
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                token = response.data['access']

                # Verify token works initially
                self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
                response = self.client.get(self.notifications_url)
                self.assertEqual(response.status_code, status.HTTP_200_OK)

            # Travel 2 seconds into the future
            future_time = current_time + timedelta(seconds=2)
            with time_machine.travel(future_time, tick=False):  # Don't let time tick
                # Verify token is expired
                self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
                response = self.client.get(self.notifications_url)
                self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        finally:
            settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'] = original_lifetime

    def test_session_expiration(self):
        """Test that sessions expire after 1 hour"""
        self.client.login(email=self.user.email, password='testpass123')
        session = self.client.session
        session['last_login'] = (timezone.now() - timedelta(hours=2)).isoformat()
        session.save()
        response = self.client.get(self.notifications_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('expired', response.json()['error'].lower())

    def test_token_rotation(self):
        """Test that tokens are rotated on new login"""
        response = self.client.post(reverse('token_obtain_pair'), {
            'email': self.user.email,
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        initial_token = response.data['access']
        initial_refresh = response.data['refresh']
        response = self.client.post(reverse('token_obtain_pair'), {
            'email': self.user.email,
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        new_token = response.data['access']
        new_refresh = response.data['refresh']
        self.assertNotEqual(initial_token, new_token)
        self.assertNotEqual(initial_refresh, new_refresh)
        response = self.client.post(reverse('token_refresh'), {
            'refresh': initial_refresh
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_jwt_token_expiration(self):
        """Test that JWT tokens expire and refresh works"""
        # Set token lifetime to 1 second
        original_lifetime = settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME']
        settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'] = timedelta(seconds=1)

        try:
            # Get tokens at current time
            current_time = timezone.now()
            with time_machine.travel(current_time, tick=False):  # Don't let time tick
                # Get initial tokens
                response = self.client.post(reverse('token_obtain_pair'), {
                    'email': self.user.email,
                    'password': 'testpass123'
                })
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                access_token = response.data['access']
                refresh_token = response.data['refresh']

                # Verify token works initially
                self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
                response = self.client.get(self.notifications_url)
                self.assertEqual(response.status_code, status.HTTP_200_OK)

            # Travel 1 second into the future (not 2)
            future_time = current_time + timedelta(seconds=1)
            with time_machine.travel(future_time, tick=False):  # Don't let time tick
                # Verify access token is expired
                self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
                response = self.client.get(self.notifications_url)
                self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
                self.assertIn('expired', str(response.data).lower())

                # Get new tokens since the old ones are blacklisted
                response = self.client.post(reverse('token_obtain_pair'), {
                    'email': self.user.email,
                    'password': 'testpass123'
                })
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                new_access_token = response.data['access']
                new_refresh_token = response.data['refresh']

                # Verify new access token works
                self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {new_access_token}')
                response = self.client.get(self.notifications_url)
                print('DEBUG: new access token response:', response.status_code, response.data)
                self.assertEqual(response.status_code, status.HTTP_200_OK)

                # Verify old refresh token is blacklisted
                response = self.client.post(reverse('token_refresh'), {
                    'refresh': refresh_token
                })
                self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
                self.assertIn('blacklisted', str(response.data).lower())
        finally:
            settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'] = original_lifetime

    def test_token_invalidation_after_password_change(self):
        """Test that tokens are invalidated after password change"""
        # Get initial token
        current_time = timezone.now()
        with time_machine.travel(current_time, tick=False):  # Don't let time tick
            response = self.client.post(reverse('token_obtain_pair'), {
                'email': self.user.email,
                'password': 'testpass123'
            })
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            token = response.data['access']
            
            # Use token immediately - should work
            self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
            response = self.client.get(self.notifications_url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            
            # Change password
            response = self.client.post(reverse('password_change'), {
                'old_password': 'testpass123',
                'new_password': 'newpass123'
            })
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            
            # Try to use old token after password change - should get 401
            response = self.client.get(self.notifications_url)
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
            error_msg = str(response.data).lower()
            self.assertIn('token is invalid due to password change', error_msg)
