from .base_load_choices import BaseLoadChoicesCommand
from userprofile.models import LanguageChoices

class Command(BaseLoadChoicesCommand):
    help = 'Load language choices from JSON file'

    def handle(self, *args, **options):
        data = self.load_json_file('languages.json')
        if not data:
            return

        # Get or create LanguageChoices instance
        language_choices, created = LanguageChoices.objects.get_or_create()
        
        # Update the fields with data from JSON
        language_choices.choices = data.get('languages', [])
        language_choices.save()
        
        if created:
            self.stdout.write(self.style.SUCCESS('Successfully created and populated LanguageChoices'))
        else:
            self.stdout.write(self.style.SUCCESS('Successfully updated LanguageChoices')) 