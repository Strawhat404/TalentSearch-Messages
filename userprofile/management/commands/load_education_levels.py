from userprofile.management.commands.base_load_choices import BaseLoadChoicesCommand

class Command(BaseLoadChoicesCommand):
    help = 'Load education levels from JSON file'

    def handle(self, *args, **options):
        self.load_choices('education_levels.json', 'education_levels') 