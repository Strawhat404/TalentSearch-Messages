from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from .models import GalleryItem
from .serializers import GalleryItemSerializer
from userprofile.models import Profile
import os
import glob
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()


class GalleryItemModelTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='testuser@example.com', password='testpass')
        self.profile = Profile.objects.create(user=self.user, name='Test Profile', profession='Tester')
        self.valid_image = SimpleUploadedFile('test.jpg', b'file_content' * 100, content_type='image/jpeg')
        self.valid_video = SimpleUploadedFile('test.mp4', b'file_content' * 100, content_type='video/mp4')

    def test_gallery_item_creation(self):
        gallery_item = GalleryItem.objects.create(
            profile_id=self.profile,
            item_url=self.valid_image,
            item_type='image',
            description='Test image'
        )
        self.assertEqual(gallery_item.item_type, 'image')
        self.assertEqual(gallery_item.description, 'Test image')
        self.assertTrue(os.path.exists(gallery_item.item_url.path))

    def test_gallery_item_invalid_extension(self):
        invalid_file = SimpleUploadedFile('test.txt', b'file_content' * 100, content_type='text/plain')
        with self.assertRaises(ValueError):
            GalleryItem.objects.create(
                profile_id=self.profile,
                item_url=invalid_file,
                item_type='image',
                description='Test invalid'
            )

    def test_gallery_item_save_method(self):
        gallery_item = GalleryItem(profile_id=self.profile, item_url=self.valid_video, description='Test video')
        gallery_item.save()
        self.assertEqual(gallery_item.item_type, 'video')


class GalleryItemSerializerTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='testuser@example.com', password='testpass')
        self.profile = Profile.objects.create(user=self.user, name='Test Profile', profession='Tester')
        self.valid_image = SimpleUploadedFile('test.jpg', b'file_content' * 100, content_type='image/jpeg')
        self.data = {
            'profile_id': self.profile.id,
            'item_url': self.valid_image,
            'item_type': 'image',
            'description': 'Test image'
        }

    def test_serializer_valid_data(self):
        serializer = GalleryItemSerializer(data=self.data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        gallery_item = serializer.save()
        self.assertEqual(gallery_item.profile_id, self.profile)
        self.assertEqual(gallery_item.item_type, 'image')

    def test_serializer_invalid_extension(self):
        invalid_file = SimpleUploadedFile('test.txt', b'file_content' * 100, content_type='text/plain')
        data = self.data.copy()
        data['item_url'] = invalid_file
        serializer = GalleryItemSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('item_url', serializer.errors)

    def test_serializer_large_file(self):
        large_file = SimpleUploadedFile('test.jpg', b'0' * (51 * 1024 * 1024), content_type='image/jpeg')  # >50MB
        data = self.data.copy()
        data['item_url'] = large_file
        serializer = GalleryItemSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('item_url', serializer.errors)

    def test_serializer_invalid_profile_id(self):
        data = self.data.copy()
        data['profile_id'] = 999  # Non-existent profile ID
        serializer = GalleryItemSerializer(data=data)
        self.assertTrue(serializer.is_valid())  # Validation passes, but creation should fail
        with self.assertRaises(Profile.DoesNotExist):
            serializer.save()


class GalleryItemViewTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.gallery_dir = os.path.join(settings.MEDIA_ROOT, 'gallery')
        if not os.path.exists(cls.gallery_dir):
            os.makedirs(cls.gallery_dir)

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(email='testuser@example.com', password='testpass')
        self.profile = Profile.objects.create(user=self.user, name='Test Profile', profession='Tester')
        self.client.force_authenticate(user=self.user)  # 🔐 Enforce authentication
        self.valid_image = SimpleUploadedFile('test.jpg', b'file_content' * 100, content_type='image/jpeg')
        print(f"Test file size: {self.valid_image.size} bytes")  # Debug file size
        self.gallery_item = GalleryItem.objects.create(
            profile_id=self.profile,
            item_url=self.valid_image,
            item_type='image',
            description='Test image'
        )
        self.list_url = reverse('gallery-item-list-create')
        self.detail_url = reverse('gallery-item-detail', kwargs={'id': self.gallery_item.id})

    def test_list_gallery_items(self):
        response = self.client.get(self.list_url, {'profile_id': self.profile.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['profile_id'], self.profile.id)

    def test_list_gallery_items_no_profile_id(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)  # Since profile_id is None

    def test_create_gallery_item(self):
        # Create a fresh file for this test to avoid file pointer issues
        fresh_image = SimpleUploadedFile('test.jpg', b'file_content' * 100, content_type='image/jpeg')
        data = {
            'profile_id': str(self.profile.id),
            'item_url': fresh_image,
            'item_type': 'image',
            'description': 'New test image'
        }
        response = self.client.post(self.list_url, data, format='multipart')
        if response.status_code != status.HTTP_201_CREATED:
            print(f"Serializer errors: {response.data}")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(GalleryItem.objects.count(), 2)

    def test_create_invalid_extension(self):
        invalid_file = SimpleUploadedFile('test.txt', b'file_content' * 100, content_type='text/plain')
        data = {
            'profile_id': str(self.profile.id),
            'item_url': invalid_file,
            'item_type': 'image',
            'description': 'Invalid test'
        }
        response = self.client.post(self.list_url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('item_url', response.data)

    def test_retrieve_gallery_item(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.gallery_item.id)

    def test_retrieve_nonexistent_gallery_item(self):
        url = reverse('gallery-item-detail', kwargs={'id': 999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_gallery_item(self):
        new_image = SimpleUploadedFile('new.jpg', b'new_content' * 100, content_type='image/jpeg')
        data = {'item_url': new_image, 'description': 'Updated image'}
        response = self.client.put(self.detail_url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Gallery item updated successfully.')
        updated_item = GalleryItem.objects.get(id=self.gallery_item.id)
        self.assertEqual(updated_item.description, 'Updated image')

    def test_update_nonexistent_gallery_item(self):
        url = reverse('gallery-item-detail', kwargs={'id': 999})
        new_image = SimpleUploadedFile('new.jpg', b'new_content' * 100, content_type='image/jpeg')
        data = {'item_url': new_image, 'description': 'Updated image'}
        response = self.client.put(url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_gallery_item(self):
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(GalleryItem.objects.count(), 0)

    def test_delete_nonexistent_gallery_item(self):
        url = reverse('gallery-item-detail', kwargs={'id': 999})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @classmethod
    def tearDownClass(cls):
        """Clean up all test files in media/gallery/ after all tests."""
        gallery_dir = os.path.join(settings.MEDIA_ROOT, 'gallery')
        test_files = glob.glob(os.path.join(gallery_dir, 'test_*.jpg')) + \
                     glob.glob(os.path.join(gallery_dir, 'test_*.mp4')) + \
                     glob.glob(os.path.join(gallery_dir, 'new.jpg'))
        for file_path in test_files:
            if os.path.isfile(file_path):
                os.remove(file_path)

        super().tearDownClass()
