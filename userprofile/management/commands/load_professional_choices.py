import json
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from userprofile.models import ProfessionalChoices

class Command(BaseCommand):
    help = 'Load professional choices data from JSON file'

    def handle(self, *args, **options):
        json_file_path = os.path.join(settings.BASE_DIR, 'userprofile', 'data', 'professional_choices.json')
        
        try:
            with open(json_file_path, 'r') as file:
                data = json.load(file)
                
            # Get or create ProfessionalChoices instance
            professional_choices, created = ProfessionalChoices.objects.get_or_create()
            
            # Update the fields with data from JSON
            professional_choices.company_sizes = data.get('company_sizes', [])
            professional_choices.industries = data.get('industries', [])
            professional_choices.leadership_styles = data.get('leadership_styles', [])
            professional_choices.communication_styles = data.get('communication_styles', [])
            professional_choices.motivations = data.get('motivations', [])
            
            professional_choices.save()
            
            if created:
                self.stdout.write(self.style.SUCCESS('Successfully created and populated ProfessionalChoices'))
            else:
                self.stdout.write(self.style.SUCCESS('Successfully updated ProfessionalChoices'))
                
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'Could not find file: {json_file_path}'))
        except json.JSONDecodeError:
            self.stdout.write(self.style.ERROR('Invalid JSON file'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'An error occurred: {str(e)}')) 