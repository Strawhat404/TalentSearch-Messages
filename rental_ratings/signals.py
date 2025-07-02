from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Rating
from rental_items.models import RentalItem

@receiver([post_save, post_delete], sender=Rating)
def update_rental_item_rating_stats(sender, instance, **kwargs):
    """Update rental item rating statistics when ratings change"""
    try:
        # Update the rental item's rating statistics
        rental_item = RentalItem.objects.get(id=instance.item_id)
        
        # Calculate new statistics
        ratings = Rating.objects.filter(item_id=instance.item_id)
        total_ratings = ratings.count()
        
        if total_ratings > 0:
            # Calculate average rating
            total_rating_sum = sum(r.rating for r in ratings)
            average_rating = total_rating_sum / total_ratings
            
            # Calculate rating distribution
            distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
            for rating in ratings:
                distribution[rating.rating] += 1
            
            # Convert to percentages
            for key in distribution:
                distribution[key] = (distribution[key] / total_ratings) * 100
        else:
            average_rating = 0
            distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        
        # Update rental item fields (if they exist)
        if hasattr(rental_item, 'rating_count'):
            rental_item.rating_count = total_ratings
        if hasattr(rental_item, 'average_rating'):
            rental_item.average_rating = average_rating
        if hasattr(rental_item, 'rating_distribution'):
            rental_item.rating_distribution = distribution
        
        rental_item.save(update_fields=['rating_count', 'average_rating', 'rating_distribution'])
        
    except RentalItem.DoesNotExist:
        # Rental item doesn't exist, skip update
        pass
    except Exception as e:
        # Log error but don't fail
        print(f"Error updating rating stats: {e}") 