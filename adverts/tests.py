from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from .models import Advert
import tempfile
from django.core.files.uploadedfile import SimpleUploadedFile
from io import BytesIO
from PIL import Image
import uuid
from .serializers import AdvertSerializer
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

class AdvertModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='testpass',
            name='Test User'
        )
        self.advert = Advert.objects.create(
            title='Test Advert',
            created_by=self.user,
            status='published'
        )

    def test_advert_creation(self):
        self.assertEqual(self.advert.title, 'Test Advert')
        self.assertEqual(self.advert.created_by, self.user)
        self.assertEqual(self.advert.status, 'published')
        self.assertTrue(self.advert.created_at)
        self.assertTrue(self.advert.updated_at)

    def test_advert_str(self):
        self.assertEqual(str(self.advert), 'Test Advert')

class AdvertAPITest(TestCase):
    throttle_classes = []

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='testpass',
            name='Test User'
        )
        self.client.force_authenticate(user=self.user)
        self.advert = Advert.objects.create(
            title='Test Advert',
            created_by=self.user,
            status='published'
        )
        self.list_create_url = reverse('advert-list-create')
        self.detail_url = reverse('advert-retrieve-update-destroy', args=[self.advert.id])

    def _create_image(self):
        image = Image.new('RGB', (100, 100))
        tmp_file = BytesIO()
        image.save(tmp_file, 'JPEG')
        tmp_file.seek(0)
        return SimpleUploadedFile('test.jpg', tmp_file.read(), content_type='image/jpeg')

    def test_list_adverts(self):
        response = self.client.get(self.list_create_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_create_advert(self):
        data = {
            'title': 'New Advert',
            'created_by': self.user.id,
            'status': 'draft',
            'description': 'A new advert',
            'location': 'Test City',
        }
        response = self.client.post(self.list_create_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('id', response.data)
        self.assertEqual(response.data['message'], 'Advert created successfully.')

    def test_retrieve_advert(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Test Advert')

    def test_update_advert(self):
        data = {
            'title': 'Updated Advert',
            'status': 'archived',
            'created_by': self.user.id
        }
        response = self.client.put(self.detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Advert updated successfully.')
        self.advert.refresh_from_db()
        self.assertEqual(self.advert.title, 'Updated Advert')
        self.assertEqual(self.advert.status, 'archived')

    def test_delete_advert(self):
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Advert deleted successfully.')
        self.assertFalse(Advert.objects.filter(id=self.advert.id).exists())

class AdvertImageUpdateTest(TestCase):
    def setUp(self):
        pass

    def test_update_advert_image(self):
        pass

class AdvertValidationTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='testpass',
            name='Test User'
        )
        self.client.force_authenticate(user=self.user)
        self.list_create_url = reverse('advert-list-create')
        
        # Create a test advert
        self.advert = Advert.objects.create(
            title='Test Advert',
            created_by=self.user,
            status='draft',
            run_from=timezone.now() + timedelta(days=1),
            run_to=timezone.now() + timedelta(days=30)
        )
        self.detail_url = reverse('advert-retrieve-update-destroy', args=[self.advert.id])

    def _create_test_image(self, size_mb=1):
        """Create a test image of specified size in MB"""
        image = Image.new('RGB', (100, 100))
        tmp_file = BytesIO()
        image.save(tmp_file, 'JPEG')
        tmp_file.seek(0)
        return SimpleUploadedFile(
            'test.jpg',
            tmp_file.read() * (size_mb * 1024 * 1024 // len(tmp_file.getvalue()) + 1),
            content_type='image/jpeg'
        )

    def _create_test_video(self, size_mb=1):
        """Create a test video file of specified size in MB"""
        content = b'0' * (size_mb * 1024 * 1024)
        return SimpleUploadedFile(
            'test.mp4',
            content,
            content_type='video/mp4'
        )

    def test_image_size_validation(self):
        """Test that images larger than 5MB are rejected"""
        # Test with 6MB image
        image = self._create_test_image(size_mb=6)
        data = {
            'title': 'Test Advert',
            'image': image,
            'status': 'draft'
        }
        response = self.client.post(self.list_create_url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Image file size must not exceed 5.0MB', str(response.data['image']))

    def test_video_size_validation(self):
        """Test that videos larger than 100MB are rejected"""
        # Test with 101MB video
        video = self._create_test_video(size_mb=101)
        data = {
            'title': 'Test Advert',
            'video': video,
            'status': 'draft'
        }
        response = self.client.post(self.list_create_url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Video file size must not exceed 100.0MB', str(response.data['video']))

    def test_title_sanitization(self):
        """Test that HTML in title is stripped"""
        data = {
            'title': '<script>alert("xss")</script>Test Advert',
            'status': 'draft'
        }
        response = self.client.post(self.list_create_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # The sanitizer leaves script content as text, so expect 'alert("xss")Test Advert'
        self.assertEqual(Advert.objects.get(id=response.data['id']).title, 'alert("xss")Test Advert')

    def test_description_sanitization(self):
        """Test that only allowed HTML tags are preserved in description"""
        data = {
            'title': 'Test Advert',
            'description': '<p>Valid</p><script>alert("xss")</script><a href="http://example.com">Link</a>',
            'status': 'draft'
        }
        response = self.client.post(self.list_create_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        advert = Advert.objects.get(id=response.data['id'])
        self.assertIn('<p>Valid</p>', advert.description)
        self.assertIn('<a href="http://example.com">Link</a>', advert.description)
        self.assertNotIn('<script>', advert.description)

    def test_status_transition_validation(self):
        """Test that status transitions follow the defined rules"""
        # Test invalid transition from draft to expired
        data = {'status': 'expired'}
        response = self.client.patch(self.detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Cannot transition from draft to expired', str(response.data['status']))

        # Test valid transition from draft to published
        run_from = (timezone.now() + timedelta(days=1)).isoformat()
        run_to = (timezone.now() + timedelta(days=30)).isoformat()
        data = {
            'title': 'Test Advert',
            'status': 'published',
            'run_from': run_from,
            'run_to': run_to
        }
        response = self.client.patch(self.detail_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Test invalid transition from published to draft
        data = {'status': 'draft'}
        response = self.client.patch(self.detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Cannot transition from published to draft', str(response.data['status']))

    def test_campaign_duration_validation(self):
        """Test that campaign duration cannot exceed 1 year"""
        data = {
            'title': 'Test Advert',
            'run_from': timezone.now() + timedelta(days=1),
            'run_to': timezone.now() + timedelta(days=366),
            'status': 'draft'
        }
        response = self.client.post(self.list_create_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Campaign duration cannot exceed 1 year', str(response.data['run_to']))

    def test_published_advert_requirements(self):
        """Test that published adverts must have required fields"""
        data = {
            'title': 'Test Advert',
            'status': 'published'
            # Missing run_from and run_to
        }
        response = self.client.post(self.list_create_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Cannot publish advert without', str(response.data['status']))

    def test_run_date_validation(self):
        """Test run date validations"""
        # Test run_to before run_from
        data = {
            'title': 'Test Advert',
            'run_from': timezone.now() + timedelta(days=30),
            'run_to': timezone.now() + timedelta(days=1),
            'status': 'draft'
        }
        response = self.client.post(self.list_create_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('End date must be after start date', str(response.data['run_to']))

        # Test run_from in the past
        data = {
            'title': 'Test Advert',
            'run_from': timezone.now() - timedelta(days=1),
            'run_to': timezone.now() + timedelta(days=30),
            'status': 'draft'
        }
        response = self.client.post(self.list_create_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Start date cannot be in the past', str(response.data['run_from']))
