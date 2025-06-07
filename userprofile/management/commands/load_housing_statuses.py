from .base_load_choices import BaseLoadChoicesCommand
from userprofile.models import HousingStatusChoices

class Command(BaseLoadChoicesCommand):
    help = 'Load housing status choices from JSON file'

    def handle(self, *args, **options):
        data = self.load_json_file('housing_status.json')
        if not data:
            return

        # Get or create HousingStatusChoices instance
        housing_status_choices, created = HousingStatusChoices.objects.get_or_create()
        
        # Update the fields with data from JSON
        housing_status_choices.choices = data.get('housing_statuses', [])
        housing_status_choices.save()
        
        if created:
            self.stdout.write(self.style.SUCCESS('Successfully created and populated HousingStatusChoices'))
        else:
            self.stdout.write(self.style.SUCCESS('Successfully updated HousingStatusChoices')) 