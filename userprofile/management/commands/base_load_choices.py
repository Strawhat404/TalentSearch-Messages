from django.core.management.base import BaseCommand
from userprofile.models import ChoiceData
import json
import os
from django.conf import settings

class BaseLoadChoicesCommand(BaseCommand):
    help = 'Base command for loading choice data from JSON files'

    def load_choices(self, json_file, category):
        try:
            with open(os.path.join(settings.BASE_DIR, 'userprofile', 'data', json_file), 'r') as f:
                data = json.load(f)
                ChoiceData.objects.update_or_create(
                    category=category,
                    defaults={'choices': data[category]}
                )
                self.stdout.write(self.style.SUCCESS(f'Successfully loaded {category}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error loading {category}: {str(e)}'))

    def handle(self, *args, **options):
        raise NotImplementedError('Subclasses must implement handle()') 