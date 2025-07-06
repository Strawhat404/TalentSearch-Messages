from django.core.management.base import BaseCommand
from feed_posts.models import UserFollow
from userprofile.models import Profile

class Command(BaseCommand):
    help = "Remove orphaned UserFollow records"

    def handle(self, *args, **kwargs):
        before = UserFollow.objects.count()
        UserFollow.objects.exclude(follower_id__in=Profile.objects.values_list('id', flat=True)).delete()
        UserFollow.objects.exclude(following_id__in=Profile.objects.values_list('id', flat=True)).delete()
        after = UserFollow.objects.count()
        self.stdout.write(self.style.SUCCESS(f"Cleaned up orphaned UserFollow records: {before - after} removed."))
