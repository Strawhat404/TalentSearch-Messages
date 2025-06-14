from .base_load_choices import BaseLoadChoicesCommand
from userprofile.models import EducationTypeChoices

class Command(BaseLoadChoicesCommand):
    help = 'Load education type choices from JSON file'

    def handle(self, *args, **options):
        data = self.load_json_file('education_types.json')
        if not data:
            return

        # Get or create EducationTypeChoices instance
        education_type_choices, created = EducationTypeChoices.objects.get_or_create()
        
        # Update the fields with data from JSON
        education_type_choices.choices = data.get('education_types', [])
        education_type_choices.save()
        
        if created:
            self.stdout.write(self.style.SUCCESS('Successfully created and populated EducationTypeChoices'))
        else:
            self.stdout.write(self.style.SUCCESS('Successfully updated EducationTypeChoices')) 