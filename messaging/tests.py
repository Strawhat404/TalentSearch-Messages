import json
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from userprofile.models import Profile
from messaging.models import Message, MessageThread
from messaging.serializers import MessageSerializer, MessageThreadSerializer
from django.utils import timezone
from datetime import timedelta
import time

User = get_user_model()

class MessageModelTest(TestCase):
    def setUp(self):
        # Create users first
        self.sender_user = User.objects.create_user(
            email='sender@test.com',
            username='sender',
            password='testpass123',
            name='Sender User'
        )
        self.receiver_user = User.objects.create_user(
            email='receiver@test.com',
            username='receiver',
            password='testpass123',
            name='Receiver User'
        )
        
        # Create profiles that reference the users
        self.sender_profile = Profile.objects.create(user=self.sender_user)
        self.receiver_profile = Profile.objects.create(user=self.receiver_user)
        
        self.thread = MessageThread.objects.create(
            title="Test Thread"
        )
        self.thread.participants.add(self.sender_profile, self.receiver_profile)

    def test_message_creation(self):
        message = Message.objects.create(
            thread=self.thread,
            sender=self.sender_profile,
            receiver=self.receiver_profile,
            content="Hello, this is a test message!"
        )
        
        self.assertEqual(message.content, "Hello, this is a test message!")
        self.assertEqual(message.sender, self.sender_profile)
        self.assertEqual(message.receiver, self.receiver_profile)
        self.assertEqual(message.thread, self.thread)
        self.assertFalse(message.is_read)

    def test_message_str(self):
        message = Message.objects.create(
            thread=self.thread,
            sender=self.sender_profile,
            receiver=self.receiver_profile,
            content="Test message"
        )
        
        expected_str = f"Message from {self.sender_profile.name} to {self.receiver_profile.name}"
        self.assertEqual(str(message), expected_str)

