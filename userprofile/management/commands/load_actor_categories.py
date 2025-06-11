from .base_load_choices import BaseLoadChoicesCommand
from userprofile.models import ActorCategoryChoices

class Command(BaseLoadChoicesCommand):
    help = 'Load actor category choices from JSON file'

    def handle(self, *args, **options):
        data = self.load_json_file('actor_categories.json')
        if not data:
            return

        # Get or create ActorCategoryChoices instance
        actor_category_choices, created = ActorCategoryChoices.objects.get_or_create()
        
        # Update the fields with data from JSON
        actor_category_choices.choices = data.get('actor_categories', [])
        actor_category_choices.save()
        
        if created:
            self.stdout.write(self.style.SUCCESS('Successfully created and populated ActorCategoryChoices'))
        else:
            self.stdout.write(self.style.SUCCESS('Successfully updated ActorCategoryChoices')) 