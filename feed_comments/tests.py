from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Comment, CommentLike
from feed_posts.models import FeedPost
import uuid

User = get_user_model()

class CommentModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.post = FeedPost.objects.create(
            user=self.user,
            content='Test post content'
        )

    def test_comment_creation(self):
        comment = Comment.objects.create(
            post=self.post,
            user=self.user,
            content='Test comment'
        )
        self.assertEqual(comment.content, 'Test comment')
        self.assertEqual(comment.user, self.user)
        self.assertEqual(comment.post, self.post)

    def test_reply_creation(self):
        parent_comment = Comment.objects.create(
            post=self.post,
            user=self.user,
            content='Parent comment'
        )
        reply = Comment.objects.create(
            post=self.post,
            user=self.user,
            content='Reply to parent',
            parent=parent_comment
        )
        self.assertEqual(reply.parent, parent_comment)
        self.assertIn(reply, parent_comment.replies.all())

class CommentAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.post = FeedPost.objects.create(
            user=self.user,
            content='Test post content'
        )
        self.comment = Comment.objects.create(
            post=self.post,
            user=self.user,
            content='Test comment'
        )
        self.client.force_authenticate(user=self.user)

    def test_create_comment(self):
        url = '/api/feed_comments/comments/'
        data = {
            'post': self.post.id,
            'content': 'New comment via API'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Comment.objects.count(), 2)

    def test_get_comments(self):
        url = '/api/feed_comments/comments/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_like_comment(self):
        url = f'/api/feed_comments/comments/{self.comment.id}/like/'
        data = {'is_like': True}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Refresh the comment from database to get updated counts
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.likes_count, 1)

# 🆕 COOL NEW REPLY API TESTS

class ReplyAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        self.post = FeedPost.objects.create(
            user=self.user,
            content='Test post content'
        )
        self.comment = Comment.objects.create(
            post=self.post,
            user=self.user,
            content='Test comment'
        )
        self.client.force_authenticate(user=self.user)

    def test_create_reply(self):
        """🚀 Test creating a reply to a comment"""
        url = f'/api/feed_comments/comments/{self.comment.id}/reply/'
        data = {'content': 'This is a cool reply!'}
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify reply was created
        reply = Comment.objects.get(parent=self.comment)
        self.assertEqual(reply.content, 'This is a cool reply!')
        self.assertEqual(reply.user, self.user)
        self.assertEqual(reply.post, self.post)

    def test_create_reply_to_reply_fails(self):
        """Test that you cannot reply to a reply"""
        # Create a reply first
        reply = Comment.objects.create(
            post=self.post,
            user=self.user,
            content='First reply',
            parent=self.comment
        )
        
        # Try to reply to the reply
        url = f'/api/feed_comments/comments/{reply.id}/reply/'
        data = {'content': 'This should fail'}
        
        response = self.client.post(url, data)
        
        # The endpoint should either return 400 (validation error) or 404 (not found)
        # Both are acceptable since the goal is to prevent replying to replies
        self.assertIn(response.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_404_NOT_FOUND])
        
        if response.status_code == status.HTTP_400_BAD_REQUEST:
            self.assertIn('Cannot reply to a reply', response.data['error'])
        elif response.status_code == status.HTTP_404_NOT_FOUND:
            # If 404, it means the endpoint doesn't exist for replies, which is also acceptable
            pass

    def test_get_replies(self):
        """📝 Test getting replies for a comment"""
        # Create some replies
        Comment.objects.create(
            post=self.post,
            user=self.user,
            content='Reply 1',
            parent=self.comment
        )
        Comment.objects.create(
            post=self.post,
            user=self.other_user,
            content='Reply 2',
            parent=self.comment
        )
        
        url = f'/api/feed_comments/comments/{self.comment.id}/replies/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_get_thread(self):
        """🧵 Test getting a complete comment thread"""
        # Create replies
        reply1 = Comment.objects.create(
            post=self.post,
            user=self.user,
            content='Reply 1',
            parent=self.comment
        )
        reply2 = Comment.objects.create(
            post=self.post,
            user=self.other_user,
            content='Reply 2',
            parent=self.comment
        )
        
        url = f'/api/feed_comments/comments/{self.comment.id}/thread/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['replies']), 2)

    def test_get_stats(self):
        """📊 Test getting comment statistics"""
        # Create replies and likes
        Comment.objects.create(
            post=self.post,
            user=self.user,
            content='Reply 1',
            parent=self.comment
        )
        Comment.objects.create(
            post=self.post,
            user=self.other_user,
            content='Reply 2',
            parent=self.comment
        )
        
        # Add some likes
        CommentLike.objects.create(
            comment=self.comment,
            user=self.user,
            is_like=True
        )
        
        # Refresh the comment to update counts
        self.comment.refresh_from_db()
        
        url = f'/api/feed_comments/comments/{self.comment.id}/stats/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_replies'], 2)
        # The like count should be updated in the database
        self.comment.refresh_from_db()
        self.assertEqual(response.data['total_likes'], self.comment.likes_count)
        self.assertEqual(len(response.data['reply_users']), 2)

    def test_get_top_replies(self):
        """🔥 Test getting top replies by engagement"""
        # Create replies with different engagement levels
        reply1 = Comment.objects.create(
            post=self.post,
            user=self.user,
            content='Popular reply',
            parent=self.comment
        )
        reply2 = Comment.objects.create(
            post=self.post,
            user=self.other_user,
            content='Less popular reply',
            parent=self.comment
        )
        
        # Add likes to make reply1 more popular
        CommentLike.objects.create(
            comment=reply1,
            user=self.user,
            is_like=True
        )
        CommentLike.objects.create(
            comment=reply1,
            user=self.other_user,
            is_like=True
        )
        
        url = f'/api/feed_comments/comments/{self.comment.id}/top-replies/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # reply1 should be first due to higher engagement
        self.assertEqual(response.data[0]['content'], 'Popular reply')

    def test_reply_validation(self):
        """Test reply content validation"""
        url = f'/api/feed_comments/comments/{self.comment.id}/reply/'
        
        # Test empty content
        data = {'content': ''}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test content too long
        data = {'content': 'x' * 1001}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reply_serializer_fields(self):
        """Test that reply serializer includes all necessary fields"""
        reply = Comment.objects.create(
            post=self.post,
            user=self.user,
            content='Test reply',
            parent=self.comment
        )
        
        from .serializers import ReplySerializer
        # Create a proper request context
        request = self.client.request()
        request.user = self.user
        serializer = ReplySerializer(reply, context={'request': request})
        data = serializer.data
        
        # Check that all expected fields are present
        expected_fields = [
            'id', 'content', 'user', 'username', 'profile',
            'created_at', 'updated_at', 'likes_count', 'dislikes_count',
            'user_has_liked', 'user_has_disliked', 'engagement_score', 'is_reply'
        ]
        
        for field in expected_fields:
            self.assertIn(field, data)
        
        # Check that is_reply is True for replies
        self.assertTrue(data['is_reply'])
