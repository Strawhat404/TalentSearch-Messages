from django.db import models
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError
import os
from PIL import Image
import mimetypes


class GalleryItem(models.Model):
    """
    Model representing a gallery item (image or video) associated with a user profile.

    Attributes:
        profile_id (ForeignKey): Reference to the Profile model, linked via the user's profile.
        item_url (FileField): Uploaded file (image or video) stored in the media directory.
        item_type (CharField): Type of item, either 'image' or 'video'.
        description (TextField): Description of the gallery item.
        created_at (DateTimeField): Timestamp of item creation.
        updated_at (DateTimeField): Timestamp of the last update.
    """
    profile_id = models.ForeignKey('userprofile.Profile', on_delete=models.CASCADE, related_name='gallery_items')
    item_url = models.FileField(
        upload_to='gallery/',
        null=True,
        blank=True,
        validators=[
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif', 'mp4', 'avi', 'mov', 'mkv'])],
        max_length=255
    )
    item_type = models.CharField(max_length=10, choices=[('image', 'image'), ('video', 'video')])
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        """
        Validate the content of the uploaded file to ensure it's a valid image or video.
        """
        if self.item_url:
            ext = os.path.splitext(self.item_url.name)[1].lower()
            valid_image_extensions = ['.jpg', '.jpeg', '.png', '.gif']
            valid_video_extensions = ['.mp4', '.avi', '.mov', '.mkv']

            if ext in valid_image_extensions:
                try:
                    with Image.open(self.item_url) as img:
                        img.verify()  # Verify it's a valid image
                except Exception as e:
                    raise ValidationError({
                        'item_url': f"Invalid image file: {str(e)}"
                    })
            elif ext in valid_video_extensions:
                mime_type, _ = mimetypes.guess_type(self.item_url.name)
                if not mime_type or not mime_type.startswith('video/'):
                    raise ValidationError({
                        'item_url': "File must be a valid video (e.g., mp4, avi, mov, mkv)."
                    })

    def save(self, *args, **kwargs):
        """
        Override save method to automatically set item_type based on file extension
        and sanitize the description field.

        Raises:
            ValueError: If item_url is provided but its extension doesn't match allowed处处

        """
        import bleach

        if self.description:
            # Sanitize description to prevent XSS
            allowed_tags = ['p', 'br', 'strong', 'em', 'ul', 'li', 'a']
            self.description = bleach.clean(
                self.description,
                tags=allowed_tags,
                strip=True
            )

        if self.item_url:
            ext = os.path.splitext(self.item_url.name)[1].lower()
            if ext in ['.jpg', '.jpeg', '.png', '.gif']:
                self.item_type = 'image'
            elif ext in ['.mp4', '.avi', '.mov', '.mkv']:
                self.item_type = 'video'
            else:
                raise ValueError("Invalid file extension. Must be .jpg, .jpeg, .png, .gif, .mp4, .avi, .mov, or .mkv.")

        super().save(*args, **kwargs)

    def __str__(self):
        """
        Return a string representation of the gallery item.

        Returns:
            str: A description including item type and description.
        """
        return f"{self.item_type} - {self.description}"