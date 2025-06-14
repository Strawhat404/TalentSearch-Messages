from .base_load_choices import BaseLoadChoicesCommand
from userprofile.models import EducationInstitutionChoices

class Command(BaseLoadChoicesCommand):
    help = 'Load education institution choices from JSON file'

    def handle(self, *args, **options):
        data = self.load_json_file('education_institutions.json')
        if not data:
            return

        # Get or create EducationInstitutionChoices instance
        education_institution_choices, created = EducationInstitutionChoices.objects.get_or_create()
        
        # Update the fields with data from JSON
        education_institution_choices.choices = data.get('education_institutions', [])
        education_institution_choices.save()
        
        if created:
            self.stdout.write(self.style.SUCCESS('Successfully created and populated EducationInstitutionChoices'))
        else:
            self.stdout.write(self.style.SUCCESS('Successfully updated EducationInstitutionChoices')) 