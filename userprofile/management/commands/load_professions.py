from .base_load_choices import BaseLoadChoicesCommand
from userprofile.models import ProfessionChoices

class Command(BaseLoadChoicesCommand):
    help = 'Load profession choices from JSON file'

    def handle(self, *args, **options):
        data = self.load_json_file('professions.json')
        if not data:
            return

        # Get or create ProfessionChoices instance
        profession_choices, created = ProfessionChoices.objects.get_or_create()
        
        # Update the fields with data from JSON
        profession_choices.choices = data.get('professions', [])
        profession_choices.save()
        
        if created:
            self.stdout.write(self.style.SUCCESS('Successfully created and populated ProfessionChoices'))
        else:
            self.stdout.write(self.style.SUCCESS('Successfully updated ProfessionChoices')) 