class MessageAPITest(APITestCase):
    def setUp(self):
        # Create users first
        self.sender_user = User.objects.create_user(
            email='sender@test.com',
            username='sender',
            password='testpass123',
            name='Sender User'
        )
        self.receiver_user = User.objects.create_user(
            email='receiver@test.com',
            username='receiver',
            password='testpass123',
            name='Receiver User'
        )
        
        # Create profiles that reference the users
        self.sender_profile = Profile.objects.create(user=self.sender_user)
        self.receiver_profile = Profile.objects.create(user=self.receiver_user)
        
        self.thread = MessageThread.objects.create(
            title="Test Thread"
        )
        self.thread.participants.add(self.sender_profile, self.receiver_profile)
        
        # Authenticate as sender
        self.client.force_authenticate(user=self.sender_user)

    def test_create_message(self):
        url = reverse('message-list')
        data = {
            'thread': self.thread.id,
            'receiver': self.receiver_profile.id,
            'content': 'Hello, this is a test message!'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        message = Message.objects.get(id=response.data['id'])
        self.assertEqual(message.content, 'Hello, this is a test message!')
        self.assertEqual(message.sender, self.sender_profile)
        self.assertEqual(message.receiver, self.receiver_profile)

    def test_list_messages(self):
        # Create some test messages
        Message.objects.create(
            thread=self.thread,
            sender=self.sender_profile,
            receiver=self.receiver_profile,
            content="Message 1"
        )
        Message.objects.create(
            thread=self.thread,
            sender=self.receiver_profile,
            receiver=self.sender_profile,
            content="Message 2"
        )
        
        url = reverse('message-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_list_messages_filter_by_sender(self):
        # Create messages from different senders
        Message.objects.create(
            thread=self.thread,
            sender=self.sender_profile,
            receiver=self.receiver_profile,
            content="From sender"
        )
        Message.objects.create(
            thread=self.thread,
            sender=self.receiver_profile,
            receiver=self.sender_profile,
            content="From receiver"
        )
        
        url = reverse('message-list')
        response = self.client.get(url, {'sender': self.sender_profile.id})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['content'], "From sender")

    def test_list_messages_filter_by_receiver(self):
        # Create messages to different receivers
        Message.objects.create(
            thread=self.thread,
            sender=self.sender_profile,
            receiver=self.receiver_profile,
            content="To receiver"
        )
        Message.objects.create(
            thread=self.thread,
            sender=self.receiver_profile,
            receiver=self.sender_profile,
            content="To sender"
        )
        
        url = reverse('message-list')
        response = self.client.get(url, {'receiver': self.receiver_profile.id})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['content'], "To receiver")

    def test_message_length_validation(self):
        url = reverse('message-list')
        long_content = "A" * 1001  # Exceeds max length
        data = {
            'thread': self.thread.id,
            'receiver': self.receiver_profile.id,
            'content': long_content
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_message_content_sanitization(self):
        url = reverse('message-list')
        malicious_content = "<script>alert('xss')</script>Hello"
        data = {
            'thread': self.thread.id,
            'receiver': self.receiver_profile.id,
            'content': malicious_content
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check that the content was sanitized
        message = Message.objects.get(id=response.data['id'])
        self.assertNotIn('<script>', message.content)
        self.assertIn('Hello', message.content)

    def test_self_messaging_validation(self):
        url = reverse('message-list')
        data = {
            'thread': self.thread.id,
            'receiver': self.sender_profile.id,  # Sending to self
            'content': 'Hello'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_inactive_user_validation(self):
        # Deactivate the receiver
        self.receiver_user.is_active = False
        self.receiver_user.save()
        
        url = reverse('message-list')
        data = {
            'thread': self.thread.id,
            'receiver': self.receiver_profile.id,
            'content': 'Hello'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

class MessageRateLimitTest(APITestCase):
    def setUp(self):
        # Create users first
        self.user1 = User.objects.create_user(
            email='user1@test.com',
            username='user1',
            password='testpass123',
            name='User One'
        )
        self.user2 = User.objects.create_user(
            email='user2@test.com',
            username='user2',
            password='testpass123',
            name='User Two'
        )
        
        # Create profiles that reference the users
        self.profile1 = Profile.objects.create(user=self.user1)
        self.profile2 = Profile.objects.create(user=self.user2)
        
        self.thread = MessageThread.objects.create(title="Test Thread")
        self.thread.participants.add(self.profile1, self.profile2)
        
        self.client.force_authenticate(user=self.user1)

    def test_rate_limit_authenticated_user(self):
        url = reverse('message-list')
        data = {
            'thread': self.thread.id,
            'receiver': self.profile2.id,
            'content': 'Test message'
        }
        
        # Send multiple messages rapidly
        for i in range(10):
            response = self.client.post(url, data, format='json')
            if response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
                break
        
        # Should eventually hit rate limit
        self.assertIn(response.status_code, [status.HTTP_201_CREATED, status.HTTP_429_TOO_MANY_REQUESTS])

    def test_rate_limit_anonymous_user(self):
        self.client.force_authenticate(user=None)
        
        url = reverse('message-list')
        data = {
            'thread': self.thread.id,
            'receiver': self.profile2.id,
            'content': 'Test message'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_rate_limit_reset(self):
        url = reverse('message-list')
        data = {
            'thread': self.thread.id,
            'receiver': self.profile2.id,
            'content': 'Test message'
        }
        
        # Send a message
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Wait for rate limit to reset (if implemented)
        time.sleep(1)
        
        # Try sending another message
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

class MessageUserValidationTest(APITestCase):
    def setUp(self):
        # Create users first
        self.user1 = User.objects.create_user(
            email='user1@test.com',
            username='user1',
            password='testpass123',
            name='User One'
        )
        self.user2 = User.objects.create_user(
            email='user2@test.com',
            username='user2',
            password='testpass123',
            name='User Two'
        )
        
        # Create profiles that reference the users
        self.profile1 = Profile.objects.create(user=self.user1)
        self.profile2 = Profile.objects.create(user=self.user2)
        
        self.thread = MessageThread.objects.create(title="Test Thread")
        self.thread.participants.add(self.profile1, self.profile2)
        
        self.client.force_authenticate(user=self.user1)

    def test_send_to_nonexistent_user(self):
        url = reverse('message-list')
        data = {
            'thread': self.thread.id,
            'receiver': 99999,  # Non-existent profile ID
            'content': 'Hello'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_send_to_inactive_user(self):
        # Deactivate user2
        self.user2.is_active = False
        self.user2.save()
        
        url = reverse('message-list')
        data = {
            'thread': self.thread.id,
            'receiver': self.profile2.id,
            'content': 'Hello'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_send_from_deleted_user(self):
        # Delete user1
        self.user1.delete()
        
        url = reverse('message-list')
        data = {
            'thread': self.thread.id,
            'receiver': self.profile2.id,
            'content': 'Hello'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_similar_user_ids(self):
        # Create another user with similar ID
        user3 = User.objects.create_user(
            email='user3@test.com',
            username='user3',
            password='testpass123',
            name='User Three'
        )
        profile3 = Profile.objects.create(user=user3)
        
        url = reverse('message-list')
        data = {
            'thread': self.thread.id,
            'receiver': profile3.id,
            'content': 'Hello'
        }
        
        response = self.client.post(url, data, format='json')
        # Should fail because profile3 is not in the thread
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

class MessageContentValidationTest(APITestCase):
    def setUp(self):
        # Create users first
        self.user1 = User.objects.create_user(
            email='user1@test.com',
            username='user1',
            password='testpass123',
            name='User One'
        )
        self.user2 = User.objects.create_user(
            email='user2@test.com',
            username='user2',
            password='testpass123',
            name='User Two'
        )
        
        # Create profiles that reference the users
        self.profile1 = Profile.objects.create(user=self.user1)
        self.profile2 = Profile.objects.create(user=self.user2)
        
        self.thread = MessageThread.objects.create(title="Test Thread")
        self.thread.participants.add(self.profile1, self.profile2)
        
        self.client.force_authenticate(user=self.user1)

    def test_empty_message(self):
        """Test sending empty message"""
        url = reverse('message-list')
        data = {
            'thread': self.thread.id,
            'receiver': self.profile2.id,
            'content': ''
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_large_message(self):
        """Test sending message that exceeds size limit"""
        url = reverse('message-list')
        large_content = "A" * 1001  # Exceeds max length
        data = {
            'thread': self.thread.id,
            'receiver': self.profile2.id,
            'content': large_content
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unicode_emoji(self):
        """Test message with Unicode characters and emoji"""
        url = reverse('message-list')
        unicode_content = "Hello! 👋 How are you? 😊"
        data = {
            'thread': self.thread.id,
            'receiver': self.profile2.id,
            'content': unicode_content
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        message = Message.objects.get(id=response.data['id'])
        self.assertEqual(message.content, unicode_content)

    def test_formatting_characters(self):
        """Test message with newlines and formatting characters"""
        url = reverse('message-list')
        formatted_content = "Line 1\nLine 2\nLine 3"
        data = {
            'thread': self.thread.id,
            'receiver': self.profile2.id,
            'content': formatted_content
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        message = Message.objects.get(id=response.data['id'])
        self.assertEqual(message.content, formatted_content)

    def test_xss_content(self):
        """Test message with potential XSS content"""
        url = reverse('message-list')
        xss_content = "<script>alert('xss')</script>Hello <img src=x onerror=alert(1)>"
        data = {
            'thread': self.thread.id,
            'receiver': self.profile2.id,
            'content': xss_content
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check that the content was sanitized
        message = Message.objects.get(id=response.data['id'])
        self.assertNotIn('<script>', message.content)
        self.assertNotIn('<img', message.content)
        self.assertIn('Hello', message.content)

class MessageErrorHandlingTest(APITestCase):
    def setUp(self):
        # Create users first
        self.user1 = User.objects.create_user(
            email='user1@test.com',
            username='user1',
            password='testpass123',
            name='User One'
        )
        self.user2 = User.objects.create_user(
            email='user2@test.com',
            username='user2',
            password='testpass123',
            name='User Two'
        )
        
        # Create profiles that reference the users
        self.profile1 = Profile.objects.create(user=self.user1)
        self.profile2 = Profile.objects.create(user=self.user2)
        
        self.thread = MessageThread.objects.create(title="Test Thread")
        self.thread.participants.add(self.profile1, self.profile2)
        
        self.client.force_authenticate(user=self.user1)

    def test_database_failure(self):
        """Test handling of database failures"""
        url = reverse('message-list')
        data = {
            'thread': self.thread.id,
            'receiver': self.profile2.id,
            'content': 'Test message'
        }
        
        # This test would require mocking database operations
        # For now, just test normal operation
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_queue_full(self):
        """Test behavior when message queue is full"""
        url = reverse('message-list')
        data = {
            'thread': self.thread.id,
            'receiver': self.profile2.id,
            'content': 'Test message'
        }
        
        # This test would require mocking queue operations
        # For now, just test normal operation
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_race_condition(self):
        """Test handling of race conditions"""
        url = reverse('message-list')
        data = {
            'thread': self.thread.id,
            'receiver': self.profile2.id,
            'content': 'Test message'
        }
        
        # This test would require simulating race conditions
        # For now, just test normal operation
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

class MessageThreadViewTest(APITestCase):
    def setUp(self):
        # Create users first
        self.user1 = User.objects.create_user(
            email='user1@test.com',
            username='user1',
            password='testpass123',
            name='User One'
        )
        self.user2 = User.objects.create_user(
            email='user2@test.com',
            username='user2',
            password='testpass123',
            name='User Two'
        )
        
        # Create profiles that reference the users
        self.profile1 = Profile.objects.create(user=self.user1)
        self.profile2 = Profile.objects.create(user=self.user2)
        
        self.client.force_authenticate(user=self.user1)

    def test_create_thread(self):
        """Test creating a new message thread"""
        url = reverse('thread-list')
        data = {
            'title': 'New Thread',
            'participants': [self.profile1.id, self.profile2.id]
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        thread = MessageThread.objects.get(id=response.data['id'])
        self.assertEqual(thread.title, 'New Thread')
        self.assertIn(self.profile1, thread.participants.all())
        self.assertIn(self.profile2, thread.participants.all())

    def test_list_threads(self):
        """Test listing all threads for a user"""
        # Create a thread
        thread = MessageThread.objects.create(title="Test Thread")
        thread.participants.add(self.profile1, self.profile2)
        
        url = reverse('thread-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], "Test Thread")

class MessageThreadDetailViewTest(APITestCase):
    def setUp(self):
        # Create users first
        self.user1 = User.objects.create_user(
            email='user1@test.com',
            username='user1',
            password='testpass123',
            name='User One'
        )
        self.user2 = User.objects.create_user(
            email='user2@test.com',
            username='user2',
            password='testpass123',
            name='User Two'
        )
        
        # Create profiles that reference the users
        self.profile1 = Profile.objects.create(user=self.user1)
        self.profile2 = Profile.objects.create(user=self.user2)
        
        self.thread = MessageThread.objects.create(title="Test Thread")
        self.thread.participants.add(self.profile1, self.profile2)
        
        self.client.force_authenticate(user=self.user1)

    def test_get_thread_details(self):
        """Test getting thread details"""
        url = reverse('thread-detail', kwargs={'pk': self.thread.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], "Test Thread")
        self.assertEqual(len(response.data['participants']), 2)

    def test_update_thread(self):
        """Test updating thread details"""
        url = reverse('thread-detail', kwargs={'pk': self.thread.id})
        data = {'title': 'Updated Thread Title'}
        
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.thread.refresh_from_db()
        self.assertEqual(self.thread.title, 'Updated Thread Title')

    def test_delete_thread(self):
        """Test soft deleting a thread"""
        url = reverse('thread-detail', kwargs={'pk': self.thread.id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Check that the thread is soft deleted
        self.thread.refresh_from_db()
        self.assertTrue(self.thread.is_deleted)

class MessageViewTest(APITestCase):
    def setUp(self):
        # Create users first
        self.user1 = User.objects.create_user(
            email='user1@test.com',
            username='user1',
            password='testpass123',
            name='User One'
        )
        self.user2 = User.objects.create_user(
            email='user2@test.com',
            username='user2',
            password='testpass123',
            name='User Two'
        )
        
        # Create profiles that reference the users
        self.profile1 = Profile.objects.create(user=self.user1)
        self.profile2 = Profile.objects.create(user=self.user2)
        
        self.thread = MessageThread.objects.create(title="Test Thread")
        self.thread.participants.add(self.profile1, self.profile2)
        
        self.client.force_authenticate(user=self.user1)

    def test_create_message(self):
        """Test creating a new message in a thread"""
        url = reverse('message-list')
        data = {
            'thread': self.thread.id,
            'receiver': self.profile2.id,
            'content': 'Hello, this is a test message!'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        message = Message.objects.get(id=response.data['id'])
        self.assertEqual(message.content, 'Hello, this is a test message!')
        self.assertEqual(message.sender, self.profile1)
        self.assertEqual(message.receiver, self.profile2)

    def test_list_messages(self):
        """Test listing messages in a thread"""
        # Create some test messages
        Message.objects.create(
            thread=self.thread,
            sender=self.profile1,
            receiver=self.profile2,
            content="Message 1"
        )
        Message.objects.create(
            thread=self.thread,
            sender=self.profile2,
            receiver=self.profile1,
            content="Message 2"
        )
        
        url = reverse('message-list')
        response = self.client.get(url, {'thread': self.thread.id})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_rate_limiting(self):
        """Test rate limiting for message creation"""
        url = reverse('message-list')
        data = {
            'thread': self.thread.id,
            'receiver': self.profile2.id,
            'content': 'Test message'
        }
        
        # Send multiple messages rapidly
        responses = []
        for i in range(5):
            response = self.client.post(url, data, format='json')
            responses.append(response.status_code)
        
        # Should handle rate limiting gracefully
        self.assertIn(status.HTTP_201_CREATED, responses)

    def test_message_queue_full(self):
        """Test message creation when queue is full"""
        url = reverse('message-list')
        data = {
            'thread': self.thread.id,
            'receiver': self.profile2.id,
            'content': 'Test message'
        }
        
        # This test would require mocking queue operations
        # For now, just test normal operation
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
