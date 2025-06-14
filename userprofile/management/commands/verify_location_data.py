from django.core.management.base import BaseCommand
from userprofile.models import LocationData

class Command(BaseCommand):
    help = 'Verify location data in the database'

    def handle(self, *args, **options):
        # Get all location data
        locations = LocationData.objects.all()
        
        if not locations.exists():
            self.stdout.write(self.style.ERROR('No location data found in the database'))
            return

        self.stdout.write(self.style.SUCCESS('Found location data:'))
        
        for location in locations:
            self.stdout.write(f"\nRegion: {location.region_name} (ID: {location.region_id})")
            self.stdout.write("Cities:")
            for city in location.cities:
                self.stdout.write(f"  - {city['name']} (ID: {city['id']})") 