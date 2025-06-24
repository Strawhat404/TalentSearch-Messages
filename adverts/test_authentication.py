from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from .models import Advert
from django.utils import timezone
from datetime import timedelta
import uuid

User = get_user_model()


class AdvertAuthenticationTest(TestCase):
    """
    Test cases to verify authentication and authorization for adverts
    """
    
    def setUp(self):
        self.client = APIClient()
        
        # Create test users
        self.user1 = User.objects.create_user(
            email='user1@example.com',
            password='testpass123',
            name='User One'
        )
        self.user2 = User.objects.create_user(
            email='user2@example.com',
            password='testpass123',
            name='User Two'
        )
        
        # Create test adverts
        now = timezone.now()
        
        # Published advert currently running (visible to public)
        self.published_advert = Advert.objects.create(
            title='Published Advert',
            description='This is a published advert',
            status='published',
            run_from=now - timedelta(days=1),
            run_to=now + timedelta(days=30),
            created_by=self.user1
        )
        
        # Draft advert (only visible to authenticated users)
        self.draft_advert = Advert.objects.create(
            title='Draft Advert',
            description='This is a draft advert',
            status='draft',
            created_by=self.user1
        )
        
        # Published advert that has expired (not visible to public)
        self.expired_advert = Advert.objects.create(
            title='Expired Advert',
            description='This advert has expired',
            status='published',
            run_from=now - timedelta(days=30),
            run_to=now - timedelta(days=1),
            created_by=self.user1
        )
        
        # Published advert that hasn't started yet (not visible to public)
        self.future_advert = Advert.objects.create(
            title='Future Advert',
            description='This advert will start in the future',
            status='published',
            run_from=now + timedelta(days=1),
            run_to=now + timedelta(days=30),
            created_by=self.user1
        )
        
        # Advert created by user2
        self.user2_advert = Advert.objects.create(
            title='User2 Advert',
            description='This advert belongs to user2',
            status='published',
            run_from=now - timedelta(days=1),
            run_to=now + timedelta(days=30),
            created_by=self.user2
        )
        
        self.list_url = reverse('advert-list-create')
    
    def test_public_access_to_list(self):
        """Test that unauthenticated users can only see published adverts that are currently running"""
        response = self.client.get(self.list_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        advert_titles = [advert['title'] for advert in response.data]
        
        # Should see published advert that is currently running
        self.assertIn('Published Advert', advert_titles)
        self.assertIn('User2 Advert', advert_titles)
        
        # Should NOT see draft, expired, or future adverts
        self.assertNotIn('Draft Advert', advert_titles)
        self.assertNotIn('Expired Advert', advert_titles)
        self.assertNotIn('Future Advert', advert_titles)
    
    def test_authenticated_user_access_to_list(self):
        """Test that authenticated users can see all adverts"""
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.list_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        advert_titles = [advert['title'] for advert in response.data]
        
        # Should see all adverts
        self.assertIn('Published Advert', advert_titles)
        self.assertIn('Draft Advert', advert_titles)
        self.assertIn('Expired Advert', advert_titles)
        self.assertIn('Future Advert', advert_titles)
        self.assertIn('User2 Advert', advert_titles)
    
    def test_public_access_to_detail(self):
        """Test that unauthenticated users can only access published adverts that are currently running"""
        # Should be able to access published advert
        detail_url = reverse('advert-retrieve-update-destroy', args=[self.published_advert.id])
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should NOT be able to access draft advert
        detail_url = reverse('advert-retrieve-update-destroy', args=[self.draft_advert.id])
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Should NOT be able to access expired advert
        detail_url = reverse('advert-retrieve-update-destroy', args=[self.expired_advert.id])
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_authenticated_user_access_to_detail(self):
        """Test that authenticated users can access all adverts"""
        self.client.force_authenticate(user=self.user1)
        
        # Should be able to access all adverts
        for advert in [self.published_advert, self.draft_advert, self.expired_advert, self.future_advert]:
            detail_url = reverse('advert-retrieve-update-destroy', args=[advert.id])
            response = self.client.get(detail_url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_create_advert_requires_authentication(self):
        """Test that creating an advert requires authentication"""
        data = {
            'title': 'New Advert',
            'description': 'Test description',
            'status': 'draft'
        }
        
        # Unauthenticated user should be denied
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Authenticated user should be allowed
        self.client.force_authenticate(user=self.user1)
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_update_advert_requires_authentication_and_ownership(self):
        """Test that updating an advert requires authentication and ownership"""
        data = {'title': 'Updated Title'}
        
        # Unauthenticated user should be denied
        detail_url = reverse('advert-retrieve-update-destroy', args=[self.published_advert.id])
        response = self.client.patch(detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # User2 should be denied (not the owner)
        self.client.force_authenticate(user=self.user2)
        response = self.client.patch(detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Owner should be allowed
        self.client.force_authenticate(user=self.user1)
        response = self.client.patch(detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_delete_advert_requires_authentication_and_ownership(self):
        """Test that deleting an advert requires authentication and ownership"""
        # Unauthenticated user should be denied
        detail_url = reverse('advert-retrieve-update-destroy', args=[self.published_advert.id])
        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # User2 should be denied (not the owner)
        self.client.force_authenticate(user=self.user2)
        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Owner should be allowed
        self.client.force_authenticate(user=self.user1)
        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_custom_manager_methods(self):
        """Test the custom manager methods work correctly"""
        # Test for_public method
        public_adverts = Advert.objects.for_public()
        self.assertEqual(public_adverts.count(), 2)  # published_advert and user2_advert
        self.assertIn(self.published_advert, public_adverts)
        self.assertIn(self.user2_advert, public_adverts)
        
        # Test for_authenticated_user method
        auth_adverts = Advert.objects.for_authenticated_user(self.user1)
        self.assertEqual(auth_adverts.count(), 5)  # all adverts
        
        # Test for_user method with authenticated user
        user_adverts = Advert.objects.for_user(self.user1)
        self.assertEqual(user_adverts.count(), 5)  # all adverts
        
        # Test for_user method with unauthenticated user
        public_user_adverts = Advert.objects.for_user(None)
        self.assertEqual(public_user_adverts.count(), 2)  # only published and running
        self.assertIn(self.published_advert, public_user_adverts)
        self.assertIn(self.user2_advert, public_user_adverts)
    
    def test_invalid_uuid_returns_404(self):
        """Test that invalid UUID returns 404"""
        invalid_uuid = uuid.uuid4()
        detail_url = reverse('advert-retrieve-update-destroy', args=[invalid_uuid])
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND) 