import os
from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    help = 'Check environment variables and S3 configuration'

    def handle(self, *args, **options):
        # Check environment variables
        self.stdout.write(self.style.SUCCESS('=== Environment Variables ==='))
        env_vars = [
            'USE_S3',
            'AWS_ACCESS_KEY_ID',
            'AWS_SECRET_ACCESS_KEY',
            'AWS_STORAGE_BUCKET_NAME',
            'AWS_S3_REGION_NAME',
            'DEBUG'
        ]
        
        for var in env_vars:
            value = os.environ.get(var)
            if var in ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY'] and value:
                value = value[:4] + '****'  # Mask sensitive info
            self.stdout.write(f"{var}: {value}")
        
        # Check Django settings
        self.stdout.write(self.style.SUCCESS('\n=== Django Settings ==='))
        settings_vars = [
            'USE_S3',
            'AWS_ACCESS_KEY_ID',
            'AWS_SECRET_ACCESS_KEY',
            'AWS_STORAGE_BUCKET_NAME',
            'AWS_S3_REGION_NAME',
            'MEDIA_URL',
            'MEDIA_ROOT',
            'DEFAULT_FILE_STORAGE',
            'STATICFILES_STORAGE'
        ]
        
        for var in settings_vars:
            if hasattr(settings, var):
                value = getattr(settings, var)
                if var in ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY'] and value:
                    value = value[:4] + '****'  # Mask sensitive info
                self.stdout.write(f"{var}: {value}")
            else:
                self.stdout.write(self.style.WARNING(f"{var}: Not set in Django settings"))
        
        # Check storage backend for UserProfile.cv field
        self.stdout.write(self.style.SUCCESS('\n=== Storage Configuration ==='))
        try:
            from core.models import UserProfile
            profile_model = UserProfile
            cv_field = profile_model._meta.get_field('cv')
            
            # Check if field has storage attribute
            if hasattr(cv_field, 'storage'):
                storage = cv_field.storage
                self.stdout.write(f"CV field storage class: {storage.__class__.__name__}")
                
                if hasattr(storage, 'bucket_name'):
                    self.stdout.write(f"Storage bucket: {storage.bucket_name}")
                
                if hasattr(storage, 'location'):
                    self.stdout.write(f"Storage location: {storage.location}")
                
                # Check storage backend methods
                self.stdout.write("\nTesting storage backend:")
                try:
                    # Create a test file to test storage
                    import tempfile
                    from django.core.files.base import ContentFile
                    
                    test_content = ContentFile(b"Test file content for S3 check")
                    test_path = "test_s3_check.txt"
                    
                    # Try to save the file
                    saved_name = storage.save(test_path, test_content)
                    self.stdout.write(self.style.SUCCESS(f"File saved as: {saved_name}"))
                    
                    # Check if file exists
                    if storage.exists(saved_name):
                        self.stdout.write(self.style.SUCCESS(f"File exists in storage"))
                        
                        # Get file URL
                        url = storage.url(saved_name)
                        self.stdout.write(f"File URL: {url}")
                        
                        # Get file size
                        size = storage.size(saved_name)
                        self.stdout.write(f"File size: {size} bytes")
                        
                        # Delete the test file
                        storage.delete(saved_name)
                        self.stdout.write("Test file deleted")
                    else:
                        self.stdout.write(self.style.ERROR(f"File does not exist in storage after save!"))
                        
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error testing storage: {str(e)}"))
            else:
                self.stdout.write(self.style.ERROR("CV field does not have storage attribute"))
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error checking storage configuration: {str(e)}"))
            
        # Check wsgi.py for environment variable loading
        self.stdout.write(self.style.SUCCESS('\n=== WSGI Configuration ==='))
        wsgi_path = os.path.join(settings.BASE_DIR, 'jobsy', 'wsgi.py')
        if os.path.exists(wsgi_path):
            with open(wsgi_path, 'r') as f:
                content = f.read()
                if 'environ.get' in content or 'environ[' in content or 'load_dotenv' in content:
                    self.stdout.write(self.style.SUCCESS("Environment variables are being loaded in wsgi.py"))
                else:
                    self.stdout.write(self.style.WARNING("No environment variable loading found in wsgi.py"))
        else:
            self.stdout.write(self.style.ERROR(f"WSGI file not found at {wsgi_path}"))
            
        # Summary
        self.stdout.write(self.style.SUCCESS('\n=== Summary ==='))
        if hasattr(settings, 'USE_S3') and settings.USE_S3:
            self.stdout.write(self.style.SUCCESS("S3 storage is ENABLED in Django settings"))
            
            default_storage = settings.DEFAULT_FILE_STORAGE
            if 'S3' in default_storage or 'storages' in default_storage:
                self.stdout.write(self.style.SUCCESS(f"Default storage is properly set to: {default_storage}"))
            else:
                self.stdout.write(self.style.ERROR(f"Default storage does not appear to be S3: {default_storage}"))
        else:
            self.stdout.write(self.style.WARNING("S3 storage is DISABLED in Django settings")) 