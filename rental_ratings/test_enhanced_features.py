from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.utils import timezone
from datetime import timedelta
import uuid

from .models import Rating
from rental_items.models import RentalItem

User = get_user_model()

class EnhancedRatingModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.rental_item = RentalItem.objects.create(
            name='Test Camera',
            type='electronics',
            category='photography',
            description='Test camera for rental',
            daily_rate=50.00,
            user=self.user,
            specs={'resolution': '4K'}
        )

    def test_rating_creation_with_new_fields(self):
        """Test creating a rating with new enhanced fields"""
        rating = Rating.objects.create(
            item_id=self.rental_item.id,
            user=self.user,
            rating=5,
            comment='Excellent camera!',
            is_verified_purchase=True
        )
        
        self.assertEqual(rating.rating, 5)
        self.assertEqual(rating.is_verified_purchase, True)
        self.assertEqual(rating.helpful_votes, 0)
        self.assertEqual(rating.reported, False)
        self.assertEqual(rating.is_edited, False)
        self.assertIsNotNone(rating.created_at)
        self.assertIsNotNone(rating.updated_at)

    def test_get_item_rating_stats(self):
        """Test getting comprehensive rating statistics for an item"""
        # Create multiple ratings
        Rating.objects.create(
            item_id=self.rental_item.id,
            user=self.user,
            rating=5,
            comment='Great!'
        )
        
        another_user = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass123'
        )
        
        Rating.objects.create(
            item_id=self.rental_item.id,
            user=another_user,
            rating=4,
            comment='Good camera',
            is_verified_purchase=True
        )
        
        stats = Rating.get_item_rating_stats(self.rental_item.id)
        
        self.assertEqual(stats['total_ratings'], 2)
        self.assertEqual(stats['average_rating'], 4.5)
        self.assertEqual(stats['verified_ratings'], 1)
        self.assertEqual(stats['rating_distribution'][5], 50.0)
        self.assertEqual(stats['rating_distribution'][4], 50.0)

    def test_get_user_rating_stats(self):
        """Test getting rating statistics for a user"""
        # Create ratings by the user
        Rating.objects.create(
            item_id=self.rental_item.id,
            user=self.user,
            rating=5,
            comment='Great!'
        )
        
        another_item = RentalItem.objects.create(
            name='Test Lens',
            type='electronics',
            category='photography',
            description='Test lens for rental',
            daily_rate=30.00,
            user=self.user
        )
        
        Rating.objects.create(
            item_id=another_item.id,
            user=self.user,
            rating=4,
            comment='Good lens'
        )
        
        stats = Rating.get_user_rating_stats(self.user.id)
        
        self.assertEqual(stats['total_ratings'], 2)
        self.assertEqual(stats['average_rating_given'], 4.5)
        self.assertEqual(stats['rating_distribution'][5], 50.0)
        self.assertEqual(stats['rating_distribution'][4], 50.0)

    def test_rating_stats_empty(self):
        """Test rating statistics for items/users with no ratings"""
        stats = Rating.get_item_rating_stats(self.rental_item.id)
        
        self.assertEqual(stats['total_ratings'], 0)
        self.assertEqual(stats['average_rating'], 0)
        self.assertEqual(stats['verified_ratings'], 0)
        self.assertEqual(stats['recent_ratings'], 0)


