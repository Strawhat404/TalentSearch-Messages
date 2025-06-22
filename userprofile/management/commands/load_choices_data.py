import json
import os
from django.core.management.base import BaseCommand
from userprofile.models import LocationData, Choices
from django.db import transaction
from django.conf import settings

class Command(BaseCommand):
    help = 'Load all choice data (locations, languages, etc.) from JSON files'

    def add_arguments(self, parser):
        parser.add_argument(
            '--type',
            type=str,
            help='Type of data to load (locations, choices, all)',
            default='all'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force reload even if data exists'
        )

    def load_json_file(self, filename):
        """Load JSON data from file."""
        filepath = os.path.join(settings.BASE_DIR, 'userprofile', 'data', filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                return json.load(file)
        except FileNotFoundError:
            return None
        except json.JSONDecodeError as e:
            self.stdout.write(f'Error parsing {filename}: {e}')
            return None

    def load_or_update_choice(self, category, subcategory, data):
        """Create or update a choice entry."""
        choice, created = Choices.objects.get_or_create(
            category=category,
            subcategory=subcategory,
            defaults={'choices': data}
        )
        if not created:
            choice.choices = data
            choice.save()
        return choice

    @transaction.atomic
    def load_locations(self):
        self.stdout.write('Loading location data...')
        
        # Load location information bundle
        location_data = self.load_json_file('location_information.json')
        
        if not location_data or 'location_information' not in location_data:
            self.stdout.write(self.style.ERROR('Failed to load location_information.json'))
            return

        location_info = location_data['location_information']
        regions_data = location_info.get('regions', [])
        cities_data = location_info.get('cities', {})

        # Clear existing location data
        LocationData.objects.all().delete()

        # Create location data entries
        for region in regions_data:
            region_id = region['id']
            region_name = region['name']
            cities = cities_data.get(region_id, [])
            
            LocationData.objects.create(
                region_id=region_id,
                region_name=region_name,
                cities=cities
            )
        self.stdout.write(self.style.SUCCESS('Successfully loaded location data from location_information bundle'))

    @transaction.atomic
    def load_choices(self):
        self.stdout.write('Loading choice data...')
        
        # Load basic information bundle
        basic_info_data = self.load_json_file('basic_information.json')
        
        # Load location information bundle
        location_info_data = self.load_json_file('location_information.json')
        
        # Load ID verification bundle
        id_verification_data = self.load_json_file('id_verification.json')
        
        # Load professions & skills bundle
        professions_skills_data = self.load_json_file('professions_skills.json')
        
        # Define all choice data files
        choice_files = {
            'education_levels': 'education_levels.json',
            'personality_types': 'personality_types.json',
            'work_preferences': 'work_preferences.json',
            'company_cultures': 'company_cultures.json',
            'social_media_platforms': 'social_media_platforms.json',
            'tools': 'tools.json',
            'awards': 'awards.json',
        }

        # Load bundle data
        if basic_info_data and 'basic_information' in basic_info_data:
            bundle = basic_info_data['basic_information']
            for subcategory, data in bundle.items():
                self.load_or_update_choice('basic_information', subcategory, data)
                self.stdout.write(f'Successfully loaded {subcategory} data from basic_information bundle')

        if location_info_data and 'location_information' in location_info_data:
            bundle = location_info_data['location_information']
            for subcategory, data in bundle.items():
                self.load_or_update_choice('location_information', subcategory, data)
                self.stdout.write(f'Successfully loaded {subcategory} data from location_information bundle')

        if id_verification_data and 'id_verification' in id_verification_data:
            bundle = id_verification_data['id_verification']
            for subcategory, data in bundle.items():
                self.load_or_update_choice('id_verification', subcategory, data)
                self.stdout.write(f'Successfully loaded {subcategory} data from id_verification bundle')

        if professions_skills_data and 'professions_skills' in professions_skills_data:
            bundle = professions_skills_data['professions_skills']
            for subcategory, data in bundle.items():
                self.load_or_update_choice('professions_skills', subcategory, data)
                self.stdout.write(f'Successfully loaded {subcategory} data from professions_skills bundle')

        # Load individual files
        for choice_type, filename in choice_files.items():
            data = self.load_json_file(filename)
            if data:
                # Handle both formats: {choice_type: [...]} and direct [...]
                if choice_type in data:
                    self.load_or_update_choice('general', choice_type, data[choice_type])
                elif isinstance(data, list):
                    self.load_or_update_choice('general', choice_type, data)
                else:
                    # Handle direct object with choices
                    self.load_or_update_choice('general', choice_type, data)
                self.stdout.write(f'Successfully loaded {choice_type} data')
            else:
                self.stdout.write(f'File not found: {filename}')

    def handle(self, *args, **options):
        data_type = options['type'].lower()
        force = options['force']

        # Check if data exists
        if not force:
            if data_type in ['all', 'locations'] and LocationData.objects.exists():
                self.stdout.write(self.style.WARNING('Location data already exists. Use --force to reload.'))
                return
            if data_type in ['all', 'choices'] and Choices.objects.exists():
                self.stdout.write(self.style.WARNING('Choice data already exists. Use --force to reload.'))
                return

        try:
            if data_type == 'all':
                self.load_locations()
                self.load_choices()
            elif data_type == 'locations':
                self.load_locations()
            elif data_type == 'choices':
                self.load_choices()
            else:
                self.stdout.write(self.style.ERROR(f'Invalid data type: {data_type}'))
                self.stdout.write('Available types: all, locations, choices')

            # Print verification of loaded data
            self.stdout.write('\nLoaded Categories:')
            
            # Show professions & skills categories from bundle
            professions_data = self.load_json_file('professions_skills.json')
            if professions_data and 'professions_skills' in professions_data:
                bundle = professions_data['professions_skills']
                
                for category_type in ['model_categories', 'performer_categories', 'influencer_categories', 'actor_categories']:
                    if category_type in bundle:
                        self.stdout.write(f'\n{category_type.replace("_", " ").title()}:')
                        for item in bundle[category_type]:
                            if isinstance(item, dict) and 'name' in item and 'description' in item:
                                self.stdout.write(f'- {item["name"]}: {item["description"]}')
                            
            # Check for any remaining individual files
            for choice_type in ['actor_categories']:
                data = self.load_json_file(f'{choice_type}.json')
                if data:
                    self.stdout.write(f'\n{choice_type.replace("_", " ").title()}:')
                    for item in data.get(choice_type, []):
                        if isinstance(item, dict) and 'name' in item and 'description' in item:
                            self.stdout.write(f'- {item["name"]}: {item["description"]}')
                else:
                    self.stdout.write(f'File not found: {choice_type}.json')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error loading data: {str(e)}')) 