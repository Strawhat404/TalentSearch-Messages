from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

class TokenRefreshTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!',
            name='Test User'
        )
        
    def test_token_refresh_flow(self):
        """Test the complete token refresh flow"""
        
        # 1. Login to get initial tokens
        login_response = self.client.post('/auth/login/', {
            'email': 'test@example.com',
            'password': 'TestPass123!'
        })
        
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        self.assertIn('access', login_response.data)
        self.assertIn('refresh', login_response.data)
        
        access_token = login_response.data['access']
        refresh_token = login_response.data['refresh']
        
        # 2. Use access token to access protected endpoint
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        profile_response = self.client.get('/auth/token/status/')
        self.assertEqual(profile_response.status_code, status.HTTP_200_OK)
        
        # 3. Refresh the token
        refresh_response = self.client.post('/auth/token/refresh/', {
            'refresh': refresh_token
        })
        
        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)
        self.assertIn('access', refresh_response.data)
        self.assertIn('refresh', refresh_response.data)
        self.assertIn('user', refresh_response.data)
        self.assertIn('expires_in', refresh_response.data)
        
        # 4. Use new access token
        new_access_token = refresh_response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {new_access_token}')
        new_profile_response = self.client.get('/auth/token/status/')
        self.assertEqual(new_profile_response.status_code, status.HTTP_200_OK)
        
        # 5. Verify old refresh token is blacklisted
        old_refresh_response = self.client.post('/auth/token/refresh/', {
            'refresh': refresh_token
        })
        self.assertEqual(old_refresh_response.status_code, status.HTTP_400_BAD_REQUEST) 