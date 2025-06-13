from .base_load_choices import BaseLoadChoicesCommand
from userprofile.models import ExperienceLevelChoices

class Command(BaseLoadChoicesCommand):
    help = 'Load experience level choices from JSON file'

    def handle(self, *args, **options):
        data = self.load_json_file('experience_levels.json')
        if not data:
            return

        # Get or create ExperienceLevelChoices instance
        experience_level_choices, created = ExperienceLevelChoices.objects.get_or_create()
        
        # Update the fields with data from JSON
        experience_level_choices.choices = data.get('experience_levels', [])
        experience_level_choices.save()
        
        if created:
            self.stdout.write(self.style.SUCCESS('Successfully created and populated ExperienceLevelChoices'))
        else:
            self.stdout.write(self.style.SUCCESS('Successfully updated ExperienceLevelChoices')) 