import json
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from userprofile.models import Choices

class Command(BaseCommand):
    help = 'Load all choices data from JSON file'

    def handle(self, *args, **options):
        json_file_path = os.path.join(settings.BASE_DIR, 'userprofile', 'data', 'choices.json')
        
        try:
            with open(json_file_path, 'r') as file:
                data = json.load(file)
                
            for choice_data in data['choices_data']:
                # Get or create choice instance
                choice, created = Choices.objects.get_or_create(
                    category=choice_data['category'],
                    subcategory=choice_data['subcategory'],
                    defaults={'choices': choice_data['choices']}
                )
                
                if not created:
                    # Update choices if the record already exists
                    choice.choices = choice_data['choices']
                    choice.save()
                
                status = 'Created' if created else 'Updated'
                self.stdout.write(
                    self.style.SUCCESS(
                        f'{status} choices for {choice.category}/{choice.subcategory}'
                    )
                )
                
        except FileNotFoundError:
            self.stdout.write(
                self.style.ERROR(f'Could not find file: {json_file_path}')
            )
        except json.JSONDecodeError:
            self.stdout.write(
                self.style.ERROR('Invalid JSON file')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'An error occurred: {str(e)}')
            ) 