from .base_load_choices import BaseLoadChoicesCommand
from userprofile.models import IDTypeChoices

class Command(BaseLoadChoicesCommand):
    help = 'Load ID type choices from JSON file'

    def handle(self, *args, **options):
        data = self.load_json_file('id_types.json')
        if not data:
            return

        # Get or create IDTypeChoices instance
        id_type_choices, created = IDTypeChoices.objects.get_or_create()
        
        # Update the fields with data from JSON
        id_type_choices.choices = data.get('id_types', [])
        id_type_choices.save()
        
        if created:
            self.stdout.write(self.style.SUCCESS('Successfully created and populated IDTypeChoices'))
        else:
            self.stdout.write(self.style.SUCCESS('Successfully updated IDTypeChoices')) 