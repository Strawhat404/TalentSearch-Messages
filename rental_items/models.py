from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import FileExtensionValidator, MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from django.db.models.signals import pre_save, post_delete
from django.dispatch import receiver
from django.core.files.storage import default_storage
import uuid
import os
import json
import shutil

User = get_user_model()

def delete_file_if_exists(file_path):
    """Helper function to safely delete a file if it exists"""
    if file_path and os.path.isfile(file_path):
        try:
            os.remove(file_path)
            # Try to remove the parent directory if it's empty
            parent_dir = os.path.dirname(file_path)
            if os.path.exists(parent_dir) and not os.listdir(parent_dir):
                os.rmdir(parent_dir)
        except Exception as e:
            print(f"Error deleting file {file_path}: {e}")

def rental_item_image_path(instance, filename):
    """Generate path for rental item additional images"""
    return f'rental_items/additional/{instance.rental_item.id}/{filename}'

class RentalItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=255)
    category = models.CharField(max_length=255)
    description = models.TextField()
    daily_rate = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif'])],
        help_text='Main image for the rental item'
    )
    specs = models.JSONField(help_text="Technical specifications of the item")
    available = models.BooleanField(default=True)
    featured_item = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rental_items')
    approved = models.BooleanField(default=False)
    additional_images = models.JSONField(
        default=list,
        help_text='List of additional image paths'
    )
    location = models.CharField(max_length=255, blank=True)
    tags = models.JSONField(default=list, help_text="Searchable tags")
    rating_count = models.IntegerField(default=0)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    rating_distribution = models.JSONField(default=dict, help_text="Rating distribution (1-5 stars)")

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def delete(self, *args, **kwargs):
        # Delete the main image file
        if self.image:
            delete_file_if_exists(self.image.path)
        
        # Delete all additional images
        for image in self.images.all():
            if image.image:
                delete_file_if_exists(image.image.path)
            image.delete()
        
        super().delete(*args, **kwargs)

    def update_rating_stats(self):
        """Update rating statistics when ratings change"""
        ratings = self.ratings.all()
        self.rating_count = ratings.count()
        
        if self.rating_count > 0:
            self.average_rating = sum(r.rating for r in ratings) / self.rating_count
            
            # Calculate rating distribution
            distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
            for rating in ratings:
                distribution[rating.rating] += 1
            
            # Convert to percentages
            for key in distribution:
                distribution[key] = (distribution[key] / self.rating_count) * 100
                
            self.rating_distribution = distribution
        else:
            self.average_rating = 0.00
            self.rating_distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        
        self.save(update_fields=['rating_count', 'average_rating', 'rating_distribution'])

@receiver(pre_save, sender=RentalItem)
def delete_old_image(sender, instance, **kwargs):
    if not instance.pk:  # Skip for new instances
        return
    
    try:
        old_instance = RentalItem.objects.get(pk=instance.pk)
        if old_instance.image and old_instance.image != instance.image:
            delete_file_if_exists(old_instance.image.path)
    except RentalItem.DoesNotExist:
        pass

@receiver(post_delete, sender=RentalItem)
def cleanup_rental_item_files(sender, instance, **kwargs):
    """Clean up any remaining files after rental item deletion"""
    if instance.image:
        delete_file_if_exists(instance.image.path)
    
    # Clean up additional images directory
    additional_images_dir = os.path.join('media', 'rental_items', 'additional', str(instance.id))
    if os.path.exists(additional_images_dir):
        try:
            shutil.rmtree(additional_images_dir)
        except Exception as e:
            print(f"Error deleting directory {additional_images_dir}: {e}")

class RentalItemImage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    rental_item = models.ForeignKey(RentalItem, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(
        upload_to='media/rental_items/main/',
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif'])],
        help_text='Additional image for the rental item'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Image for {self.rental_item.name}"

@receiver(pre_save, sender=RentalItemImage)
def delete_old_additional_image(sender, instance, **kwargs):
    if not instance.pk:  # Skip for new instances
        return
    
    try:
        old_instance = RentalItemImage.objects.get(pk=instance.pk)
        if old_instance.image and old_instance.image != instance.image:
            if default_storage.exists(old_instance.image.name):
                default_storage.delete(old_instance.image.name)
                # Try to remove the parent directory if it's empty
                parent_dir = os.path.dirname(old_instance.image.path)
                if os.path.exists(parent_dir) and not os.listdir(parent_dir):
                    try:
                        os.rmdir(parent_dir)
                    except Exception as e:
                        print(f"Error removing directory {parent_dir}: {e}")
    except RentalItemImage.DoesNotExist:
        pass

class RentalItemRating(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    rental_item = models.ForeignKey(RentalItem, related_name="ratings", on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rental_item_ratings')
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rating value from 1 to 5"
    )
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['rental_item', 'user']

    def __str__(self):
        return f"{self.user.email}'s rating for {self.rental_item.name}"

class Wishlist(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wishlist_items')
    rental_item = models.ForeignKey(RentalItem, on_delete=models.CASCADE, related_name='wishlisted_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['user', 'rental_item']

    def __str__(self):
        return f"{self.user.email}'s wishlist item: {self.rental_item.name}"
