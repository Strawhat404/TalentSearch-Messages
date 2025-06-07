from .base_load_choices import BaseLoadChoicesCommand
from userprofile.models import YearsChoices

class Command(BaseLoadChoicesCommand):
    help = 'Load years choices from JSON file'

    def handle(self, *args, **options):
        data = self.load_json_file('years.json')
        if not data:
            return

        # Get or create YearsChoices instance
        years_choices, created = YearsChoices.objects.get_or_create()
        
        # Update the fields with data from JSON
        years_choices.choices = data.get('years', [])
        years_choices.save()
        
        if created:
            self.stdout.write(self.style.SUCCESS('Successfully created and populated YearsChoices'))
        else:
            self.stdout.write(self.style.SUCCESS('Successfully updated YearsChoices')) 