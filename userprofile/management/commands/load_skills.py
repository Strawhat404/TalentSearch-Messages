from .base_load_choices import BaseLoadChoicesCommand
from userprofile.models import SkillsChoices

class Command(BaseLoadChoicesCommand):
    help = 'Load skills choices from JSON file'

    def handle(self, *args, **options):
        data = self.load_json_file('skills.json')
        if not data:
            return

        # Get or create SkillsChoices instance
        skills_choices, created = SkillsChoices.objects.get_or_create()
        
        # Update the fields with data from JSON
        skills_choices.choices = data.get('skills', [])
        skills_choices.save()
        
        if created:
            self.stdout.write(self.style.SUCCESS('Successfully created and populated SkillsChoices'))
        else:
            self.stdout.write(self.style.SUCCESS('Successfully updated SkillsChoices')) 