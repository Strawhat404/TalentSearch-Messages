from .base_load_choices import BaseLoadChoicesCommand
from userprofile.models import RegionChoices

class Command(BaseLoadChoicesCommand):
    help = 'Load region choices from JSON file'

    def handle(self, *args, **options):
        data = self.load_json_file('regions.json')
        if not data:
            return

        # Get or create RegionChoices instance
        region_choices, created = RegionChoices.objects.get_or_create()
        
        # Update the fields with data from JSON
        region_choices.choices = data.get('regions', [])
        region_choices.save()
        
        if created:
            self.stdout.write(self.style.SUCCESS('Successfully created and populated RegionChoices'))
        else:
            self.stdout.write(self.style.SUCCESS('Successfully updated RegionChoices')) 