from django.core.management.base import BaseCommand
from django.db import connection
from django.db.utils import OperationalError
import os
from django.conf import settings

class Command(BaseCommand):
    help = 'Test database connection and show configuration details'

    def handle(self, *args, **options):
        self.stdout.write("=== Database Connection Test ===")
        
        # Show environment variables
        self.stdout.write(f"DATABASE_URL set: {bool(os.environ.get('DATABASE_URL'))}")
        if os.environ.get('DATABASE_URL'):
            # Show first few characters of DATABASE_URL for debugging
            db_url = os.environ.get('DATABASE_URL')
            self.stdout.write(f"DATABASE_URL preview: {db_url[:50]}...")
        
        # Show current database configuration
        self.stdout.write(f"Database engine: {settings.DATABASES['default']['ENGINE']}")
        if 'NAME' in settings.DATABASES['default']:
            self.stdout.write(f"Database name: {settings.DATABASES['default']['NAME']}")
        if 'HOST' in settings.DATABASES['default']:
            self.stdout.write(f"Database host: {settings.DATABASES['default']['HOST']}")
        if 'PORT' in settings.DATABASES['default']:
            self.stdout.write(f"Database port: {settings.DATABASES['default']['PORT']}")
        if 'USER' in settings.DATABASES['default']:
            self.stdout.write(f"Database user: {settings.DATABASES['default']['USER']}")
        
        # Test connection
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                self.stdout.write(
                    self.style.SUCCESS(f"Database connection successful! Test query result: {result}")
                )
        except OperationalError as e:
            self.stdout.write(
                self.style.ERROR(f"Database connection failed: {e}")
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Unexpected error: {e}")
            ) 