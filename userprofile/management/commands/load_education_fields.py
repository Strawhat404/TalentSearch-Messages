from .base_load_choices import BaseLoadChoicesCommand
from userprofile.models import EducationFieldChoices

class Command(BaseLoadChoicesCommand):
    help = 'Load education field choices from JSON file'

    def handle(self, *args, **options):
        data = self.load_json_file('education_fields.json')
        if not data:
            return

        # Get or create EducationFieldChoices instance
        education_field_choices, created = EducationFieldChoices.objects.get_or_create()
        
        # Update the fields with data from JSON
        education_field_choices.choices = data.get('education_fields', [])
        education_field_choices.save()
        
        if created:
            self.stdout.write(self.style.SUCCESS('Successfully created and populated EducationFieldChoices'))
        else:
            self.stdout.write(self.style.SUCCESS('Successfully updated EducationFieldChoices')) 