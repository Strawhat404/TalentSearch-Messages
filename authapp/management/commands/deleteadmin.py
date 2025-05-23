from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Delete the admin user'

    def handle(self, *args, **options):
        User = get_user_model()
        email = 'admin@example.com'
        deleted, _ = User.objects.filter(email=email).delete()
        if deleted:
            self.stdout.write(self.style.SUCCESS('Admin user deleted!'))
        else:
            self.stdout.write(self.style.WARNING('No admin user found.'))
