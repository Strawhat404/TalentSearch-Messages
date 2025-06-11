from .base_load_choices import BaseLoadChoicesCommand
from userprofile.models import EducationStatusChoices

class Command(BaseLoadChoicesCommand):
    help = 'Load education status choices from JSON file'

    def handle(self, *args, **options):
        data = self.load_json_file('education_statuses.json')
        if not data:
            return

        # Get or create EducationStatusChoices instance
        education_status_choices, created = EducationStatusChoices.objects.get_or_create()
        
        # Update the fields with data from JSON
        education_status_choices.choices = data.get('education_statuses', [])
        education_status_choices.save()
        
        if created:
            self.stdout.write(self.style.SUCCESS('Successfully created and populated EducationStatusChoices'))
        else:
            self.stdout.write(self.style.SUCCESS('Successfully updated EducationStatusChoices')) 