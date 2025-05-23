from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import RentalItem, RentalItemRating
from django.core.files.uploadedfile import SimpleUploadedFile
import json
from rental_ratings.models import Rating

User = get_user_model()

def get_dummy_image():
    return SimpleUploadedFile(
        name='test_image.jpg',
        content=b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b',
        content_type='image/jpeg'
    )

class RentalItemTests(APITestCase):
    def setUp(self):
        # Create test users
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.admin_user = User.objects.create_superuser(
            email='admin@example.com',
            password='adminpass123'
        )
        
        # Create test rental item
        self.rental_item_data = {
            'name': 'Professional 4K Camera',
            'type': 'camera',
            'category': 'professional',
            'description': 'High-end 4K camera with accessories',
            'daily_rate': 2500,
            'image': get_dummy_image(),
            'specs': {
                'resolution': '4K',
                'sensor': 'Full Frame',
                'lens_mount': 'EF',
                'weight': '1.2kg'
            },
            'available': True,
            'featured_item': False
        }
        
        self.client.force_authenticate(user=self.user)
        self.rental_item = RentalItem.objects.create(
            user=self.user,
            name=self.rental_item_data['name'],
            type=self.rental_item_data['type'],
            category=self.rental_item_data['category'],
            description=self.rental_item_data['description'],
            daily_rate=self.rental_item_data['daily_rate'],
            image=get_dummy_image(),
            specs=self.rental_item_data['specs'],
            available=self.rental_item_data['available'],
            featured_item=self.rental_item_data['featured_item']
        )

    def test_create_rental_item(self):
        url = reverse('rental-item-list')
        data = self.rental_item_data.copy()
        data['image'] = get_dummy_image()
        data['specs'] = json.dumps(data['specs'])
        response = self.client.post(url, data, format='multipart')
        if response.status_code != status.HTTP_201_CREATED:
            print('RESPONSE DATA:', response.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(RentalItem.objects.count(), 2)
        self.assertEqual(response.data['name'], self.rental_item_data['name'])

    def test_get_rental_items_list(self):
        url = reverse('rental-item-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_get_rental_item_detail(self):
        url = reverse('rental-item-detail', args=[self.rental_item.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], self.rental_item.name)

    def test_update_rental_item(self):
        url = reverse('rental-item-detail', args=[self.rental_item.id])
        update_data = {
            'name': 'Updated Camera Name',
            'description': 'Updated description',
            'daily_rate': 3000,
            'available': False
        }
        response = self.client.patch(url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.rental_item.refresh_from_db()
        self.assertEqual(self.rental_item.name, update_data['name'])

    def test_delete_rental_item(self):
        url = reverse('rental-item-detail', args=[self.rental_item.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(RentalItem.objects.count(), 0)

    def test_approve_rental_item(self):
        url = reverse('rental-item-approve', args=[self.rental_item.id])
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.put(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.rental_item.refresh_from_db()
        self.assertTrue(self.rental_item.approved)

    def test_rate_rental_item(self):
        url = reverse('rating-list')
        data = {
            'item_id': str(self.rental_item.id),
            'rating': 5,
            'comment': 'Great item!'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Rating.objects.count(), 1)
        self.assertEqual(response.data['rating'], 5)

    def test_filter_rental_items(self):
        # Create another rental item with different category
        RentalItem.objects.create(
            user=self.user,
            name='Drone',
            type='camera',
            category='professional',
            description='Professional drone',
            daily_rate=3000,
            image=get_dummy_image(),
            specs={'battery_life': '30min'},
            available=True,
            featured_item=True
        )

        # Test category filter
        url = reverse('rental-item-list')
        response = self.client.get(url, {'category': 'professional'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

        # Test price range filter
        response = self.client.get(url, {'min_rate': 2000, 'max_rate': 2800})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        # Test search
        response = self.client.get(url, {'search': 'Camera'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_unauthorized_access(self):
        # Test unauthorized create
        self.client.force_authenticate(user=None)
        url = reverse('rental-item-list')
        data = self.rental_item_data.copy()
        data['image'] = get_dummy_image()
        data['specs'] = json.dumps(data['specs'])
        response = self.client.post(url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Test unauthorized update
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('rental-item-detail', args=[self.rental_item.id])
        update_data = {
            'name': 'Updated Camera Name',
            'description': 'Updated description',
            'daily_rate': 3000,
            'available': False
        }
        response = self.client.patch(url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

class RatingTests(APITestCase):
    def setUp(self):
        # Create test users
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            email='other@example.com',
            password='testpass123'
        )
        
        # Create test rental item
        self.rental_item = RentalItem.objects.create(
            user=self.user,
            name='Professional 4K Camera',
            type='camera',
            category='professional',
            description='High-end 4K camera with accessories',
            daily_rate=2500,
            image=get_dummy_image(),
            specs={'resolution': '4K'},
            available=True
        )
        
        self.client.force_authenticate(user=self.user)

    def test_create_rating(self):
        url = reverse('rating-list')
        data = {
            'item_id': str(self.rental_item.id),
            'rating': 5,
            'comment': 'Excellent rental item!'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Rating.objects.count(), 1)
        self.assertEqual(response.data['rating'], 5)
        self.assertEqual(response.data['comment'], 'Excellent rental item!')
        self.assertEqual(response.data['item_id'], str(self.rental_item.id))

    def test_get_ratings_list(self):
        # Create some ratings
        Rating.objects.create(
            item_id=self.rental_item.id,
            user=self.user,
            rating=5,
            comment='Great item!'
        )
        Rating.objects.create(
            item_id=self.rental_item.id,
            user=self.other_user,
            rating=4,
            comment='Good condition'
        )
        
        url = reverse('rating-list')
        
        # Test without filters
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        
        # Test filter by item_id
        response = self.client.get(url, {'item_id': str(self.rental_item.id)})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        
        # Test filter by user_id
        response = self.client.get(url, {'user_id': str(self.user.id)})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_get_rating_detail(self):
        rating = Rating.objects.create(
            item_id=self.rental_item.id,
            user=self.user,
            rating=5,
            comment='Excellent rental item!'
        )
        
        url = reverse('rating-detail', args=[rating.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['rating'], 5)
        self.assertEqual(response.data['comment'], 'Excellent rental item!')
        self.assertEqual(response.data['item_id'], str(self.rental_item.id))

    def test_delete_rating(self):
        rating = Rating.objects.create(
            item_id=self.rental_item.id,
            user=self.user,
            rating=5,
            comment='Excellent rental item!'
        )
        
        url = reverse('rating-detail', args=[rating.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Rating.objects.count(), 0)

    def test_cannot_rate_twice(self):
        # Create initial rating
        Rating.objects.create(
            item_id=self.rental_item.id,
            user=self.user,
            rating=5,
            comment='First rating'
        )
        
        # Try to create another rating
        url = reverse('rating-list')
        data = {
            'item_id': str(self.rental_item.id),
            'rating': 4,
            'comment': 'Second rating'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Rating.objects.count(), 1)

    def test_invalid_rating_value(self):
        url = reverse('rating-list')
        data = {
            'item_id': str(self.rental_item.id),
            'rating': 6,  # Invalid rating value
            'comment': 'Invalid rating'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Rating.objects.count(), 0)

    def test_nonexistent_item(self):
        url = reverse('rating-list')
        data = {
            'item_id': '00000000-0000-0000-0000-000000000000',  # Non-existent UUID
            'rating': 5,
            'comment': 'Test comment'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(Rating.objects.count(), 0)
