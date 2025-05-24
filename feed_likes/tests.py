from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from feed_posts.models import FeedPost
from .models import FeedLike
import uuid

User = get_user_model()

class FeedLikeModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.post = FeedPost.objects.create(
            user=self.user,
            content='Test content',
            media_type='image',
            project_title='Test Project',
            project_type='Film',
            location='Test Location'
        )

    def test_create_like(self):
        like = FeedLike.objects.create(
            user=self.user,
            post=self.post
        )
        self.assertEqual(like.user, self.user)
        self.assertEqual(like.post, self.post)

    def test_unique_like_constraint(self):
        # Create first like
        FeedLike.objects.create(
            user=self.user,
            post=self.post
        )
        # Try to create duplicate like
        with self.assertRaises(Exception):
            FeedLike.objects.create(
                user=self.user,
                post=self.post
            )

class FeedLikeAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            email='other@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        self.post = FeedPost.objects.create(
            user=self.user,
            content='Test content',
            media_type='image',
            project_title='Test Project',
            project_type='Film',
            location='Test Location'
        )
        # Create initial like for the post
        self.like = FeedLike.objects.create(
            user=self.user,
            post=self.post
        )

    def test_list_likes(self):
        """Test listing all likes"""
        url = reverse('feed_likes:feed-like-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_list_likes_with_post_filter(self):
        """Test listing likes filtered by post_id"""
        url = reverse('feed_likes:feed-like-list')
        response = self.client.get(f"{url}?post_id={self.post.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['user_id'], str(self.user.id))

    def test_list_likes_with_user_filter(self):
        """Test listing likes filtered by user_id"""
        url = reverse('feed_likes:feed-like-list')
        response = self.client.get(f"{url}?user_id={self.user.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['user_id'], str(self.user.id))
        self.assertEqual(response.data[0]['post_id'], str(self.post.id))

    def test_list_likes_with_multiple_filters(self):
        """Test listing likes with both post_id and user_id filters"""
        url = reverse('feed_likes:feed-like-list')
        response = self.client.get(f"{url}?post_id={self.post.id}&user_id={self.user.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['user_id'], str(self.user.id))
        self.assertEqual(response.data[0]['post_id'], str(self.post.id))

    def test_list_likes_with_invalid_filters(self):
        """Test listing likes with invalid UUID filters"""
        url = reverse('feed_likes:feed-like-list')
        response = self.client.get(f"{url}?post_id=invalid-uuid&user_id=invalid-uuid")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_create_like_invalid_post_id(self):
        """Test creating a like with invalid post_id"""
        url = reverse('feed_likes:feed-like-list')
        data = {
            'post': 'invalid-uuid'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('post', response.data)

    def test_delete_like(self):
        # Use the like created in setUp instead of creating a new one
        url = reverse('feed_likes:feed-like-delete')
        data = {
            'post_id': str(self.post.id)
        }
        response = self.client.delete(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(FeedLike.objects.count(), 0)  # All likes should be deleted

    def test_like_other_users_post(self):
        # Create a post by another user
        other_post = FeedPost.objects.create(
            user=self.other_user,
            content='Other content',
            media_type='image',
            project_title='Other Project',
            project_type='Film',
            location='Other Location'
        )
        
        # Create a like for the other user's post
        url = reverse('feed_likes:feed-like-list')
        data = {
            'post': str(other_post.id)
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(FeedLike.objects.count(), 2)  # Original like + new like
