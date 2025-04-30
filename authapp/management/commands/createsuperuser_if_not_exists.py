from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Creates a superuser if none exists'

    def handle(self, *args, **options):
        if not User.objects.filter(is_superuser=True).exists():
            User.objects.create_superuser(
                username='admin',
                email='kingzaljaguar@gmail.com.com',
                password='admin' 
            )
            self.stdout.write(self.style.SUCCESS('Superuser created successfully'))
        else:
            self.stdout.write(self.style.WARNING('Superuser already exists'))