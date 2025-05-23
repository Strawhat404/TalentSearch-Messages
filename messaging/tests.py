from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from .models import Message, MessageThread
from django.utils import timezone
import time
from django.core.cache import cache
from django.db import transaction
from django.db.utils import IntegrityError
import threading
import uuid

User = get_user_model()

class MessageModelTest(TestCase):
    def setUp(self):
        self.sender = User.objects.create_user(
            email='sender@example.com',
            password='testpass',
            name='Sender User'
        )
        self.receiver = User.objects.create_user(
            email='receiver@example.com',
            password='testpass',
            name='Receiver User'
        )
        self.message = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            message='Hello!'
        )

    def test_message_creation(self):
        self.assertEqual(self.message.sender, self.sender)
        self.assertEqual(self.message.receiver, self.receiver)
        self.assertEqual(self.message.message, 'Hello!')
        self.assertFalse(self.message.is_read)
        self.assertTrue(self.message.created_at)

    def test_message_str(self):
        expected = f"Message from {self.sender} to {self.receiver} at {self.message.created_at}"
        self.assertEqual(str(self.message), expected)

class MessageAPITest(TestCase):
    throttle_classes = []

    def setUp(self):
        self.client = APIClient()
        self.sender = User.objects.create_user(
            email='sender@example.com',
            password='testpass',
            name='Sender User'
        )
        self.receiver = User.objects.create_user(
            email='receiver@example.com',
            password='testpass',
            name='Receiver User'
        )
        self.inactive_user = User.objects.create_user(
            email='inactive@example.com',
            password='testpass',
            name='Inactive User',
            is_active=False
        )
        self.client.force_authenticate(user=self.sender)
        self.message = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            message='Hello!'
        )
        self.url = reverse('message_list_create')

    def test_list_messages(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_list_messages_filter_by_sender(self):
        response = self.client.get(self.url, {'sender_id': self.sender.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for msg in response.data:
            self.assertEqual(msg['sender_id'], self.sender.id)

    def test_list_messages_filter_by_receiver(self):
        response = self.client.get(self.url, {'receiver_id': self.receiver.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for msg in response.data:
            self.assertEqual(msg['receiver_id'], self.receiver.id)

    def test_create_message(self):
        data = {
            'sender_id': self.sender.id,
            'receiver_id': self.receiver.id,
            'message': 'Test message'
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('id', response.data)
        self.assertEqual(response.data['message'], 'Message sent successfully.')

    def test_message_length_validation(self):
        # Test empty message
        data = {
            'sender_id': self.sender.id,
            'receiver_id': self.receiver.id,
            'message': ''
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('message', response.data)

        # Test message too long
        data['message'] = 'x' * 5001
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('message', response.data)

    def test_self_messaging_validation(self):
        data = {
            'sender_id': self.sender.id,
            'receiver_id': self.sender.id,  # Same as sender
            'message': 'Test message'
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('receiver_id', response.data)

    def test_inactive_user_validation(self):
        # Test sending to inactive user
        data = {
            'sender_id': self.sender.id,
            'receiver_id': self.inactive_user.id,
            'message': 'Test message'
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_message_content_sanitization(self):
        # Test HTML content sanitization
        data = {
            'sender_id': self.sender.id,
            'receiver_id': self.receiver.id,
            'message': '<script>alert("xss")</script>Hello <b>World</b>'
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify the message was sanitized
        message = Message.objects.latest('created_at')
        self.assertEqual(message.message, 'Hello World')

class MessageRateLimitTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user1 = User.objects.create_user(
            email='user1@example.com',
            password='testpass123',
            name='User One'
        )
        self.user2 = User.objects.create_user(
            email='user2@example.com',
            password='testpass123',
            name='User Two'
        )
        self.client.force_authenticate(user=self.user1)
        self.message_url = reverse('message-list')

    def test_rate_limit_authenticated_user(self):
        """Test rate limiting for authenticated users"""
        # Send messages up to rate limit
        for _ in range(10):  # Assuming rate limit is 10 messages per minute
            response = self.client.post(self.message_url, {
                'receiver': self.user2.id,
                'content': 'Test message'
            })
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Try to send one more message
        response = self.client.post(self.message_url, {
            'receiver': self.user2.id,
            'content': 'Rate limit test'
        })
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_rate_limit_reset(self):
        """Test rate limit reset after cooldown period"""
        # Send messages up to rate limit
        for _ in range(10):
            self.client.post(self.message_url, {
                'receiver': self.user2.id,
                'content': 'Test message'
            })

        # Wait for rate limit to reset (assuming 1 minute cooldown)
        time.sleep(61)

        # Try sending message again
        response = self.client.post(self.message_url, {
            'receiver': self.user2.id,
            'content': 'After cooldown'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_rate_limit_anonymous_user(self):
        """Test rate limiting for anonymous users"""
        self.client.force_authenticate(user=None)
        
        # Try to send message as anonymous user
        response = self.client.post(self.message_url, {
            'receiver': self.user2.id,
            'content': 'Anonymous message'
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

class MessageUserValidationTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user1 = User.objects.create_user(
            email='user1@example.com',
            password='testpass123',
            name='User One'
        )
        self.user2 = User.objects.create_user(
            email='user2@example.com',
            password='testpass123',
            name='User Two'
        )
        self.client.force_authenticate(user=self.user1)
        self.message_url = reverse('message-list')

    def test_send_to_nonexistent_user(self):
        """Test sending message to non-existent user"""
        response = self.client.post(self.message_url, {
            'receiver': 99999,  # Non-existent user ID
            'content': 'Test message'
        })
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_send_from_deleted_user(self):
        """Test sending message from deleted user account"""
        self.user1.delete()
        response = self.client.post(self.message_url, {
            'receiver': self.user2.id,
            'content': 'Test message'
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_send_to_inactive_user(self):
        """Test sending message to inactive user"""
        self.user2.is_active = False
        self.user2.save()
        
        response = self.client.post(self.message_url, {
            'receiver': self.user2.id,
            'content': 'Test message'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_similar_user_ids(self):
        """Test message delivery with similar user IDs"""
        # Create users with similar IDs
        user3 = User.objects.create_user(
            email='user3@example.com',
            password='testpass123',
            name='User Three'
        )
        
        # Send message to correct user
        response = self.client.post(self.message_url, {
            'receiver': user3.id,
            'content': 'Test message'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

class MessageContentValidationTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user1 = User.objects.create_user(
            email='user1@example.com',
            password='testpass123',
            name='User One'
        )
        self.user2 = User.objects.create_user(
            email='user2@example.com',
            password='testpass123',
            name='User Two'
        )
        self.client.force_authenticate(user=self.user1)
        self.message_url = reverse('message-list')

    def test_empty_message(self):
        """Test sending empty message"""
        response = self.client.post(self.message_url, {
            'receiver': self.user2.id,
            'content': ''
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_large_message(self):
        """Test sending extremely large message"""
        large_content = 'x' * 10001  # Assuming 10000 is the limit
        response = self.client.post(self.message_url, {
            'receiver': self.user2.id,
            'content': large_content
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_xss_content(self):
        """Test message with potential XSS content"""
        xss_content = '<script>alert("xss")</script>'
        response = self.client.post(self.message_url, {
            'receiver': self.user2.id,
            'content': xss_content
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Verify content was sanitized
        message = Message.objects.latest('created_at')
        self.assertNotIn('<script>', message.content)

    def test_unicode_emoji(self):
        """Test message with Unicode characters and emoji"""
        unicode_content = 'Hello 👋 World 🌍 你好'
        response = self.client.post(self.message_url, {
            'receiver': self.user2.id,
            'content': unicode_content
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        message = Message.objects.latest('created_at')
        self.assertEqual(message.content, unicode_content)

    def test_formatting_characters(self):
        """Test message with newlines and formatting characters"""
        formatted_content = 'Line 1\nLine 2\r\nLine 3\tTabbed'
        response = self.client.post(self.message_url, {
            'receiver': self.user2.id,
            'content': formatted_content
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        message = Message.objects.latest('created_at')
        self.assertEqual(message.content, formatted_content)

class MessageErrorHandlingTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user1 = User.objects.create_user(
            email='user1@example.com',
            password='testpass123',
            name='User One'
        )
        self.user2 = User.objects.create_user(
            email='user2@example.com',
            password='testpass123',
            name='User Two'
        )
        self.client.force_authenticate(user=self.user1)
        self.message_url = reverse('message-list')

    def test_database_failure(self):
        """Test handling of database failures"""
        # Simulate database failure by using an invalid transaction
        with transaction.atomic():
            # Create a message that would violate a unique constraint
            Message.objects.create(
                sender=self.user1,
                receiver=self.user2,
                content='Test message 1'
            )
            try:
                # Try to create the same message again
                Message.objects.create(
                    sender=self.user1,
                    receiver=self.user2,
                    content='Test message 1'
                )
            except IntegrityError:
                pass

        # Verify system is still operational
        response = self.client.post(self.message_url, {
            'receiver': self.user2.id,
            'content': 'New message'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_race_condition(self):
        """Test handling of race conditions"""
        def send_message():
            self.client.post(self.message_url, {
                'receiver': self.user2.id,
                'content': f'Message {uuid.uuid4()}'
            })

        # Create multiple threads to send messages simultaneously
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=send_message)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify all messages were saved
        message_count = Message.objects.filter(
            sender=self.user1,
            receiver=self.user2
        ).count()
        self.assertEqual(message_count, 5)

    def test_queue_full(self):
        """Test behavior when message queue is full"""
        # Simulate queue full condition
        cache.set('message_queue_full', True, 60)
        
        response = self.client.post(self.message_url, {
            'receiver': self.user2.id,
            'content': 'Test message'
        })
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        
        # Clear the queue full condition
        cache.delete('message_queue_full')
        
        # Verify system returns to normal operation
        response = self.client.post(self.message_url, {
            'receiver': self.user2.id,
            'content': 'Test message'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

class MessageThreadViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user1)
        self.thread_url = reverse('thread-list')

    def test_create_thread(self):
        """Test creating a new message thread"""
        data = {
            'participant_ids': [self.user2.id],
            'title': 'Test Thread'
        }
        response = self.client.post(self.thread_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(MessageThread.objects.count(), 1)
        thread = MessageThread.objects.first()
        self.assertEqual(thread.participants.count(), 2)
        self.assertEqual(thread.title, 'Test Thread')

    def test_list_threads(self):
        """Test listing all threads for a user"""
        # Create a thread
        thread = MessageThread.objects.create(title='Test Thread')
        thread.participants.add(self.user1, self.user2)

        response = self.client.get(self.thread_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'Test Thread')

class MessageThreadDetailViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user1)
        
        # Create a thread
        self.thread = MessageThread.objects.create(title='Test Thread')
        self.thread.participants.add(self.user1, self.user2)
        self.thread_url = reverse('thread-detail', args=[self.thread.id])

    def test_get_thread_details(self):
        """Test getting thread details"""
        response = self.client.get(self.thread_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Test Thread')
        self.assertEqual(len(response.data['participants']), 2)

    def test_update_thread(self):
        """Test updating thread details"""
        data = {'title': 'Updated Thread'}
        response = self.client.put(self.thread_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.thread.refresh_from_db()
        self.assertEqual(self.thread.title, 'Updated Thread')

    def test_delete_thread(self):
        """Test soft deleting a thread"""
        response = self.client.delete(self.thread_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.thread.refresh_from_db()
        self.assertFalse(self.thread.is_active)

class MessageViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user1)
        
        # Create a thread
        self.thread = MessageThread.objects.create(title='Test Thread')
        self.thread.participants.add(self.user1, self.user2)
        self.message_url = reverse('message-list')

    def test_create_message(self):
        """Test creating a new message in a thread"""
        data = {
            'thread_id': self.thread.id,
            'content': 'Hello, this is a test message!'
        }
        response = self.client.post(self.message_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Message.objects.count(), 1)
        message = Message.objects.first()
        self.assertEqual(message.content, 'Hello, this is a test message!')
        self.assertEqual(message.sender, self.user1)
        self.assertEqual(message.thread, self.thread)

    def test_list_messages(self):
        """Test listing messages in a thread"""
        # Create some messages
        Message.objects.create(
            thread=self.thread,
            sender=self.user1,
            receiver=self.user2,
            content='Message 1'
        )
        Message.objects.create(
            thread=self.thread,
            sender=self.user2,
            receiver=self.user1,
            content='Message 2'
        )

        response = self.client.get(f'{self.message_url}?thread_id={self.thread.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_message_queue_full(self):
        """Test message creation when queue is full"""
        cache.set('message_queue_full', True)
        data = {
            'thread_id': self.thread.id,
            'content': 'Test message'
        }
        response = self.client.post(self.message_url, data)
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        cache.delete('message_queue_full')

    def test_rate_limiting(self):
        """Test rate limiting for message creation"""
        data = {
            'thread_id': self.thread.id,
            'content': 'Test message'
        }
        # Make 11 requests in quick succession
        for _ in range(11):
            response = self.client.post(self.message_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
