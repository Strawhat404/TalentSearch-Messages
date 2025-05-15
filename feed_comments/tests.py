from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import Comment, CommentLike
from feed_posts.models import FeedPost
import uuid

User = get_user_model()

class CommentModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.post = FeedPost.objects.create(
            user=self.user,
            content='Test post content'
        )
        self.comment = Comment.objects.create(
            user=self.user,
            post=self.post,
            content='Test comment content'
        )

    def test_comment_creation(self):
        self.assertEqual(self.comment.user, self.user)
        self.assertEqual(self.comment.post, self.post)
        self.assertEqual(self.comment.content, 'Test comment content')
        self.assertIsNone(self.comment.parent)
        self.assertEqual(self.comment.likes_count, 0)
        self.assertEqual(self.comment.dislikes_count, 0)

    def test_comment_reply(self):
        reply = Comment.objects.create(
            user=self.user,
            post=self.post,
            content='Test reply content',
            parent=self.comment
        )
        self.assertEqual(reply.parent, self.comment)
        self.assertEqual(self.comment.replies.count(), 1)

class CommentAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            email='other@example.com',
            password='testpass123'
        )
        self.post = FeedPost.objects.create(
            user=self.user,
            content='Test post content'
        )
        self.comment = Comment.objects.create(
            user=self.user,
            post=self.post,
            content='Test comment content'
        )
        self.client.force_authenticate(user=self.user)

    def test_create_comment(self):
        url = reverse('comment-list')
        data = {
            'post': str(self.post.id),
            'content': 'New test comment'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Comment.objects.count(), 2)
        self.assertEqual(response.data['content'], 'New test comment')

    def test_create_reply(self):
        url = reverse('comment-list')
        data = {
            'post': str(self.post.id),
            'content': 'Test reply',
            'parent': str(self.comment.id)
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.comment.replies.count(), 1)

    def test_list_comments(self):
        # Create a few more comments
        Comment.objects.create(
            user=self.user,
            post=self.post,
            content='Another comment'
        )
        Comment.objects.create(
            user=self.other_user,
            post=self.post,
            content='Other user comment'
        )

        url = reverse('comment-list')
        response = self.client.get(url, {'post_id': str(self.post.id)})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)  # Including the one from setUp

    def test_comment_like(self):
        url = reverse('comment-like', args=[str(self.comment.id)])
        data = {'is_like': True}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.likes_count, 1)
        self.assertEqual(self.comment.dislikes_count, 0)

        # Test unlike
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.likes_count, 0)

    def test_comment_dislike(self):
        url = reverse('comment-like', args=[str(self.comment.id)])
        data = {'is_like': False}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.likes_count, 0)
        self.assertEqual(self.comment.dislikes_count, 1)

    def test_switch_like_to_dislike(self):
        # First like
        url = reverse('comment-like', args=[str(self.comment.id)])
        response = self.client.post(url, {'is_like': True}, format='json')
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.likes_count, 1)
        self.assertEqual(self.comment.dislikes_count, 0)

        # Then switch to dislike
        response = self.client.post(url, {'is_like': False}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.likes_count, 0)
        self.assertEqual(self.comment.dislikes_count, 1)

    def test_unauthorized_access(self):
        self.client.force_authenticate(user=None)
        url = reverse('comment-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_invalid_reply_to_reply(self):
        # Create a reply
        reply = Comment.objects.create(
            user=self.user,
            post=self.post,
            content='First reply',
            parent=self.comment
        )

        # Try to reply to the reply
        url = reverse('comment-list')
        data = {
            'post': str(self.post.id),
            'content': 'Invalid reply to reply',
            'parent': str(reply.id)
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_comment_update(self):
        url = reverse('comment-detail', args=[str(self.comment.id)])
        data = {'content': 'Updated comment content'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.content, 'Updated comment content')

    def test_comment_delete(self):
        url = reverse('comment-detail', args=[str(self.comment.id)])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Comment.objects.count(), 0)

    def test_other_user_cannot_update_comment(self):
        self.client.force_authenticate(user=self.other_user)
        url = reverse('comment-detail', args=[str(self.comment.id)])
        data = {'content': 'Unauthorized update attempt'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_comment_with_invalid_post(self):
        url = reverse('comment-list')
        data = {
            'post': str(uuid.uuid4()),  # Non-existent post ID
            'content': 'Test comment'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_comment_with_invalid_parent(self):
        url = reverse('comment-list')
        data = {
            'post': str(self.post.id),
            'content': 'Test comment',
            'parent': str(uuid.uuid4())  # Non-existent parent ID
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
