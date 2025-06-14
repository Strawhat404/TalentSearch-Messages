from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command

class Command(BaseCommand):
    help = 'Fake the problematic adverts migration'

    def handle(self, *args, **options):
        try:
            call_command('migrate', 'adverts', '0002', fake=True)  # Replace 0002 with your migration number
            self.stdout.write(self.style.SUCCESS('Successfully faked adverts migration'))
        except Exception as e:
            raise CommandError(f'Error faking migration: {e}')
