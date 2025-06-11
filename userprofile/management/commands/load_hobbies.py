from .base_load_choices import BaseLoadChoicesCommand
from userprofile.models import HobbyChoices

class Command(BaseLoadChoicesCommand):
    help = 'Load hobby choices from JSON file'

    def handle(self, *args, **options):
        data = self.load_json_file('hobbies.json')
        if not data:
            return

        # Get or create HobbyChoices instance
        hobby_choices, created = HobbyChoices.objects.get_or_create()
        
        # Update the fields with data from JSON
        hobby_choices.choices = data.get('hobbies', [])
        hobby_choices.save()
        
        if created:
            self.stdout.write(self.style.SUCCESS('Successfully created and populated HobbyChoices'))
        else:
            self.stdout.write(self.style.SUCCESS('Successfully updated HobbyChoices')) 