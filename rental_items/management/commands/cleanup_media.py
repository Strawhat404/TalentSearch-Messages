from django.core.management.base import BaseCommand
from django.db.models import Q
from rental_items.models import RentalItem, RentalItemImage
import os
import shutil

class Command(BaseCommand):
    help = 'Cleans up old media files that are no longer referenced in the database'

    def handle(self, *args, **options):
        # Get all rental items and their images from the database
        rental_items = RentalItem.objects.all()
        rental_item_images = RentalItemImage.objects.all()

        # Get all valid image paths from the database
        valid_paths = set()
        valid_rental_item_ids = set()
        
        # Add main images and track valid rental item IDs
        for item in rental_items:
            valid_rental_item_ids.add(str(item.id))
            if item.image:
                valid_paths.add(item.image.path)
        
        # Add additional images
        for image in rental_item_images:
            if image.image:
                valid_paths.add(image.image.path)
                valid_rental_item_ids.add(str(image.rental_item.id))

        # Clean up main images directory
        main_dir = 'media/rental_items/main'
        if os.path.exists(main_dir):
            for filename in os.listdir(main_dir):
                file_path = os.path.join(main_dir, filename)
                if os.path.isfile(file_path) and file_path not in valid_paths:
                    try:
                        os.remove(file_path)
                        self.stdout.write(f'Deleted: {file_path}')
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'Error deleting {file_path}: {e}'))

        # Clean up additional images directory
        additional_dir = 'media/rental_items/additional'
        if os.path.exists(additional_dir):
            # First, remove any directories for non-existent rental items
            for item_dir in os.listdir(additional_dir):
                item_path = os.path.join(additional_dir, item_dir)
                if os.path.isdir(item_path):
                    if item_dir not in valid_rental_item_ids:
                        try:
                            shutil.rmtree(item_path)
                            self.stdout.write(f'Deleted directory for non-existent rental item: {item_path}')
                        except Exception as e:
                            self.stdout.write(self.style.ERROR(f'Error deleting directory {item_path}: {e}'))
                    else:
                        # For existing rental items, clean up unreferenced images
                        for filename in os.listdir(item_path):
                            file_path = os.path.join(item_path, filename)
                            if os.path.isfile(file_path) and file_path not in valid_paths:
                                try:
                                    os.remove(file_path)
                                    self.stdout.write(f'Deleted unreferenced image: {file_path}')
                                except Exception as e:
                                    self.stdout.write(self.style.ERROR(f'Error deleting {file_path}: {e}'))

        # Remove empty directories
        for root, dirs, files in os.walk('media/rental_items', topdown=False):
            for dir_name in dirs:
                dir_path = os.path.join(root, dir_name)
                if not os.listdir(dir_path):
                    try:
                        os.rmdir(dir_path)
                        self.stdout.write(f'Removed empty directory: {dir_path}')
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'Error removing directory {dir_path}: {e}'))

        self.stdout.write(self.style.SUCCESS('Media cleanup completed')) 