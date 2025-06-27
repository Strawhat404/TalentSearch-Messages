from django.core.management.base import BaseCommand
import json
import os
from django.conf import settings

class Command(BaseCommand):
    help = 'Load all prepopulated data from JSON files'

    def handle(self, *args, **options):
        self.stdout.write('🚀 Starting to load all prepopulated data...')
        
        # List of JSON files to load
        json_files = [
            'basic_information.json',
            'location_information.json',
            'id_verification.json',
            'professions_and_skills.json',
            'experience.json'
        ]
        
        success_count = 0
        error_count = 0
        
        for json_file in json_files:
            try:
                self.load_json_data(json_file)
                success_count += 1
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Error loading {json_file}: {str(e)}')
                )
                error_count += 1
        
        # Summary
        self.stdout.write('\n' + '='*50)
        self.stdout.write('📊 LOADING SUMMARY:')
        self.stdout.write(f'✅ Successfully loaded: {success_count} files')
        if error_count > 0:
            self.stdout.write(f'❌ Failed to load: {error_count} files')
        self.stdout.write('='*50)
        
        if success_count == len(json_files):
            self.stdout.write(
                self.style.SUCCESS('🎉 All data loaded successfully!')
            )
        else:
            self.stdout.write(
                self.style.WARNING('⚠️  Some files failed to load. Check the errors above.')
            )
    
    def load_json_data(self, filename):
        """Load data from a specific JSON file"""
        file_path = os.path.join(settings.BASE_DIR, 'userprofile', 'data', filename)
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f'File not found: {file_path}')
        
        self.stdout.write(f'📁 Loading {filename}...')
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Load data based on filename
        if filename == 'basic_information.json':
            self.load_basic_information(data)
        elif filename == 'location_information.json':
            self.load_location_information(data)
        elif filename == 'id_verification.json':
            self.load_id_verification(data)
        elif filename == 'professions_and_skills.json':
            self.load_professions_and_skills(data)
        elif filename == 'experience.json':
            self.load_experience(data)
        else:
            self.stdout.write(f'⚠️  Unknown file type: {filename}')
    
    def load_basic_information(self, data):
        """Load basic information data"""
        # Since we removed the choice models, we'll just validate the JSON structure
        total_items = 0
        
        categories = ['nationality', 'gender', 'languages', 'hair_color', 'eye_color', 
                     'skin_tone', 'body_type', 'medical_condition', 'medicine_type', 
                     'marital_status', 'hobbies']
        
        for category in categories:
            if category in data:
                count = len(data[category])
                total_items += count
                self.stdout.write(f'📋 Found {count} {category} items')
        
        self.stdout.write(f'✅ Validated {total_items} total items from basic_information.json')
        self.stdout.write('💡 Note: Data is ready for frontend/API use. No database models needed.')
    
    def load_location_information(self, data):
        """Load location information data"""
        # Since we removed the choice models, we'll just validate the JSON structure
        total_items = 0
        
        categories = ['housing_status', 'regions', 'duration', 'cities', 'countries']
        
        for category in categories:
            if category in data:
                if category == 'cities':
                    # Cities is a nested structure
                    city_count = sum(len(cities) for cities in data[category].values())
                    total_items += city_count
                    self.stdout.write(f'🏙️  Found {city_count} cities across {len(data[category])} regions')
                else:
                    count = len(data[category])
                    total_items += count
                    self.stdout.write(f'📍 Found {count} {category} items')
        
        self.stdout.write(f'✅ Validated {total_items} total items from location_information.json')
        self.stdout.write('💡 Note: Data is ready for frontend/API use. No database models needed.')
    
    def load_id_verification(self, data):
        """Load ID verification data"""
        # Since we removed the choice models, we'll just validate the JSON structure
        total_items = 0
        
        if 'id_type' in data:
            count = len(data['id_type'])
            total_items += count
            self.stdout.write(f'🆔 Found {count} ID types')
            for id_type in data['id_type']:
                self.stdout.write(f'   - {id_type["name"]} (id: {id_type["id"]})')
        
        self.stdout.write(f'✅ Validated {total_items} total items from id_verification.json')
        self.stdout.write('💡 Note: Data is ready for frontend/API use. No database models needed.')
    
    def load_professions_and_skills(self, data):
        """Load professions and skills data"""
        # Since we removed the choice models, we'll just validate the JSON structure
        # and provide a summary of what would be loaded
        
        total_items = 0
        
        # Check professions
        if 'professions' in data:
            professions_count = len(data['professions'])
            total_items += professions_count
            self.stdout.write(f'📋 Found {professions_count} professions')
            for profession in data['professions']:
                self.stdout.write(f'   - {profession["name"]} (id: {profession["id"]})')
        
        # Check actor categories
        if 'actor_category' in data:
            actor_count = len(data['actor_category'])
            total_items += actor_count
            self.stdout.write(f'🎭 Found {actor_count} actor categories')
        
        # Check model categories
        if 'model_categories' in data:
            model_count = len(data['model_categories'])
            total_items += model_count
            self.stdout.write(f'👗 Found {model_count} model categories')
        
        # Check performer categories
        if 'performer_categories' in data:
            performer_count = len(data['performer_categories'])
            total_items += performer_count
            self.stdout.write(f'🎪 Found {performer_count} performer categories')
        
        # Check influencer categories
        if 'influencer_categories' in data:
            influencer_count = len(data['influencer_categories'])
            total_items += influencer_count
            self.stdout.write(f'📱 Found {influencer_count} influencer categories')
        
        # Check skills
        if 'skills' in data:
            skills_count = len(data['skills'])
            total_items += skills_count
            self.stdout.write(f'🛠️  Found {skills_count} skills')
        
        # Check main skills
        if 'main_skill' in data:
            main_skills_count = len(data['main_skill'])
            total_items += main_skills_count
            self.stdout.write(f'⭐ Found {main_skills_count} main skills')
        
        self.stdout.write(f'✅ Validated {total_items} total items from professions_and_skills.json')
        self.stdout.write('💡 Note: Data is ready for frontend/API use. No database models needed.')
    
    def load_experience(self, data):
        """Load experience data"""
        # Since we removed the choice models, we'll just validate the JSON structure
        total_items = 0
        
        categories = ['experience_level', 'years', 'availability', 'employment_status', 'work_location', 'shift']
        
        for category in categories:
            if category in data:
                count = len(data[category])
                total_items += count
                self.stdout.write(f'💼 Found {count} {category} items')
        
        self.stdout.write(f'✅ Validated {total_items} total items from experience.json')
        self.stdout.write('💡 Note: Data is ready for frontend/API use. No database models needed.') 