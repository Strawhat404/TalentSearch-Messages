from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from .models import Message

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
