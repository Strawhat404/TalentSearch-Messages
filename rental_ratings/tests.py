from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import Rating
from rental_items.models import RentalItem
from django.core.files.uploadedfile import SimpleUploadedFile

User = get_user_model()

def get_dummy_image():
    return SimpleUploadedFile(
        name='test_image.jpg',
        content=b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b',
        content_type='image/jpeg'
    )

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
            'comment': 'Excellent rental item, worked perfectly!'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Rating.objects.count(), 1)
        self.assertEqual(response.data['rating'], 5)
        self.assertEqual(response.data['comment'], 'Excellent rental item, worked perfectly!')
        self.assertEqual(response.data['item_id'], str(self.rental_item.id))
        self.assertEqual(response.data['user_id'], str(self.user.id))

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
        
        # Test filter by min_rating
        response = self.client.get(url, {'min_rating': 5})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        
        # Test sort by highest
        response = self.client.get(url, {'sort': 'highest'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]['rating'], 5)
        
        # Test sort by lowest
        response = self.client.get(url, {'sort': 'lowest'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]['rating'], 4)

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
        self.assertEqual(response.data['user_id'], str(self.user.id))
        self.assertIn('user_profile', response.data)
        self.assertIn('item_details', response.data)

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
        self.assertEqual(response.data['message'], 'Rating deleted successfully.')

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
