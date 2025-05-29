import json
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from userprofile.models import Profile, PhysicalAttributes, PersonalInfo, MedicalInfo

class Command(BaseCommand):
    help = 'Loads choice data from JSON files'

    def handle(self, *args, **kwargs):
        data_dir = os.path.join(settings.BASE_DIR, 'userprofile', 'data')
        
        # Load countries
        with open(os.path.join(data_dir, 'countries.json'), 'r') as f:
            countries_data = json.load(f)
            self.stdout.write(f"Loaded {len(countries_data['countries'])} countries")
        
        # Load languages
        with open(os.path.join(data_dir, 'languages.json'), 'r') as f:
            languages_data = json.load(f)
            self.stdout.write(f"Loaded {len(languages_data['languages'])} languages")
        
        # Load physical attributes
        with open(os.path.join(data_dir, 'physical_attributes.json'), 'r') as f:
            physical_data = json.load(f)
            self.stdout.write("Loaded physical attributes:")
            self.stdout.write(f"- {len(physical_data['hair_colors'])} hair colors")
            self.stdout.write(f"- {len(physical_data['eye_colors'])} eye colors")
            self.stdout.write(f"- {len(physical_data['skin_tones'])} skin tones")
            self.stdout.write(f"- {len(physical_data['body_types'])} body types")
            self.stdout.write(f"- {len(physical_data['genders'])} genders")
        
        # Load personal info
        with open(os.path.join(data_dir, 'personal_info.json'), 'r') as f:
            personal_data = json.load(f)
            self.stdout.write("Loaded personal info:")
            self.stdout.write(f"- {len(personal_data['marital_statuses'])} marital statuses")
            self.stdout.write(f"- {len(personal_data['hobbies'])} hobbies")
            self.stdout.write(f"- {len(personal_data['medical_conditions'])} medical conditions")
            self.stdout.write(f"- {len(personal_data['medicine_types'])} medicine types")
        
        self.stdout.write(self.style.SUCCESS('Successfully loaded all choice data')) 