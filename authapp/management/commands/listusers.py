from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'List all users'

    def handle(self, *args, **options):
        User = get_user_model()
        for user in User.objects.all():
            self.stdout.write(f"{user.email} | staff: {user.is_staff} | superuser: {user.is_superuser}")
