from django.core.management.base import BaseCommand
from django.core.files.storage import default_storage
from django.conf import settings
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Migrate existing local media files to Cloudinary'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be migrated without actually doing it',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force migration even if Cloudinary is not configured',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force = options['force']
        
        # Check if Cloudinary is configured
        if not hasattr(settings, 'CLOUDINARY_STORAGE') or not settings.CLOUDINARY_STORAGE.get('CLOUD_NAME'):
            if not force:
                self.stdout.write(
                    self.style.ERROR('Cloudinary is not configured. Set CLOUD_NAME, API_KEY, and API_SECRET in your environment variables.')
                )
                return
            else:
                self.stdout.write(
                    self.style.WARNING('Cloudinary not configured, but proceeding with --force flag')
                )

        # Check if we're using Cloudinary storage
        if not isinstance(default_storage, type(settings.CLOUDINARY_STORAGE)):
            self.stdout.write(
                self.style.WARNING('Not using Cloudinary storage. Current storage: {}'.format(type(default_storage)))
            )

        # Get the media root directory
        media_root = getattr(settings, 'MEDIA_ROOT', None)
        if not media_root or not os.path.exists(media_root):
            self.stdout.write(
                self.style.WARNING('No local media directory found or it does not exist.')
            )
            return

        self.stdout.write(f'Scanning media directory: {media_root}')
        
        # Find all media files
        media_files = []
        for root, dirs, files in os.walk(media_root):
            for file in files:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, media_root)
                media_files.append((file_path, relative_path))

        if not media_files:
            self.stdout.write(self.style.SUCCESS('No media files found to migrate.'))
            return

        self.stdout.write(f'Found {len(media_files)} files to migrate.')

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - No files will be actually migrated'))
            for file_path, relative_path in media_files:
                self.stdout.write(f'Would migrate: {relative_path}')
            return

        # Migrate files
        migrated_count = 0
        failed_count = 0

        for file_path, relative_path in media_files:
            try:
                with open(file_path, 'rb') as f:
                    # Upload to Cloudinary
                    cloudinary_path = default_storage.save(relative_path, f)
                    migrated_count += 1
                    self.stdout.write(f'Migrated: {relative_path} -> {cloudinary_path}')
                    
                    # Optionally delete local file after successful upload
                    # os.remove(file_path)
                    # self.stdout.write(f'Deleted local file: {file_path}')
                    
            except Exception as e:
                failed_count += 1
                self.stdout.write(
                    self.style.ERROR(f'Failed to migrate {relative_path}: {str(e)}')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'Migration completed. Successfully migrated: {migrated_count}, Failed: {failed_count}'
            )
        )

        if failed_count > 0:
            self.stdout.write(
                self.style.WARNING(
                    'Some files failed to migrate. Check the error messages above.'
                )
            ) 