from django.core.management.base import BaseCommand
from userprofile.models import ChoiceData
import json
import os
from django.conf import settings

class Command(BaseCommand):
    help = 'Load all education-related data from JSON files'

    def handle(self, *args, **options):
        # Load education levels
        try:
            with open(os.path.join(settings.BASE_DIR, 'userprofile', 'data', 'education_levels.json'), 'r') as f:
                education_levels = json.load(f)
                ChoiceData.objects.update_or_create(
                    category='education_level',
                    defaults={'choices': education_levels['education_levels']}
                )
                self.stdout.write(self.style.SUCCESS('Successfully loaded education levels'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error loading education levels: {str(e)}'))

        # Load education fields
        try:
            with open(os.path.join(settings.BASE_DIR, 'userprofile', 'data', 'education_fields.json'), 'r') as f:
                education_fields = json.load(f)
                ChoiceData.objects.update_or_create(
                    category='education_field',
                    defaults={'choices': education_fields['education_fields']}
                )
                self.stdout.write(self.style.SUCCESS('Successfully loaded education fields'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error loading education fields: {str(e)}'))

        # Load education institutions
        try:
            with open(os.path.join(settings.BASE_DIR, 'userprofile', 'data', 'education_institutions.json'), 'r') as f:
                education_institutions = json.load(f)
                ChoiceData.objects.update_or_create(
                    category='education_institution',
                    defaults={'choices': education_institutions['education_institutions']}
                )
                self.stdout.write(self.style.SUCCESS('Successfully loaded education institutions'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error loading education institutions: {str(e)}')) 