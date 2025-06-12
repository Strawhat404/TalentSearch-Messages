from .base_load_choices import BaseLoadChoicesCommand
from userprofile.models import NationalityChoices

class Command(BaseLoadChoicesCommand):
    help = 'Load nationality choices from JSON file'

    def handle(self, *args, **options):
        data = self.load_json_file('nationalities.json')
        if not data:
            return

        # Get or create NationalityChoices instance
        nationality_choices, created = NationalityChoices.objects.get_or_create()
        
        # Update the fields with data from JSON
        nationality_choices.choices = data.get('nationalities', [])
        nationality_choices.save()
        
        if created:
            self.stdout.write(self.style.SUCCESS('Successfully created and populated NationalityChoices'))
        else:
            self.stdout.write(self.style.SUCCESS('Successfully updated NationalityChoices')) 