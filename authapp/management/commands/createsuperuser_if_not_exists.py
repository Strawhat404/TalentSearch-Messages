from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Create an admin user if not exists'

    def handle(self, *args, **options):
        User = get_user_model()
        email = 'admin@example.com'
        password = 'Test1234!'
        if not User.objects.filter(email=email).exists():
            User.objects.create_superuser(email=email, password=password, name='Admin User')
            self.stdout.write(self.style.SUCCESS('Admin user created!'))
        else:
            self.stdout.write(self.style.WARNING('Admin user already exists.'))