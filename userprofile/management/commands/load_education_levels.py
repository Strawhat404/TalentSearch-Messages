from .base_load_choices import BaseLoadChoicesCommand
from userprofile.models import EducationLevelChoices

class Command(BaseLoadChoicesCommand):
    help = 'Load education level choices from JSON file'

    def handle(self, *args, **options):
        data = self.load_json_file('education_levels.json')
        if not data:
            return

        # Get or create EducationLevelChoices instance
        education_level_choices, created = EducationLevelChoices.objects.get_or_create()
        
        # Update the fields with data from JSON
        education_level_choices.choices = data.get('education_levels', [])
        education_level_choices.save()
        
        if created:
            self.stdout.write(self.style.SUCCESS('Successfully created and populated EducationLevelChoices'))
        else:
            self.stdout.write(self.style.SUCCESS('Successfully updated EducationLevelChoices')) 