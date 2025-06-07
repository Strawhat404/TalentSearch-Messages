import json
import os
from django.core.management.base import BaseCommand
from django.conf import settings

class BaseLoadChoicesCommand(BaseCommand):
    help = 'Base command for loading choices from JSON files'

    def load_json_file(self, filename):
        json_file_path = os.path.join(settings.BASE_DIR, 'userprofile', 'data', filename)
        try:
            with open(json_file_path, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'Could not find file: {json_file_path}'))
            return None
        except json.JSONDecodeError:
            self.stdout.write(self.style.ERROR(f'Invalid JSON file: {filename}'))
            return None
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'An error occurred: {str(e)}'))
            return None 