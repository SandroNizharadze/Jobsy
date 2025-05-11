from django.db.models.signals import post_save, post_migrate
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'userprofile'):
        instance.userprofile.save()

# Ensure admin user/profile exists after migrations
@receiver(post_migrate)
def ensure_admin_user(sender, **kwargs):
    from django.contrib.auth.models import User
    from .models import UserProfile
    import os
    admin_username = 'admin'
    admin_email = 'admin@example.com'
    admin_password = 'admin123'
    try:
        admin_user, created = User.objects.get_or_create(
            username=admin_username,
            defaults={
                'email': admin_email,
                'is_staff': True,
                'is_superuser': True
            }
        )
        if created:
            admin_user.set_password(admin_password)
            admin_user.save()
            print(f"Admin user '{admin_username}' created.")
        else:
            # Update existing user to ensure they have admin privileges
            admin_user.is_staff = True
            admin_user.is_superuser = True
            admin_user.set_password(admin_password)
            admin_user.save()
            print(f"Admin user '{admin_username}' updated.")
        # Ensure UserProfile exists
        UserProfile.objects.get_or_create(
            user=admin_user,
            defaults={'role': 'admin'}
        )
        print(f"UserProfile for '{admin_username}' ensured.")
    except Exception as e:
        print(f"Error creating admin user: {e}")