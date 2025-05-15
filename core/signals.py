from django.db.models.signals import post_save, post_migrate
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Create a UserProfile for a User if it doesn't already exist.
    This signal is a safety net for any user creation that doesn't explicitly
    create a UserProfile. The registration view should handle profile creation directly.
    """
    if created:
        # Use get_or_create to be absolutely sure we don't create duplicates
        try:
            # First check if a profile already exists to avoid transaction conflicts
            if UserProfile.objects.filter(user=instance).exists():
                logger.info(f"Signal: UserProfile already exists for {instance.username}, not creating a new one")
                return
                
            # Create a default profile if none exists
            profile, created = UserProfile.objects.get_or_create(
                user=instance,
                defaults={'role': 'candidate'}
            )
            if created:
                logger.info(f"Signal: Created default UserProfile for new user {instance.username}")
            else:
                logger.info(f"Signal: Found existing UserProfile for {instance.username}")
        except Exception as e:
            logger.error(f"Signal: Error creating UserProfile: {str(e)}")
            # Don't raise the exception - we don't want to break user creation
            # if profile creation fails

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Save the UserProfile when the User is saved.
    """
    if hasattr(instance, 'userprofile'):
        logger.info(f"Signal: Saving existing UserProfile for {instance.username} with role {instance.userprofile.role}")
        instance.userprofile.save()
    else:
        logger.warning(f"Signal: User {instance.username} has no UserProfile, this is unexpected")

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