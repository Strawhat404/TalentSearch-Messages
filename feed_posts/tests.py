from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import FeedPost
import uuid
import os
from django.core.files.uploadedfile import SimpleUploadedFile

User = get_user_model()

class FeedPostModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        # Create a test image with actual content
        self.test_image = SimpleUploadedFile(
            name='test_image.jpg',
            content=b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b',
            content_type='image/jpeg'
        )

    def test_create_feed_post(self):
        post = FeedPost.objects.create(
            user=self.user,
            content='Test content',
            media_type='image',
            media_url=self.test_image,
            project_title='Test Project',
            project_type='Film',
            location='Test Location'
        )
        self.assertEqual(post.content, 'Test content')
        self.assertEqual(post.project_title, 'Test Project')
        self.assertEqual(post.project_type, 'Film')
        self.assertEqual(post.location, 'Test Location')

    def tearDown(self):
        # Clean up any created files
        for post in FeedPost.objects.all():
            if post.media_url:
                if os.path.isfile(post.media_url.path):
                    os.remove(post.media_url.path)

class FeedPostAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        # Create a test image with actual content
        self.test_image = SimpleUploadedFile(
            name='test_image.jpg',
            content=b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b',
            content_type='image/jpeg'
        )
        self.post = FeedPost.objects.create(
            user=self.user,
            content='Test content',
            media_type='image',
            media_url=self.test_image,
            project_title='Test Project',
            project_type='Film',
            location='Test Location'
        )

    def test_list_posts(self):
        url = reverse('feed_posts:feed-post-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_create_post(self):
        url = reverse('feed_posts:feed-post-list')
        # Create a new test image for this specific test
        test_image = SimpleUploadedFile(
            name='test_image.jpg',
            content=b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b',
            content_type='image/jpeg'
        )
        data = {
            'content': 'New test content',
            'media_type': 'image',
            'media_url': test_image,
            'project_title': 'New Test Project',
            'project_type': 'Film',
            'location': 'New Test Location'
        }
        response = self.client.post(url, data, format='multipart')
        if response.status_code != status.HTTP_201_CREATED:
            print("Create Post Response:", response.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(FeedPost.objects.count(), 2)

    def test_create_post_without_media(self):
        url = reverse('feed_posts:feed-post-list')
        data = {
            'content': 'New test content',
            'media_type': 'image',
            'project_title': 'New Test Project',
            'project_type': 'Film',
            'location': 'New Test Location'
        }
        response = self.client.post(url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('media_url', response.data)

    def test_create_post_with_invalid_media_type(self):
        url = reverse('feed_posts:feed-post-list')
        test_image = SimpleUploadedFile(
            name='test_image.jpg',
            content=b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b',
            content_type='image/jpeg'
        )
        data = {
            'content': 'New test content',
            'media_type': 'invalid_type',
            'media_url': test_image,
            'project_title': 'New Test Project',
            'project_type': 'Film',
            'location': 'New Test Location'
        }
        response = self.client.post(url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('media_type', response.data)

    def test_get_post_detail(self):
        url = reverse('feed_posts:feed-post-detail', kwargs={'id': self.post.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['project_title'], 'Test Project')

    def test_delete_post(self):
        url = reverse('feed_posts:feed-post-detail', kwargs={'id': self.post.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(FeedPost.objects.count(), 0)

    def test_filter_by_user_id(self):
        url = reverse('feed_posts:feed-post-list')
        response = self.client.get(f"{url}?user_id={self.user.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_filter_by_project_type(self):
        url = reverse('feed_posts:feed-post-list')
        response = self.client.get(f"{url}?project_type=Film")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def tearDown(self):
        # Clean up any created files
        for post in FeedPost.objects.all():
            if post.media_url:
                if os.path.isfile(post.media_url.path):
                    os.remove(post.media_url.path)