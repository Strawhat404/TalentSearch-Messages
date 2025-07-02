from django.core.management.base import BaseCommand
from django.db import transaction
from rental_ratings.models import Rating
from rental_items.models import RentalItem
from django.db.models import Avg, Count
import time


class Command(BaseCommand):
    help = 'Update rating statistics for all rental items'

    def add_arguments(self, parser):
        parser.add_argument(
            '--item-id',
            type=str,
            help='Update statistics for a specific item ID only'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force update even if statistics are already calculated'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Number of items to process in each batch'
        )

    def handle(self, *args, **options):
        start_time = time.time()
        
        if options['item_id']:
            # Update specific item
            try:
                item = RentalItem.objects.get(id=options['item_id'])
                self.update_item_statistics(item)
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully updated statistics for item: {item.name}')
                )
            except RentalItem.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Item with ID {options["item_id"]} not found')
                )
        else:
            # Update all items
            items = RentalItem.objects.all()
            total_items = items.count()
            
            self.stdout.write(f'Starting to update statistics for {total_items} items...')
            
            updated_count = 0
            batch_size = options['batch_size']
            
            for i in range(0, total_items, batch_size):
                batch = items[i:i + batch_size]
                
                for item in batch:
                    try:
                        self.update_item_statistics(item)
                        updated_count += 1
                        
                        if updated_count % 10 == 0:
                            self.stdout.write(f'Processed {updated_count}/{total_items} items...')
                            
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f'Error updating item {item.id}: {str(e)}')
                        )
            
            end_time = time.time()
            duration = end_time - start_time
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully updated statistics for {updated_count}/{total_items} items in {duration:.2f} seconds'
                )
            )

    def update_item_statistics(self, item):
        """Update rating statistics for a specific item"""
        with transaction.atomic():
            # Get all ratings for this item
            ratings = Rating.objects.filter(item_id=item.id)
            total_ratings = ratings.count()
            
            if total_ratings > 0:
                # Calculate average rating
                average_rating = ratings.aggregate(avg=Avg('rating'))['avg']
                
                # Calculate rating distribution
                distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
                for rating in ratings.values_list('rating', flat=True):
                    distribution[rating] += 1
                
                # Convert to percentages
                for key in distribution:
                    distribution[key] = (distribution[key] / total_ratings) * 100
            else:
                average_rating = 0
                distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
            
            # Update item fields if they exist
            if hasattr(item, 'rating_count'):
                item.rating_count = total_ratings
            if hasattr(item, 'average_rating'):
                item.average_rating = average_rating
            if hasattr(item, 'rating_distribution'):
                item.rating_distribution = distribution
            
            item.save(update_fields=['rating_count', 'average_rating', 'rating_distribution']) 