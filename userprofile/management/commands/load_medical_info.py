from .base_load_choices import BaseLoadChoicesCommand
from userprofile.models import MedicalInfoChoices

class Command(BaseLoadChoicesCommand):
    help = 'Load medical information choices from JSON file'

    def handle(self, *args, **options):
        data = self.load_json_file('medical_info.json')
        if not data:
            return

        # Get or create MedicalInfoChoices instance
        medical_choices, created = MedicalInfoChoices.objects.get_or_create()
        
        # Update the fields with data from JSON
        medical_choices.medical_conditions = data.get('medical_conditions', [])
        medical_choices.medicine_types = data.get('medicine_types', [])
        medical_choices.save()
        
        if created:
            self.stdout.write(self.style.SUCCESS('Successfully created and populated MedicalInfoChoices'))
        else:
            self.stdout.write(self.style.SUCCESS('Successfully updated MedicalInfoChoices')) 