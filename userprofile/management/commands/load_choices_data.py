import json
import os
from django.core.management.base import BaseCommand
from userprofile.models import LocationData, ChoiceData
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

    def get_data_dir(self):
        return os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')

    def load_json_file(self, filename):
        try:
            with open(os.path.join(self.get_data_dir(), filename), 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            self.stdout.write(self.style.WARNING(f'File not found: {filename}'))
            return None
        except json.JSONDecodeError:
            self.stdout.write(self.style.ERROR(f'Invalid JSON in file: {filename}'))
            return None

    @transaction.atomic
    def load_locations(self):
        self.stdout.write('Loading location data...')
        
        # Load data files
        regions_data = self.load_json_file('regions.json')
        cities_data = self.load_json_file('cities.json')
        
        if not regions_data or not cities_data:
            self.stdout.write(self.style.ERROR('Failed to load location data files'))
            return

        # Clear existing location data
        LocationData.objects.all().delete()

        # Create location data entries
        for region in regions_data['regions']:
            region_id = region['id']
            region_name = region['name']
            cities = cities_data['cities'].get(region_id, [])
            
            LocationData.objects.create(
                region_id=region_id,
                region_name=region_name,
                cities=cities
            )
        self.stdout.write(self.style.SUCCESS('Successfully loaded location data'))

    @transaction.atomic
    def load_choices(self):
        self.stdout.write('Loading choice data...')
        
        # Define all choice data files
        choice_files = {
            'languages': 'languages.json',
            'skills': 'skills.json',
            'education_levels': 'education_levels.json',
            'marital_status': 'marital_status.json',
            'personality_types': 'personality_types.json',
            'work_preferences': 'work_preferences.json',
            'company_cultures': 'company_cultures.json',
            'social_media_platforms': 'social_media_platforms.json',
            'tools': 'tools.json',
            'awards': 'awards.json',
            'model_categories': 'model_categories.json',
            'performer_categories': 'performer_categories.json',
            'influencer_categories': 'influencer_categories.json',
            'actor_categories': 'actor_categories.json'
        }

        # Clear existing choice data
        ChoiceData.objects.all().delete()

        # Load and create choice data entries
        for choice_type, filename in choice_files.items():
            data = self.load_json_file(filename)
            if data:
                ChoiceData.objects.create(
                    choice_type=choice_type,
                    choices=data.get(choice_type, [])
                )
                self.stdout.write(self.style.SUCCESS(f'Successfully loaded {choice_type} data'))

    def handle(self, *args, **options):
        data_type = options['type'].lower()
        force = options['force']

        # Check if data exists
        if not force:
            if data_type in ['all', 'locations'] and LocationData.objects.exists():
                self.stdout.write(self.style.WARNING('Location data already exists. Use --force to reload.'))
                return
            if data_type in ['all', 'choices'] and ChoiceData.objects.exists():
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
            for choice_type in ['model_categories', 'performer_categories', 'influencer_categories', 'actor_categories']:
                data = self.load_json_file(f'{choice_type}.json')
                if data:
                    self.stdout.write(f'\n{choice_type.replace("_", " ").title()}:')
                    for item in data.get(choice_type, []):
                        self.stdout.write(f"- {item['name']}: {item['description']}")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error loading data: {str(e)}')) 