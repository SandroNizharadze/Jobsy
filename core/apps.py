from django.apps import AppConfig

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        # Import signals
        import core.signals
        
        # Import here to avoid circular imports
        from django.contrib.auth.models import User
        from .models import UserProfile
        import os
        
        # Only run this when the actual server is running (not during migrations or other management commands)
        if os.environ.get('RUN_MAIN', None) != 'true' and not os.environ.get('DISABLE_ADMIN_CREATION'):
            # Create admin user if it doesn't exist
            try:
                admin_username = 'admin'
                admin_email = 'admin@example.com'
                admin_password = 'admin123'
                
                # Create or update the admin user
                try:
                    admin_user = User.objects.get(username=admin_username)
                    admin_user.is_staff = True
                    admin_user.is_superuser = True
                    admin_user.set_password(admin_password)
                    admin_user.save()
                    print(f"Admin user '{admin_username}' updated.")
                except User.DoesNotExist:
                    User.objects.create_superuser(
                        username=admin_username,
                        email=admin_email,
                        password=admin_password
                    )
                    print(f"Admin user '{admin_username}' created.")
                
                # Ensure UserProfile exists
                admin_user = User.objects.get(username=admin_username)
                UserProfile.objects.get_or_create(
                    user=admin_user,
                    defaults={'role': 'admin'}
                )
                print(f"UserProfile for '{admin_username}' ensured.")
            except Exception as e:
                print(f"Error creating admin user: {e}")