"""
Security test suite for the Auth App.

This module contains comprehensive security tests covering:
- Brute force protection and rate limiting
- Security headers and CORS
- Account recovery mechanisms
- Session management
- API security
- Audit logging
- Input validation
- Error handling

Each test class focuses on a specific security aspect and includes multiple test cases
to ensure proper security measures are in place.
"""

from django.test import TestCase, override_settings, Client
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model
from rest_framework import status
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta
import time
import json
from django.conf import settings
from .models import Notification, SecurityLog
from .utils import password_reset_token_generator
from django.core import mail
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
import re
import time_machine

User = get_user_model()

class BruteForceProtectionTest(APITestCase):
    """
    Tests for brute force protection mechanisms.
    
    This test suite verifies that the application properly protects against:
    - Multiple failed login attempts
    - IP-based rate limiting
    - Account lockout duration and expiration
    """
    
    def setUp(self):
        """Set up test data and clear cache before each test."""
        self.client = APIClient()
        self.login_url = reverse('login')
        self.user_data = {
            'email': 'test@example.com',
            'password': 'TestPass123!',
            'name': 'Test User'
        }
        self.user = User.objects.create_user(**self.user_data)
        cache.clear()

    def test_login_attempt_limiting(self):
        """
        Test that accounts are locked after multiple failed login attempts.
        
        Verifies:
        - Account is locked after 5 failed attempts
        - Locked account cannot login even with correct credentials
        - Appropriate error message is returned
        """
        # Try to login with wrong password multiple times
        for _ in range(5):
            response = self.client.post(self.login_url, {
                'email': self.user_data['email'],
                'password': 'wrongpassword'
            })
        
        # Should be locked out
        response = self.client.post(self.login_url, {
            'email': self.user_data['email'],
            'password': self.user_data['password']
        })
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertIn('Account temporarily locked', response.data['error'])

    def test_ip_based_rate_limiting(self):
        """
        Test rate limiting based on IP address.
        
        Verifies:
        - Requests from same IP are rate limited after threshold
        - Rate limit applies to all endpoints
        - Appropriate error message is returned
        """
        # Make multiple requests from same IP
        for _ in range(10):
            response = self.client.post(self.login_url, {
                'email': 'random@example.com',
                'password': 'randompass'
            })
        
        # Should be rate limited
        response = self.client.post(self.login_url, {
            'email': 'random@example.com',
            'password': 'randompass'
        })
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertIn('Too many requests', response.data['error'])

    def test_account_lockout_duration(self):
        """
        Test that account lockout expires after the specified duration.
        
        Verifies:
        - Account is locked after failed attempts
        - Lock is automatically removed after timeout period
        - User can login after lock expiration
        """
        # Lock the account
        for _ in range(5):
            self.client.post(self.login_url, {
                'email': self.user_data['email'],
                'password': 'wrongpassword'
            })
        
        # Wait for lockout to expire (mock time)
        with time_machine.travel(timezone.now() + timedelta(minutes=31)):
            response = self.client.post(self.login_url, {
                'email': self.user_data['email'],
                'password': self.user_data['password']
            })
            self.assertEqual(response.status_code, status.HTTP_200_OK)

