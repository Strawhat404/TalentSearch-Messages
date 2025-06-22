from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Drop rental_items tables to reset migration state'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            # Drop tables in correct order (respecting foreign keys)
            cursor.execute("DROP TABLE IF EXISTS rental_items_rentalitemimage CASCADE;")
            cursor.execute("DROP TABLE IF EXISTS rental_items_rentalitemrating CASCADE;")
            cursor.execute("DROP TABLE IF EXISTS rental_items_rentalitem CASCADE;")
            
            # Also remove migration records
            cursor.execute("DELETE FROM django_migrations WHERE app = 'rental_items';")
            
        self.stdout.write(
            self.style.SUCCESS('Successfully dropped rental_items tables')
        ) 