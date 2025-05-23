from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import CommentReaction
from feed_comments.models import Comment
from feed_posts.models import FeedPost
import uuid

User = get_user_model()

class CommentReactionModelTest(TestCase):
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
        self.reaction = CommentReaction.objects.create(
            user=self.user,
            comment=self.comment,
            is_dislike=False
        )

    def test_reaction_creation(self):
        self.assertEqual(self.reaction.user, self.user)
        self.assertEqual(self.reaction.comment, self.comment)
        self.assertFalse(self.reaction.is_dislike)
        self.assertEqual(self.comment.likes_count, 1)
        self.assertEqual(self.comment.dislikes_count, 0)

    def test_reaction_update(self):
        self.reaction.is_dislike = True
        self.reaction.save()
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.likes_count, 0)
        self.assertEqual(self.comment.dislikes_count, 1)

    def test_reaction_deletion(self):
        self.reaction.delete()
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.likes_count, 0)
        self.assertEqual(self.comment.dislikes_count, 0)

class CommentReactionAPITest(APITestCase):
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

    def test_create_reaction(self):
        url = reverse('comment-reaction-list')
        data = {
            'comment': str(self.comment.id),
            'is_dislike': False
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(CommentReaction.objects.count(), 1)
        self.assertEqual(response.data['message'], 'Reaction added successfully')
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.likes_count, 1)
        self.assertEqual(self.comment.dislikes_count, 0)

    def test_create_duplicate_reaction(self):
        # Create initial reaction
        CommentReaction.objects.create(
            user=self.user,
            comment=self.comment,
            is_dislike=False
        )
        
        url = reverse('comment-reaction-list')
        data = {
            'comment': str(self.comment.id),
            'is_dislike': False
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_switch_reaction_type(self):
        # Create initial like
        reaction = CommentReaction.objects.create(
            user=self.user,
            comment=self.comment,
            is_dislike=False
        )
        
        url = reverse('comment-reaction-detail', args=[str(reaction.id)])
        data = {'is_dislike': True}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.likes_count, 0)
        self.assertEqual(self.comment.dislikes_count, 1)

    def test_list_reactions(self):
        # Create some reactions
        CommentReaction.objects.create(
            user=self.user,
            comment=self.comment,
            is_dislike=False
        )
        CommentReaction.objects.create(
            user=self.other_user,
            comment=self.comment,
            is_dislike=True
        )

        url = reverse('comment-reaction-list')
        response = self.client.get(url, {'comment_id': str(self.comment.id)})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_filter_reactions(self):
        # Create reactions
        CommentReaction.objects.create(
            user=self.user,
            comment=self.comment,
            is_dislike=False
        )
        CommentReaction.objects.create(
            user=self.other_user,
            comment=self.comment,
            is_dislike=True
        )

        # Test filtering by is_dislike
        url = reverse('comment-reaction-list')
        response = self.client.get(url, {'is_dislike': 'true'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertTrue(response.data[0]['is_dislike'])

        # Test filtering by user_id
        response = self.client.get(url, {'user_id': str(self.user.id)})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['user'], str(self.user.id))

    def test_delete_reaction(self):
        reaction = CommentReaction.objects.create(
            user=self.user,
            comment=self.comment,
            is_dislike=False
        )
        
        url = reverse('comment-reaction-detail', args=[str(reaction.id)])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(CommentReaction.objects.count(), 0)
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.likes_count, 0)
        self.assertEqual(self.comment.dislikes_count, 0)

    def test_toggle_reaction(self):
        url = reverse('comment-reaction-toggle')
        
        # Create initial like
        data = {
            'comment': str(self.comment.id),
            'is_dislike': False
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.likes_count, 1)
        self.assertEqual(self.comment.dislikes_count, 0)

        # Toggle to dislike
        data['is_dislike'] = True
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.likes_count, 0)
        self.assertEqual(self.comment.dislikes_count, 1)

        # Toggle back to like
        data['is_dislike'] = False
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.likes_count, 1)
        self.assertEqual(self.comment.dislikes_count, 0)

    def test_unauthorized_access(self):
        self.client.force_authenticate(user=None)
        url = reverse('comment-reaction-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_invalid_comment_id(self):
        url = reverse('comment-reaction-list')
        data = {
            'comment': str(uuid.uuid4()),  # Non-existent comment ID
            'is_dislike': False
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_other_user_cannot_modify_reaction(self):
        # Create a reaction for other user
        reaction = CommentReaction.objects.create(
            user=self.other_user,
            comment=self.comment,
            is_dislike=False
        )
        
        # Try to modify it as the first user
        url = reverse('comment-reaction-detail', args=[str(reaction.id)])
        data = {'is_dislike': True}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
