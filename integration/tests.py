from django.test import TestCase, TransactionTestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from jobs.models import Job, JobApplication
from news.models import News, NewsComment
from messaging.models import Message, MessageNotification
from userprofile.models import UserProfile
from django.utils import timezone
from django.core.cache import cache
import threading
from django.db import transaction

User = get_user_model()

class JobApplicationMessagingTest(TransactionTestCase):
    def setUp(self):
        self.client = APIClient()
        # Create employer
        self.employer = User.objects.create_user(
            email='employer@example.com',
            password='testpass123',
            name='Test Employer'
        )
        self.employer_profile = UserProfile.objects.create(
            user=self.employer,
            name='Test Employer',
            bio='Company Bio'
        )
        # Create candidate
        self.candidate = User.objects.create_user(
            email='candidate@example.com',
            password='testpass123',
            name='Test Candidate'
        )
        self.candidate_profile = UserProfile.objects.create(
            user=self.candidate,
            name='Test Candidate',
            bio='Candidate Bio'
        )
        # Create job
        self.job = Job.objects.create(
            title='Software Engineer',
            description='Job description',
            employer=self.employer,
            status='active'
        )
        # URLs
        self.job_url = reverse('job-detail', args=[self.job.id])
        self.application_url = reverse('job-application-list')
        self.message_url = reverse('message-list')
        cache.clear()

    def test_job_application_messaging_flow(self):
        """Test complete flow from job application to messaging"""
        # Candidate applies for job
        self.client.force_authenticate(user=self.candidate)
        response = self.client.post(self.application_url, {
            'job': self.job.id,
            'cover_letter': 'I am interested in this position'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        application_id = response.data['id']

        # Verify application created
        application = JobApplication.objects.get(id=application_id)
        self.assertEqual(application.applicant, self.candidate)
        self.assertEqual(application.job, self.job)
        self.assertEqual(application.status, 'pending')

        # Employer reviews application
        self.client.force_authenticate(user=self.employer)
        response = self.client.patch(
            reverse('job-application-detail', args=[application_id]),
            {'status': 'reviewing'}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Employer sends message to candidate
        response = self.client.post(self.message_url, {
            'receiver_id': self.candidate.id,
            'content': 'Thank you for your application. Would you be available for an interview?'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Verify message notification
        notification = MessageNotification.objects.filter(
            recipient=self.candidate,
            message__sender=self.employer
        ).first()
        self.assertIsNotNone(notification)
        self.assertFalse(notification.read)

        # Candidate responds
        self.client.force_authenticate(user=self.candidate)
        response = self.client.post(self.message_url, {
            'receiver_id': self.employer.id,
            'content': 'Yes, I would be interested in an interview.'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Verify application status update
        application.refresh_from_db()
        self.assertEqual(application.status, 'reviewing')
        self.assertIsNotNone(application.last_message_at)

    def test_concurrent_application_messaging(self):
        """Test concurrent job applications and messaging"""
        # Create multiple candidates
        candidates = []
        for i in range(3):
            user = User.objects.create_user(
                email=f'candidate{i}@example.com',
                password='testpass123',
                name=f'Candidate {i}'
            )
            UserProfile.objects.create(user=user, name=f'Candidate {i}')
            candidates.append(user)

        def apply_and_message(candidate):
            with transaction.atomic():
                # Apply for job
                self.client.force_authenticate(user=candidate)
                response = self.client.post(self.application_url, {
                    'job': self.job.id,
                    'cover_letter': f'Application from {candidate.name}'
                })
                self.assertEqual(response.status_code, status.HTTP_201_CREATED)

                # Send message to employer
                response = self.client.post(self.message_url, {
                    'receiver_id': self.employer.id,
                    'content': f'Hello, I am {candidate.name}'
                })
                self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Simulate concurrent applications
        threads = []
        for candidate in candidates:
            thread = threading.Thread(target=apply_and_message, args=(candidate,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Verify all applications and messages were created
        self.assertEqual(JobApplication.objects.count(), 3)
        self.assertEqual(Message.objects.filter(sender__in=candidates).count(), 3)
        self.assertEqual(MessageNotification.objects.filter(recipient=self.employer).count(), 3)

class NewsCommentIntegrationTest(TransactionTestCase):
    def setUp(self):
        self.client = APIClient()
        # Create news author
        self.author = User.objects.create_user(
            email='author@example.com',
            password='testpass123',
            name='News Author'
        )
        self.author_profile = UserProfile.objects.create(
            user=self.author,
            name='News Author',
            bio='Journalist'
        )
        # Create commenters
        self.commenter1 = User.objects.create_user(
            email='commenter1@example.com',
            password='testpass123',
            name='Commenter One'
        )
        self.commenter2 = User.objects.create_user(
            email='commenter2@example.com',
            password='testpass123',
            name='Commenter Two'
        )
        # Create news article
        self.news = News.objects.create(
            title='Test News',
            content='News content',
            author=self.author,
            status='published'
        )
        # URLs
        self.news_url = reverse('news-detail', args=[self.news.id])
        self.comment_url = reverse('news-comment-list')
        self.message_url = reverse('message-list')
        cache.clear()

    def test_news_comment_messaging_flow(self):
        """Test complete flow from news comment to messaging"""
        # Commenter posts comment
        self.client.force_authenticate(user=self.commenter1)
        response = self.client.post(self.comment_url, {
            'news': self.news.id,
            'content': 'Great article!'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        comment_id = response.data['id']

        # Verify comment created
        comment = NewsComment.objects.get(id=comment_id)
        self.assertEqual(comment.author, self.commenter1)
        self.assertEqual(comment.news, self.news)

        # Author receives notification
        notification = MessageNotification.objects.filter(
            recipient=self.author,
            notification_type='new_comment'
        ).first()
        self.assertIsNotNone(notification)
        self.assertFalse(notification.read)

        # Author responds via message
        self.client.force_authenticate(user=self.author)
        response = self.client.post(self.message_url, {
            'receiver_id': self.commenter1.id,
            'content': 'Thank you for your comment!'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Commenter responds to message
        self.client.force_authenticate(user=self.commenter1)
        response = self.client.post(self.message_url, {
            'receiver_id': self.author.id,
            'content': 'You\'re welcome!'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Verify message thread
        messages = Message.objects.filter(
            sender__in=[self.author, self.commenter1],
            receiver__in=[self.author, self.commenter1]
        ).order_by('created_at')
        self.assertEqual(messages.count(), 2)

    def test_concurrent_comment_messaging(self):
        """Test concurrent comments and messaging"""
        def comment_and_message(commenter):
            with transaction.atomic():
                # Post comment
                self.client.force_authenticate(user=commenter)
                response = self.client.post(self.comment_url, {
                    'news': self.news.id,
                    'content': f'Comment from {commenter.name}'
                })
                self.assertEqual(response.status_code, status.HTTP_201_CREATED)

                # Send message to author
                response = self.client.post(self.message_url, {
                    'receiver_id': self.author.id,
                    'content': f'Hello, I am {commenter.name}'
                })
                self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Simulate concurrent comments
        commenters = [self.commenter1, self.commenter2]
        threads = []
        for commenter in commenters:
            thread = threading.Thread(target=comment_and_message, args=(commenter,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Verify all comments and messages were created
        self.assertEqual(NewsComment.objects.count(), 2)
        self.assertEqual(Message.objects.filter(sender__in=commenters).count(), 2)
        self.assertEqual(MessageNotification.objects.filter(recipient=self.author).count(), 4)  # 2 comments + 2 messages

    def test_comment_moderation_flow(self):
        """Test comment moderation and messaging flow"""
        # Commenter posts comment
        self.client.force_authenticate(user=self.commenter1)
        response = self.client.post(self.comment_url, {
            'news': self.news.id,
            'content': 'This is a test comment'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        comment_id = response.data['id']

        # Author moderates comment
        self.client.force_authenticate(user=self.author)
        response = self.client.patch(
            reverse('news-comment-detail', args=[comment_id]),
            {'is_hidden': True}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Author sends message to commenter
        response = self.client.post(self.message_url, {
            'receiver_id': self.commenter1.id,
            'content': 'Your comment has been moderated. Please review our community guidelines.'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Verify comment is hidden
        comment = NewsComment.objects.get(id=comment_id)
        self.assertTrue(comment.is_hidden)

        # Verify notification sent
        notification = MessageNotification.objects.filter(
            recipient=self.commenter1,
            notification_type='comment_moderated'
        ).first()
        self.assertIsNotNone(notification)
        self.assertFalse(notification.read) 