class EnhancedRatingAPITests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        self.rental_item = RentalItem.objects.create(
            name='Test Camera',
            type='electronics',
            category='photography',
            description='Test camera for rental',
            daily_rate=50.00,
            user=self.user,
            specs={'resolution': '4K'}
        )
        
        # Create test ratings
        self.rating1 = Rating.objects.create(
            item_id=self.rental_item.id,
            user=self.user,
            rating=5,
            comment='Excellent camera!',
            is_verified_purchase=True
        )
        
        self.another_user = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass123'
        )
        
        self.rating2 = Rating.objects.create(
            item_id=self.rental_item.id,
            user=self.another_user,
            rating=4,
            comment='Good camera',
            is_verified_purchase=False
        )

    def test_list_ratings_with_filters(self):
        """Test listing ratings with various filters"""
        url = reverse('rating-list')
        
        # Test filtering by rating
        response = self.client.get(f'{url}?rating=5')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        
        # Test filtering by verified purchases
        response = self.client.get(f'{url}?is_verified_purchase=true')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        
        # Test filtering by item_id
        response = self.client.get(f'{url}?item_id={self.rental_item.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

    def test_advanced_search(self):
        """Test advanced search functionality"""
        url = reverse('rating-search_advanced')
        
        # Test text search
        response = self.client.get(f'{url}?q=excellent')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        
        # Test rating range filter
        response = self.client.get(f'{url}?min_rating=4&max_rating=5')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        
        # Test verified only filter
        response = self.client.get(f'{url}?verified_only=true')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_rating_statistics(self):
        """Test rating statistics endpoint"""
        url = reverse('rating-statistics')
        
        # Test item statistics
        response = self.client.get(f'{url}?item_id={self.rental_item.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_ratings'], 2)
        self.assertEqual(response.data['average_rating'], 4.5)
        
        # Test user statistics
        response = self.client.get(f'{url}?user_id={self.user.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_ratings'], 1)
        self.assertEqual(response.data['average_rating_given'], 5.0)
        
        # Test global statistics
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_ratings'], 2)

    def test_ratings_by_item(self):
        """Test getting ratings for a specific item"""
        url = reverse('rating-by_item')
        
        response = self.client.get(f'{url}?item_id={self.rental_item.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.assertIn('item_details', response.data)
        self.assertIn('statistics', response.data)
        self.assertIn('ratings', response.data)
        
        self.assertEqual(response.data['item_details']['name'], 'Test Camera')
        self.assertEqual(response.data['statistics']['total_ratings'], 2)

    def test_mark_helpful(self):
        """Test marking a rating as helpful"""
        url = reverse('rating-mark_helpful', kwargs={'pk': self.rating1.id})
        
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['helpful_votes'], 1)
        
        # Test that helpful_votes increased
        self.rating1.refresh_from_db()
        self.assertEqual(self.rating1.helpful_votes, 1)

    def test_report_rating(self):
        """Test reporting a rating"""
        url = reverse('rating-report', kwargs={'pk': self.rating1.id})
        
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test that reported flag is set
        self.rating1.refresh_from_db()
        self.assertEqual(self.rating1.reported, True)

    def test_sorting_options(self):
        """Test various sorting options"""
        url = reverse('rating-list')
        
        # Test sorting by helpful votes
        response = self.client.get(f'{url}?sort_by=helpful')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test sorting by rating high to low
        response = self.client.get(f'{url}?sort_by=rating_high')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test sorting by verified first
        response = self.client.get(f'{url}?sort_by=verified_first')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_date_range_filtering(self):
        """Test date range filtering"""
        url = reverse('rating-list')
        
        # Test recent only filter
        response = self.client.get(f'{url}?recent_only=true')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test date range in advanced search
        search_url = reverse('rating-search_advanced')
        response = self.client.get(f'{search_url}?date_range=month')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_rating_with_new_fields(self):
        """Test creating a rating with enhanced fields"""
        url = reverse('rating-list')
        data = {
            'item_id': str(self.rental_item.id),
            'rating': 5,
            'comment': 'Amazing camera!',
            'is_verified_purchase': True
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        rating = Rating.objects.get(id=response.data['id'])
        self.assertEqual(rating.is_verified_purchase, True)
        self.assertEqual(rating.helpful_votes, 0)
        self.assertEqual(rating.reported, False)

    def test_update_rating_marks_as_edited(self):
        """Test that updating a rating marks it as edited"""
        url = reverse('rating-detail', kwargs={'pk': self.rating1.id})
        data = {
            'rating': 4,
            'comment': 'Updated comment'
        }
        
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.rating1.refresh_from_db()
        self.assertEqual(self.rating1.is_edited, True)
        self.assertEqual(self.rating1.rating, 4)

    def test_validation_errors(self):
        """Test validation errors for rating creation"""
        url = reverse('rating-list')
        
        # Test invalid rating
        data = {
            'item_id': str(self.rental_item.id),
            'rating': 6,  # Invalid rating
            'comment': 'Test comment'
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test invalid item_id
        data = {
            'item_id': str(uuid.uuid4()),  # Non-existent item
            'rating': 5,
            'comment': 'Test comment'
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_duplicate_rating_prevention(self):
        """Test that users cannot rate the same item twice"""
        url = reverse('rating-list')
        data = {
            'item_id': str(self.rental_item.id),
            'rating': 3,
            'comment': 'Another rating'
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('already rated', response.data['detail'])

    def test_rating_serializer_includes_username(self):
        """Test that the rating serializer includes the username field"""
        from .serializers import RatingSerializer
        
        # Use the existing rating from setUp
        serializer = RatingSerializer(self.rating1)
        data = serializer.data
        
        # Check that username is included
        self.assertIn('username', data)
        self.assertEqual(data['username'], self.user.username)
        self.assertIn('user_profile', data)  # Ensure backward compatibility


class RatingPerformanceTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        # Create multiple rental items and ratings for performance testing
        self.rental_items = []
        self.ratings = []
        
        for i in range(10):
            item = RentalItem.objects.create(
                name=f'Camera {i}',
                type='electronics',
                category='photography',
                description=f'Test camera {i}',
                daily_rate=50.00 + i,
                user=self.user
            )
            self.rental_items.append(item)
            
            # Create multiple ratings for each item
            for j in range(5):
                rating = Rating.objects.create(
                    item_id=item.id,
                    user=self.user,
                    rating=3 + (j % 3),  # Ratings 3, 4, 5
                    comment=f'Rating {j} for camera {i}',
                    is_verified_purchase=(j % 2 == 0)
                )
                self.ratings.append(rating)

    def test_large_dataset_performance(self):
        """Test performance with large datasets"""
        url = reverse('rating-list')
        
        # Test listing all ratings
        start_time = timezone.now()
        response = self.client.get(url)
        end_time = timezone.now()
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 50)  # 10 items * 5 ratings
        
        # Performance should be reasonable (less than 1 second)
        duration = (end_time - start_time).total_seconds()
        self.assertLess(duration, 1.0)

    def test_complex_filtering_performance(self):
        """Test performance with complex filtering"""
        url = reverse('rating-search_advanced')
        
        start_time = timezone.now()
        response = self.client.get(f'{url}?min_rating=4&verified_only=true&date_range=month')
        end_time = timezone.now()
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Performance should be reasonable
        duration = (end_time - start_time).total_seconds()
        self.assertLess(duration, 1.0)

    def test_statistics_performance(self):
        """Test performance of statistics calculation"""
        url = reverse('rating-statistics')
        
        start_time = timezone.now()
        response = self.client.get(url)
        end_time = timezone.now()
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Performance should be reasonable
        duration = (end_time - start_time).total_seconds()
        self.assertLess(duration, 1.0) 