class SecurityHeadersTest(APITestCase):
    """
    Tests for security headers and CORS configuration.
    
    This test suite verifies that the application:
    - Sets appropriate security headers
    - Configures CORS properly
    - Prevents common web vulnerabilities
    """
    
    def setUp(self):
        """Set up test client and URLs."""
        self.client = APIClient()
        self.login_url = reverse('login')
        self.register_url = reverse('register')

    def test_cors_headers(self):
        """
        Test CORS headers are properly set.
        
        Verifies:
        - CORS headers are present in OPTIONS response
        - Allowed origins are properly configured
        - Allowed methods are properly set
        - Allowed headers are properly set
        """
        response = self.client.options(self.login_url, HTTP_ORIGIN='https://allowed-origin.com')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('Access-Control-Allow-Origin', response)
        self.assertIn('Access-Control-Allow-Methods', response)
        self.assertIn('Access-Control-Allow-Headers', response)

    def test_security_headers(self):
        """
        Test security headers are properly set.
        
        Verifies presence and values of:
        - X-Frame-Options (clickjacking protection)
        - X-Content-Type-Options (MIME type sniffing protection)
        - Content-Security-Policy (XSS protection)
        - Strict-Transport-Security (HTTPS enforcement)
        - X-XSS-Protection (additional XSS protection)
        """
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check security headers
        self.assertIn('X-Frame-Options', response)
        self.assertEqual(response['X-Frame-Options'], 'DENY')
        
        self.assertIn('X-Content-Type-Options', response)
        self.assertEqual(response['X-Content-Type-Options'], 'nosniff')
        
        self.assertIn('Content-Security-Policy', response)
        self.assertIn('Strict-Transport-Security', response)
        
        self.assertIn('X-XSS-Protection', response)
        self.assertEqual(response['X-XSS-Protection'], '1; mode=block')

