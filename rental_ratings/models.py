from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Avg, Count
from django.utils import timezone
import uuid

User = get_user_model()

class Rating(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    item_id = models.UUIDField(help_text="ID of the rental item being rated")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rental_ratings')
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rating value from 1 to 5"
    )
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Additional fields for better filtering
    is_verified_purchase = models.BooleanField(default=False, help_text="Whether this rating is from a verified purchase")
    helpful_votes = models.IntegerField(default=0, help_text="Number of users who found this review helpful")
    reported = models.BooleanField(default=False, help_text="Whether this rating has been reported")
    is_edited = models.BooleanField(default=False, help_text="Whether this rating has been edited")

    class Meta:
        ordering = ['-created_at']
        unique_together = ['item_id', 'user']
        indexes = [
            models.Index(fields=['item_id', 'rating']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['rating', 'created_at']),
            models.Index(fields=['is_verified_purchase', 'rating']),
        ]

    def __str__(self):
        return f"{self.user.email}'s rating for item {self.item_id}"

    @classmethod
    def get_item_rating_stats(cls, item_id):
        """Get comprehensive rating statistics for an item"""
        ratings = cls.objects.filter(item_id=item_id)
        
        if not ratings.exists():
            return {
                'average_rating': 0,
                'total_ratings': 0,
                'rating_distribution': {1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
                'verified_ratings': 0,
                'recent_ratings': 0
            }
        
        # Calculate basic stats
        total_ratings = ratings.count()
        average_rating = ratings.aggregate(avg=Avg('rating'))['avg']
        
        # Calculate rating distribution
        distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for rating in ratings.values_list('rating', flat=True):
            distribution[rating] += 1
        
        # Convert to percentages
        for key in distribution:
            distribution[key] = (distribution[key] / total_ratings) * 100
        
        # Additional stats
        verified_ratings = ratings.filter(is_verified_purchase=True).count()
        recent_ratings = ratings.filter(created_at__gte=timezone.now() - timezone.timedelta(days=30)).count()
        
        return {
            'average_rating': round(average_rating, 2),
            'total_ratings': total_ratings,
            'rating_distribution': distribution,
            'verified_ratings': verified_ratings,
            'recent_ratings': recent_ratings
        }

    @classmethod
    def get_user_rating_stats(cls, user_id):
        """Get rating statistics for a user"""
        ratings = cls.objects.filter(user_id=user_id)
        
        if not ratings.exists():
            return {
                'total_ratings': 0,
                'average_rating_given': 0,
                'rating_distribution': {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
            }
        
        total_ratings = ratings.count()
        average_rating = ratings.aggregate(avg=Avg('rating'))['avg']
        
        # Calculate rating distribution
        distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for rating in ratings.values_list('rating', flat=True):
            distribution[rating] += 1
        
        return {
            'total_ratings': total_ratings,
            'average_rating_given': round(average_rating, 2),
            'rating_distribution': distribution
        }
