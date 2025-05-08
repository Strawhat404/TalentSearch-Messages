from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import Profile
from .serializers import ProfileSerializer

User = get_user_model()

class ProfileModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.profile = Profile.objects.create(
            user=self.user,
            name='Test User',
            profession='Developer',
            birthdate='1990-01-01',
            weight=70.0,
            height=175.0,
            gender='male',
            nationality='US',
            languages=['English'],
            skills=['Python', 'Django'],
            interests=['Programming', 'Reading'],
            bio='Test bio'
        )

    def test_profile_creation(self):
        self.assertEqual(self.profile.name, 'Test User')
        self.assertEqual(self.profile.profession, 'Developer')
        self.assertEqual(self.profile.user, self.user)

    def test_profile_age_calculation(self):
        self.assertIsNotNone(self.profile.age)

class ProfileAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        self.profile = Profile.objects.create(
            user=self.user,
            name='Test User',
            profession='Developer',
            birthdate='1990-01-01',
            weight=70.0,
            height=175.0,
            gender='male',
            nationality='US',
            languages=['English'],
            skills=['Python', 'Django'],
            interests=['Programming', 'Reading'],
            bio='Test bio'
        )
        self.profile_url = reverse('profile-detail', kwargs={'pk': self.profile.pk})
        self.profiles_url = reverse('profile-list')

    def test_get_profile_list(self):
        response = self.client.get(self.profiles_url)
        profiles = Profile.objects.all()
        serializer = ProfileSerializer(profiles, many=True)
        self.assertEqual(response.data, serializer.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_profile_detail(self):
        response = self.client.get(self.profile_url)
        serializer = ProfileSerializer(self.profile)
        self.assertEqual(response.data, serializer.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_profile(self):
        data = {
            'name': 'Updated User',
            'profession': 'Senior Developer',
            'birthdate': '1990-01-01',
            'weight': 75.0,
            'height': 180.0,
            'gender': 'male',
            'nationality': 'US',
            'languages': ['English', 'Spanish'],
            'skills': ['Python', 'Django', 'React'],
            'interests': ['Programming', 'Reading', 'Gaming'],
            'bio': 'Updated bio'
        }
        response = self.client.put(self.profile_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.name, 'Updated User')
        self.assertEqual(self.profile.profession, 'Senior Developer')

    def test_partial_update_profile(self):
        data = {'name': 'Partially Updated User'}
        response = self.client.patch(self.profile_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.name, 'Partially Updated User') 