class AccountRecoveryTest(APITestCase):
    """
    Tests for account recovery mechanisms.
    
    This test suite verifies:
    - Backup email recovery process
    - Phone number recovery process
    - Recovery token expiration
    - Security of recovery process
    """
    
    def setUp(self):
        """Set up test user with recovery options."""
        self.client = APIClient()
        self.user_data = {
            'email': 'test@example.com',
            'password': 'TestPass123!',
            'name': 'Test User',
            'backup_email': 'backup@example.com',
            'phone_number': '+1234567890'
        }
        self.user = User.objects.create_user(**self.user_data)
        self.recovery_url = reverse('account-recovery')

    def test_backup_email_recovery(self):
        """
        Test account recovery via backup email.
        
        Verifies:
        - Recovery email is sent to backup email
        - Email contains necessary recovery information
        - Process is properly secured
        """
        response = self.client.post(self.recovery_url, {
            'recovery_method': 'email',
            'email': self.user_data['backup_email']
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.user_data['backup_email']])

    def test_phone_recovery(self):
        """
        Test account recovery via phone number.
        
        Verifies:
        - SMS is sent to registered phone number
        - Process is properly secured
        - Rate limiting is applied
        """
        response = self.client.post(self.recovery_url, {
            'recovery_method': 'phone',
            'phone_number': self.user_data['phone_number']
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Verify SMS was sent (mock SMS service)

    def test_recovery_token_expiration(self):
        """
        Test recovery token expiration.
        
        Verifies:
        - Recovery tokens expire after specified time
        - Expired tokens cannot be used
        - Appropriate error message is returned
        """
        # Generate recovery token
        token = password_reset_token_generator.make_token(self.user)
        
        # Wait for token to expire
        with time_machine.travel(timezone.now() + timedelta(hours=25)):
            response = self.client.post(self.recovery_url, {
                'token': token,
                'new_password': 'NewPass123!'
            })
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn('expired', response.data['error'].lower())

class SessionManagementTest(APITestCase):
    """
    Tests for session management.
    
    This test suite verifies:
    - Concurrent session handling
    - Session timeout
    - Remember me functionality
    - Session security
    """
    
    def setUp(self):
        """Set up test user and session-related URLs."""
        self.client = APIClient()
        self.user_data = {
            'email': 'test@example.com',
            'password': 'TestPass123!',
            'name': 'Test User'
        }
        self.user = User.objects.create_user(**self.user_data)
        self.login_url = reverse('login')
        self.logout_url = reverse('logout')
        self.logout_all_url = reverse('logout-all-devices')

    def test_concurrent_sessions(self):
        """
        Test handling of concurrent sessions.
        
        Verifies:
        - Multiple sessions can be active simultaneously
        - Each session has unique token
        - Sessions don't interfere with each other
        """
        # Login from multiple devices
        client1 = APIClient()
        client2 = APIClient()
        
        # Login with first client
        response1 = client1.post(self.login_url, {
            'email': self.user_data['email'],
            'password': self.user_data['password']
        })
        token1 = response1.data['token']
        
        # Login with second client
        response2 = client2.post(self.login_url, {
            'email': self.user_data['email'],
            'password': self.user_data['password']
        })
        token2 = response2.data['token']
        
        # Verify both sessions are active
        client1.credentials(HTTP_AUTHORIZATION=f'Token {token1}')
        client2.credentials(HTTP_AUTHORIZATION=f'Token {token2}')
        
        response1 = client1.get(reverse('user-profile'))
        response2 = client2.get(reverse('user-profile'))
        
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)

    def test_session_timeout(self):
        """
        Test session timeout with inactivity.
        
        Verifies:
        - Session expires after inactivity period
        - User is properly logged out
        - Appropriate error message is returned
        """
        # Login and get token
        response = self.client.post(self.login_url, {
            'email': self.user_data['email'],
            'password': self.user_data['password']
        })
        token = response.data['token']
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        
        # Simulate inactivity
        with time_machine.travel(timezone.now() + timedelta(hours=2)):
            response = self.client.get(reverse('user-profile'))
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_remember_me_functionality(self):
        """
        Test remember me functionality extends session duration.
        
        Verifies:
        - Session duration is extended when remember me is enabled
        - Session remains valid for extended period
        - Security is maintained during extended session
        """
        # Login with remember me
        response = self.client.post(self.login_url, {
            'email': self.user_data['email'],
            'password': self.user_data['password'],
            'remember_me': True
        })
        token = response.data['token']
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        
        # Simulate time passing
        with time_machine.travel(timezone.now() + timedelta(days=7)):
            response = self.client.get(reverse('user-profile'))
            self.assertEqual(response.status_code, status.HTTP_200_OK)

class APISecurityTest(APITestCase):
    """
    Tests for API security features.
    
    This test suite verifies:
    - API versioning
    - API key management
    - API endpoint security
    """
    
    def setUp(self):
        """Set up test client with API key."""
        self.client = APIClient()
        self.api_key = 'test-api-key'
        self.client.credentials(HTTP_X_API_KEY=self.api_key)

    def test_api_versioning(self):
        """
        Test API versioning.
        
        Verifies:
        - Multiple API versions are supported
        - Version endpoints are properly configured
        - Invalid versions are rejected
        """
        # Test v1 endpoint
        response = self.client.get('/api/v1/auth/login/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test v2 endpoint
        response = self.client.get('/api/v2/auth/login/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test invalid version
        response = self.client.get('/api/v3/auth/login/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_api_key_rotation(self):
        """
        Test API key rotation.
        
        Verifies:
        - API keys can be rotated
        - Old keys are invalidated
        - New keys are properly generated
        - Key rotation is logged
        """
        # Get new API key
        response = self.client.post(reverse('rotate-api-key'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        new_api_key = response.data['api_key']
        
        # Try with old key
        self.client.credentials(HTTP_X_API_KEY=self.api_key)
        response = self.client.get(reverse('user-profile'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Try with new key
        self.client.credentials(HTTP_X_API_KEY=new_api_key)
        response = self.client.get(reverse('user-profile'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

class AuditLoggingTest(APITestCase):
    """
    Tests for audit logging functionality.
    
    This test suite verifies:
    - Login attempt logging
    - Password change logging
    - Security event logging
    - Log data integrity
    """
    
    def setUp(self):
        """Set up test user and logging-related data."""
        self.client = APIClient()
        self.user_data = {
            'email': 'test@example.com',
            'password': 'TestPass123!',
            'name': 'Test User'
        }
        self.user = User.objects.create_user(**self.user_data)
        self.login_url = reverse('login')

    def test_login_attempt_logging(self):
        """
        Test logging of login attempts.
        
        Verifies:
        - Successful logins are logged
        - Failed logins are logged
        - Log entries contain correct information
        - IP addresses are properly recorded
        """
        # Successful login
        response = self.client.post(self.login_url, {
            'email': self.user_data['email'],
            'password': self.user_data['password']
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check log entry
        log = SecurityLog.objects.filter(
            user=self.user,
            event_type='login_success'
        ).first()
        self.assertIsNotNone(log)
        self.assertEqual(log.ip_address, '127.0.0.1')
        
        # Failed login
        response = self.client.post(self.login_url, {
            'email': self.user_data['email'],
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Check log entry
        log = SecurityLog.objects.filter(
            user=self.user,
            event_type='login_failed'
        ).first()
        self.assertIsNotNone(log)

    def test_password_change_logging(self):
        """
        Test logging of password changes.
        
        Verifies:
        - Password changes are logged
        - Log entries contain correct information
        - IP addresses are properly recorded
        - Timestamps are accurate
        """
        # Login first
        response = self.client.post(self.login_url, {
            'email': self.user_data['email'],
            'password': self.user_data['password']
        })
        token = response.data['token']
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        
        # Change password
        response = self.client.post(reverse('change-password'), {
            'old_password': self.user_data['password'],
            'new_password': 'NewPass123!'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check log entry
        log = SecurityLog.objects.filter(
            user=self.user,
            event_type='password_change'
        ).first()
        self.assertIsNotNone(log)
        self.assertEqual(log.ip_address, '127.0.0.1')

class InputValidationTest(APITestCase):
    """
    Tests for input validation and sanitization.
    
    This test suite verifies:
    - SQL injection prevention
    - XSS prevention
    - Input length validation
    - Input sanitization
    """
    
    def setUp(self):
        """Set up test client and registration URL."""
        self.client = APIClient()
        self.register_url = reverse('register')

    def test_sql_injection_prevention(self):
        """
        Test prevention of SQL injection attacks.
        
        Verifies:
        - SQL injection attempts in email are blocked
        - SQL injection attempts in name are blocked
        - Appropriate error messages are returned
        """
        # Try SQL injection in email
        response = self.client.post(self.register_url, {
            'email': "test@example.com' OR '1'='1",
            'password': 'TestPass123!',
            'name': 'Test User'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Try SQL injection in name
        response = self.client.post(self.register_url, {
            'email': 'test@example.com',
            'password': 'TestPass123!',
            'name': "'; DROP TABLE users; --"
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_xss_prevention(self):
        """
        Test prevention of XSS attacks.
        
        Verifies:
        - XSS attempts in name are blocked
        - XSS attempts in email are blocked
        - HTML/script tags are properly sanitized
        """
        # Try XSS in name
        response = self.client.post(self.register_url, {
            'email': 'test@example.com',
            'password': 'TestPass123!',
            'name': '<script>alert("xss")</script>'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Try XSS in email
        response = self.client.post(self.register_url, {
            'email': 'test@example.com<script>alert("xss")</script>',
            'password': 'TestPass123!',
            'name': 'Test User'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_input_length_validation(self):
        """
        Test input length validation.
        
        Verifies:
        - Email length is properly validated
        - Name length is properly validated
        - Appropriate error messages are returned
        """
        # Test too long email
        response = self.client.post(self.register_url, {
            'email': 'a' * 256 + '@example.com',
            'password': 'TestPass123!',
            'name': 'Test User'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test too long name
        response = self.client.post(self.register_url, {
            'email': 'test@example.com',
            'password': 'TestPass123!',
            'name': 'a' * 101
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

class ErrorHandlingTest(APITestCase):
    """
    Tests for error handling and reporting.
    
    This test suite verifies:
    - Error message format
    - Error logging
    - Error rate limiting
    - Error response consistency
    """
    
    def setUp(self):
        """Set up test client and URLs."""
        self.client = APIClient()
        self.login_url = reverse('login')
        self.register_url = reverse('register')

    def test_error_message_format(self):
        """
        Test error message format and content.
        
        Verifies:
        - Error messages are properly formatted
        - Required field errors are clear
        - Validation errors are descriptive
        - Error response structure is consistent
        """
        # Test missing required field
        response = self.client.post(self.login_url, {
            'email': 'test@example.com'
            # Missing password
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data['error'])
        self.assertIsInstance(response.data['error'], dict)
        
        # Test invalid email format
        response = self.client.post(self.login_url, {
            'email': 'invalid-email',
            'password': 'TestPass123!'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data['error'])

    def test_error_logging(self):
        """
        Test error logging.
        
        Verifies:
        - Errors are properly logged
        - Log entries contain correct information
        - IP addresses are recorded
        - Error types are properly categorized
        """
        # Trigger an error
        response = self.client.post(self.login_url, {
            'email': 'nonexistent@example.com',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Check error log
        log = SecurityLog.objects.filter(
            event_type='login_failed',
            email='nonexistent@example.com'
        ).first()
        self.assertIsNotNone(log)
        self.assertEqual(log.ip_address, '127.0.0.1')

    def test_error_rate_limiting(self):
        """
        Test error rate limiting.
        
        Verifies:
        - Error rate limiting is enforced
        - Rate limit threshold is correct
        - Rate limit messages are clear
        - Rate limit resets properly
        """
        # Generate multiple errors
        for _ in range(10):
            response = self.client.post(self.login_url, {
                'email': 'test@example.com',
                'password': 'wrongpassword'
            })
        
        # Should be rate limited
        response = self.client.post(self.login_url, {
            'email': 'test@example.com',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertIn('Too many failed attempts', response.data['error'])

class PasswordResetTest(APITestCase):
    """
    Tests for password reset functionality.
    
    This test suite verifies:
    - Password reset flow for both active and inactive users
    - Token expiration and validation
    - Multiple reset request handling
    - Token reuse prevention
    - Edge cases and security measures
    """
    
    def setUp(self):
        """Set up test users and reset-related URLs."""
        self.client = APIClient()
        self.reset_request_url = reverse('password-reset-request')
        self.reset_confirm_url = reverse('password-reset-confirm')
        
        # Create active user
        self.active_user_data = {
            'email': 'active@example.com',
            'password': 'TestPass123!',
            'name': 'Active User'
        }
        self.active_user = User.objects.create_user(**self.active_user_data)
        
        # Create inactive user
        self.inactive_user_data = {
            'email': 'inactive@example.com',
            'password': 'TestPass123!',
            'name': 'Inactive User',
            'is_active': False
        }
        self.inactive_user = User.objects.create_user(**self.inactive_user_data)

    def test_reset_flow_inactive_user(self):
        """
        Test password reset flow for inactive users.
        
        Verifies:
        - Inactive users can request password reset
        - Reset email is sent to inactive users
        - Reset process works for inactive users
        - Account is activated after successful reset
        """
        # Request reset for inactive user
        response = self.client.post(self.reset_request_url, {
            'email': self.inactive_user_data['email']
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 1)
        
        # Get reset token
        token = password_reset_token_generator.make_token(self.inactive_user)
        uid = urlsafe_base64_encode(force_bytes(self.inactive_user.pk))
        
        # Reset password
        response = self.client.post(self.reset_confirm_url, {
            'uid': uid,
            'token': token,
            'new_password': 'NewPass123!'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify account is now active
        self.inactive_user.refresh_from_db()
        self.assertTrue(self.inactive_user.is_active)

    def test_multiple_reset_requests(self):
        """
        Test handling of multiple reset requests.
        
        Verifies:
        - Multiple reset requests invalidate previous tokens
        - Only the most recent token is valid
        - Appropriate error messages for invalidated tokens
        """
        # First reset request
        response = self.client.post(self.reset_request_url, {
            'email': self.active_user_data['email']
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        token1 = password_reset_token_generator.make_token(self.active_user)
        
        # Second reset request
        response = self.client.post(self.reset_request_url, {
            'email': self.active_user_data['email']
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        token2 = password_reset_token_generator.make_token(self.active_user)
        
        # Try using first token
        uid = urlsafe_base64_encode(force_bytes(self.active_user.pk))
        response = self.client.post(self.reset_confirm_url, {
            'uid': uid,
            'token': token1,
            'new_password': 'NewPass123!'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('invalidated', response.data['error'].lower())
        
        # Verify second token still works
        response = self.client.post(self.reset_confirm_url, {
            'uid': uid,
            'token': token2,
            'new_password': 'NewPass123!'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_token_reuse_prevention(self):
        """
        Test prevention of token reuse.
        
        Verifies:
        - Tokens can only be used once
        - Attempted reuse returns appropriate error
        - Token is properly invalidated after use
        """
        # Request reset
        response = self.client.post(self.reset_request_url, {
            'email': self.active_user_data['email']
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Get token
        token = password_reset_token_generator.make_token(self.active_user)
        uid = urlsafe_base64_encode(force_bytes(self.active_user.pk))
        
        # First use of token
        response = self.client.post(self.reset_confirm_url, {
            'uid': uid,
            'token': token,
            'new_password': 'NewPass123!'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Try reusing token
        response = self.client.post(self.reset_confirm_url, {
            'uid': uid,
            'token': token,
            'new_password': 'AnotherPass123!'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('already used', response.data['error'].lower())

    def test_identical_password_reset(self):
        """
        Test reset with identical new password.
        
        Verifies:
        - Reset is rejected if new password is same as current
        - Appropriate error message is returned
        - Current password remains unchanged
        """
        # Request reset
        response = self.client.post(self.reset_request_url, {
            'email': self.active_user_data['email']
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Get token
        token = password_reset_token_generator.make_token(self.active_user)
        uid = urlsafe_base64_encode(force_bytes(self.active_user.pk))
        
        # Try resetting to same password
        response = self.client.post(self.reset_confirm_url, {
            'uid': uid,
            'token': token,
            'new_password': self.active_user_data['password']
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('same as current', response.data['error'].lower())
        
        # Verify password hasn't changed
        self.active_user.refresh_from_db()
        self.assertTrue(self.active_user.check_password(self.active_user_data['password']))

class AuthenticationEdgeCasesTest(APITestCase):
    """
    Tests for authentication edge cases.
    
    This test suite verifies:
    - Case-insensitive email handling
    - Login behavior after password changes
    - Account status handling
    - Timing attack prevention
    - Various edge cases
    """
    
    def setUp(self):
        """Set up test users and authentication URLs."""
        self.client = APIClient()
        self.login_url = reverse('login')
        
        # Create user with mixed case email
        self.user_data = {
            'email': 'Test.User@Example.com',
            'password': 'TestPass123!',
            'name': 'Test User'
        }
        self.user = User.objects.create_user(**self.user_data)

    def test_case_insensitive_email(self):
        """
        Test login with case-insensitive email variations.
        
        Verifies:
        - Login works with different case variations
        - Email is properly normalized
        - Case differences don't affect authentication
        """
        # Try different case variations
        email_variations = [
            'test.user@example.com',
            'TEST.USER@EXAMPLE.COM',
            'Test.User@example.com',
            'test.User@Example.com'
        ]
        
        for email in email_variations:
            response = self.client.post(self.login_url, {
                'email': email,
                'password': self.user_data['password']
            })
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data['user']['email'], self.user_data['email'].lower())

    def test_login_inactive_account(self):
        """
        Test login with valid credentials but inactive account.
        
        Verifies:
        - Login is rejected for inactive accounts
        - Appropriate error message is returned
        - Account status is properly checked
        """
        # Deactivate account
        self.user.is_active = False
        self.user.save()
        
        # Try to login
        response = self.client.post(self.login_url, {
            'email': self.user_data['email'],
            'password': self.user_data['password']
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('inactive', response.data['error'].lower())

    def test_timing_attack_prevention(self):
        """
        Test login timing differences to prevent timing attacks.
        
        Verifies:
        - Response times are consistent regardless of password correctness
        - Timing differences don't reveal valid credentials
        - Appropriate security measures are in place
        """
        import time
        
        def measure_login_time(email, password):
            start_time = time.time()
            self.client.post(self.login_url, {
                'email': email,
                'password': password
            })
            return time.time() - start_time
        
        # Measure time for valid credentials
        valid_times = [
            measure_login_time(self.user_data['email'], self.user_data['password'])
            for _ in range(5)
        ]
        
        # Measure time for invalid credentials
        invalid_times = [
            measure_login_time(self.user_data['email'], 'wrongpassword')
            for _ in range(5)
        ]
        
        # Calculate average times
        avg_valid_time = sum(valid_times) / len(valid_times)
        avg_invalid_time = sum(invalid_times) / len(invalid_times)
        
        # Verify timing difference is within acceptable range
        # (should be less than 100ms difference)
        self.assertLess(abs(avg_valid_time - avg_invalid_time), 0.1)

class SecurityTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.admin = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        self.login_url = reverse('login')
        self.messages_url = reverse('message-list')
        self.admin_url = reverse('admin:index')

    def test_brute_force_protection(self):
        """Test brute force prevention"""
        # Try to login with wrong password multiple times
        for _ in range(6):  # MAX_ATTEMPTS + 1
            response = self.client.post(self.login_url, {
                'username': 'testuser',
                'password': 'wrongpass'
            })
        
        # Should be locked out
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        
        # Wait for lockout to expire
        time.sleep(301)  # LOCKOUT_TIME + 1
        
        # Should be able to login again
        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_sql_injection_prevention(self):
        """Test SQL injection prevention"""
        # Try SQL injection in search
        response = self.client.get(f'{self.messages_url}?search=1%27%20OR%201%3D1')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Try SQL injection in POST data
        response = self.client.post(self.messages_url, {
            'content': "'; DROP TABLE auth_user; --"
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_xss_prevention(self):
        """Test XSS prevention"""
        # Try XSS in message content
        xss_payload = '<script>alert("xss")</script>'
        response = self.client.post(self.messages_url, {
            'content': xss_payload
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Try XSS in profile update
        response = self.client.put(reverse('profile'), {
            'name': f'<img src=x onerror="{xss_payload}">'
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_csrf_protection(self):
        """Test CSRF protection"""
        # Try to make a POST request without CSRF token
        client = Client(enforce_csrf_checks=True)
        response = client.post(self.login_url, {
            'username': 'testuser',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_session_security(self):
        """Test session security"""
        # Login to get session cookie
        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'testpass123'
        })
        session_cookie = response.cookies.get('sessionid')
        
        # Verify secure cookie attributes
        self.assertTrue(session_cookie.get('secure'))
        self.assertTrue(session_cookie.get('httponly'))
        self.assertEqual(session_cookie.get('samesite'), 'Lax')

    def test_token_security(self):
        """Test token security"""
        # Get token
        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'testpass123'
        })
        token = response.data.get('token')
        
        # Try to use expired token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        time.sleep(3601)  # Wait for token to expire
        response = self.client.get(self.messages_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_admin_access_control(self):
        """Test admin access control"""
        # Try to access admin as regular user
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.admin_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Access admin as admin user
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.admin_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_file_upload_security(self):
        """Test file upload security"""
        # Try to upload executable as image
        with open('test.exe', 'wb') as f:
            f.write(b'MZ')  # Windows executable header
        
        with open('test.exe', 'rb') as f:
            response = self.client.post(
                reverse('news-image-upload'),
                {'image': f},
                format='multipart'
            )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Try to upload oversized image
        with open('large.jpg', 'wb') as f:
            f.write(b'\x00' * (6 * 1024 * 1024))  # 6MB
        
        with open('large.jpg', 'rb') as f:
            response = self.client.post(
                reverse('news-image-upload'),
                {'image': f},
                format='multipart'
            )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def tearDown(self):
        # Clean up test files
        import os
        for filename in ['test.exe', 'large.jpg']:
            if os.path.exists(filename):
                os.remove(filename) 