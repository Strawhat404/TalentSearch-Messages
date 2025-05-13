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
        # Setup code here
        pass

    def test_update_advert_image(self):
        # Test code here
        pass
