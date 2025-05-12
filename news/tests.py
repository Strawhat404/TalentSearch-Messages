from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from .models import News, NewsImage
from .serializers import NewsSerializer
from taggit.models import Tag
import tempfile
from PIL import Image
from django.core.files import File
import io
from rest_framework.authtoken.models import Token

User = get_user_model()

class NewsModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='testpass',
            name='Test User'
        )
        self.image = NewsImage.objects.create(
            image=self._create_image(),
            caption='Test Image'
        )
        self.news = News.objects.create(
            title='Test News',
            content='Test content',
            created_by=self.user,
            status='published'
        )
        self.news.image_gallery.add(self.image)
        self.news.tags.add('test', 'news')

    def _create_image(self):
        """Helper to create a temporary image file."""
        image = Image.new('RGB', (100, 100))
        tmp_file = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
        image.save(tmp_file, 'JPEG')
        tmp_file.seek(0)
        return File(tmp_file, name='test_image.jpg')

    def test_news_creation(self):
        """Test News model creation and field validation."""
        self.assertEqual(self.news.title, 'Test News')
        self.assertEqual(self.news.content, 'Test content')
        self.assertEqual(self.news.created_by, self.user)
        self.assertEqual(self.news.status, 'published')
        self.assertEqual(self.news.image_gallery.count(), 1)
        self.assertEqual(self.news.tags.count(), 2)
        self.assertTrue(self.news.created_at)
        self.assertTrue(self.news.updated_at)

    def test_news_str(self):
        """Test News __str__ method."""
        self.assertEqual(str(self.news), 'Test News')

    def test_news_image_creation(self):
        """Test NewsImage model creation."""
        self.assertEqual(self.image.caption, 'Test Image')
        self.assertTrue(self.image.image)

    def test_news_image_str(self):
        """Test NewsImage __str__ method."""
        self.assertEqual(str(self.image), 'Test Image')

class NewsSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='testpass',
            name='Test User'
        )
        self.image = NewsImage.objects.create(
            image=self._create_image(),
            caption='Test Image'
        )
        self.news = News.objects.create(
            title='Test News',
            content='Test content',
            created_by=self.user,
            status='published'
        )
        self.news.image_gallery.add(self.image)
        self.news.tags.add('test')
        self.serializer = NewsSerializer(instance=self.news)

    def _create_image(self):
        """Helper to create a temporary image file."""
        image = Image.new('RGB', (100, 100))
        tmp_file = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
        image.save(tmp_file, 'JPEG')
        tmp_file.seek(0)
        return File(tmp_file, name='test_image.jpg')

    def test_serializer_valid(self):
        """Test NewsSerializer with valid data."""
        data = self.serializer.data
        self.assertEqual(data['title'], 'Test News')
        self.assertEqual(data['content'], 'Test content')
        self.assertEqual(data['status'], 'published')
        self.assertEqual(len(data['image_gallery']), 1)
        self.assertEqual(len(data['tags']), 1)  # Tags serialized as list of strings

    def test_serializer_validation(self):
        """Test NewsSerializer validation for invalid data."""
        data = {
            'title': '',  # Invalid: empty
            'content': 'Test content',
            'status': 'invalid',  # Invalid: not in STATUS_CHOICES
            'created_by': self.user.id
        }
        serializer = NewsSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('title', serializer.errors)
        self.assertIn('status', serializer.errors)

class NewsRouteTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='testpass',
            name='Test User'
        )
        self.admin = User.objects.create_superuser(
            email='admin@example.com',
            password='adminpass',
            name='Admin User'
        )
        self.image = NewsImage.objects.create(
            image=self._create_image(),
            caption='Test Image'
        )
        self.news = News.objects.create(
            title='Test News',
            content='Test content',
            created_by=self.user,
            status='published'
        )
        self.news.image_gallery.add(self.image)
        self.news.tags.add('test')

    def _create_image(self):
        """Helper to create a temporary image file."""
        image = Image.new('RGB', (100, 100))
        tmp_file = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
        image.save(tmp_file, 'JPEG')
        tmp_file.seek(0)
        return File(tmp_file, name='test_image.jpg')

    def _get_token(self, email, password):
        """Helper to get Token authentication."""
        user = User.objects.get(email=email)
        token, created = Token.objects.get_or_create(user=user)
        return token.key

    def test_get_news_list_unauthenticated(self):
        """Test GET /api/news/ without authentication."""
        response = self.client.get('/api/news/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_news_list_authenticated_non_admin(self):
        """Test GET /api/news/ with non-admin authentication."""
        token = self._get_token('testuser@example.com', 'testpass')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        response = self.client.get('/api/news/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_news_list_authenticated_admin(self):
        """Test GET /api/news/ with admin authentication."""
        token = self._get_token('admin@example.com', 'adminpass')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        response = self.client.get('/api/news/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'Test News')

    def test_post_news_admin(self):
        """Test POST /api/news/ with admin authentication."""
        token = self._get_token('admin@example.com', 'adminpass')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        data = {
            'title': 'New News',
            'content': 'New content',
            'status': 'published',
            'image_gallery': [self.image.id],
            'tags': ['new', 'update']
        }
        response = self.client.post('/api/news/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['message'], 'News created successfully.')

    def test_post_news_non_admin(self):
        """Test POST /api/news/ with non-admin authentication."""
        token = self._get_token('testuser@example.com', 'testpass')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        data = {
            'title': 'New News',
            'content': 'New content',
            'status': 'published'
        }
        response = self.client.post('/api/news/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_put_news_admin(self):
        """Test PUT /api/news/<id>/ with admin authentication."""
        token = self._get_token('admin@example.com', 'adminpass')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        data = {
            'title': 'Updated News',
            'content': 'Updated content',
            'status': 'published'
        }
        response = self.client.put(f'/api/news/{self.news.id}/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'News updated successfully.')

    def test_delete_news_admin(self):
        """Test DELETE /api/news/<id>/ with admin authentication."""
        token = self._get_token('admin@example.com', 'adminpass')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        response = self.client.delete(f'/api/news/{self.news.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'News deleted successfully.')