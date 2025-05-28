from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import csv

class Command(BaseCommand):
    help = 'Create users in bulk from users.csv'

    def handle(self, *args, **kwargs):
        User = get_user_model()
        with open('users.csv') as f:
            reader = csv.DictReader(f)
            for row in reader:
                email = row['email']
                password = row['password']
                if not User.objects.filter(email=email).exists():
                    User.objects.create_user(email=email, password=password)
                    self.stdout.write(self.style.SUCCESS(f'Created user: {email}'))
                else:
                    self.stdout.write(self.style.WARNING(f'User already exists: {email}'))
