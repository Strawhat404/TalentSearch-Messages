from .base_load_choices import BaseLoadChoicesCommand
from userprofile.models import GenderChoices

class Command(BaseLoadChoicesCommand):
    help = 'Load gender choices from JSON file'

    def handle(self, *args, **options):
        data = self.load_json_file('genders.json')
        if not data:
            return

        # Get or create GenderChoices instance
        gender_choices, created = GenderChoices.objects.get_or_create()
        
        # Update the fields with data from JSON
        gender_choices.choices = data.get('genders', [])
        gender_choices.save()
        
        if created:
            self.stdout.write(self.style.SUCCESS('Successfully created and populated GenderChoices'))
        else:
            self.stdout.write(self.style.SUCCESS('Successfully updated GenderChoices')) 