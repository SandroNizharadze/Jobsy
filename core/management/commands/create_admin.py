from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import UserProfile

class Command(BaseCommand):
    help = 'Creates a superuser for the admin interface'

    def handle(self, *args, **options):
        username = 'admin'
        email = 'admin@example.com'
        password = 'admin123'
        
        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING(f'User {username} already exists'))
            user = User.objects.get(username=username)
            user.is_staff = True
            user.is_superuser = True
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f'Updated superuser {username}'))
        else:
            User.objects.create_superuser(username=username, email=email, password=password)
            self.stdout.write(self.style.SUCCESS(f'Created superuser {username}'))
        
        # Create UserProfile if it doesn't exist
        user = User.objects.get(username=username)
        UserProfile.objects.get_or_create(
            user=user,
            defaults={'role': 'admin'}
        )
        self.stdout.write(self.style.SUCCESS(f'Ensured UserProfile exists for {username}')) 