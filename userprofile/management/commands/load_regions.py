from django.core.management.base import BaseCommand
from userprofile.models import LocationData
import json
import os
from django.conf import settings

class Command(BaseCommand):
    help = 'Load location data from JSON files'

    def load_json_file(self, filename):
        try:
            with open(os.path.join(settings.BASE_DIR, 'userprofile', 'data', filename), 'r') as f:
                return json.load(f)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error loading {filename}: {str(e)}'))
            return None

    def handle(self, *args, **options):
        # Load regions data
        regions_data = self.load_json_file('regions.json')
        if not regions_data:
            return

        # Load locations data
        locations_data = self.load_json_file('locations.json')
        if not locations_data:
            return

        # Create LocationData entries
        for location in locations_data.get('locations', []):
            region_id = location.get('region_id')
            region_name = location.get('region_name')
            cities = location.get('cities', [])

            # Create or update LocationData
            location_data, created = LocationData.objects.get_or_create(
                region_id=region_id,
                defaults={
                    'region_name': region_name,
                    'cities': cities
                }
            )

            if not created:
                location_data.region_name = region_name
                location_data.cities = cities
                location_data.save()

            if created:
                self.stdout.write(self.style.SUCCESS(f'Successfully created location data for {region_name}'))
            else:
                self.stdout.write(self.style.SUCCESS(f'Successfully updated location data for {region_name}')) 