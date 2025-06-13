# news/management/commands/migrate_media_to_cloudinary.py

from django.core.management.base import BaseCommand
from news.models import NewsImage
from cloudinary.uploader import upload
from cloudinary.exceptions import Error as CloudinaryError

class Command(BaseCommand):
    help = "Migrate existing news images to Cloudinary"

    def handle(self, *args, **kwargs):
        for img in NewsImage.objects.all():
            if img.image and not str(img.image).startswith("https://res.cloudinary.com/"):
                try:
                    result = upload(img.image.path, resource_type="image")
                    img.image = result['secure_url']
                    img.save()
                    self.stdout.write(self.style.SUCCESS(f"Migrated image for {img.id}"))
                except CloudinaryError as e:
                    self.stdout.write(self.style.ERROR(f"Failed image for {img.id}: {str(e)}"))
