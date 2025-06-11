from .base_load_choices import BaseLoadChoicesCommand
from userprofile.models import PhysicalAttributeChoices

class Command(BaseLoadChoicesCommand):
    help = 'Load physical attribute choices from JSON file'

    def handle(self, *args, **options):
        data = self.load_json_file('physical_attributes.json')
        if not data:
            return

        # Get or create PhysicalAttributeChoices instance
        physical_choices, created = PhysicalAttributeChoices.objects.get_or_create()
        
        # Update the fields with data from JSON
        physical_choices.hair_colors = data.get('hair_colors', [])
        physical_choices.eye_colors = data.get('eye_colors', [])
        physical_choices.skin_tones = data.get('skin_tones', [])
        physical_choices.body_types = data.get('body_types', [])
        physical_choices.save()
        
        if created:
            self.stdout.write(self.style.SUCCESS('Successfully created and populated PhysicalAttributeChoices'))
        else:
            self.stdout.write(self.style.SUCCESS('Successfully updated PhysicalAttributeChoices')) 