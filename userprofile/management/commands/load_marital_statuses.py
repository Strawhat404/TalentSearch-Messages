from .base_load_choices import BaseLoadChoicesCommand
from userprofile.models import MaritalStatusChoices

class Command(BaseLoadChoicesCommand):
    help = 'Load marital status choices from JSON file'

    def handle(self, *args, **options):
        data = self.load_json_file('marital_status.json')
        if not data:
            return

        # Get or create MaritalStatusChoices instance
        marital_status_choices, created = MaritalStatusChoices.objects.get_or_create()
        
        # Update the fields with data from JSON
        marital_status_choices.choices = data.get('marital_statuses', [])
        marital_status_choices.save()
        
        if created:
            self.stdout.write(self.style.SUCCESS('Successfully created and populated MaritalStatusChoices'))
        else:
            self.stdout.write(self.style.SUCCESS('Successfully updated MaritalStatusChoices')) 