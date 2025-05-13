from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Create a default superuser'

    def handle(self, *args, **kwargs):
        if not User.objects.filter(username='admin').exists():
            user = User.objects.create_superuser('admin', 'admin@gmail.com', 'aquabill123')
            user.is_active = True  # Mark user as active (verified)
            user.save()
            self.stdout.write(self.style.SUCCESS('Default superuser created and verified.'))
        else:
            self.stdout.write('Superuser already exists.')
