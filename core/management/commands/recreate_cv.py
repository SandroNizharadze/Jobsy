import os
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import UserProfile
from jobsy.storage_backends import PrivateMediaStorage

class Command(BaseCommand):
    help = 'Recreate a missing CV file in S3'

    def handle(self, *args, **options):
        self.stdout.write('Attempting to recreate a CV file in S3...')
        
        # Get a user profile with a CV
        username = 'sandronizharadze77'  # Change to the username you want to fix
        try:
            user = User.objects.get(username=username)
            profile = UserProfile.objects.get(user=user)
            
            if not profile.cv:
                self.stdout.write(self.style.ERROR(f"User {username} doesn't have a CV path in database"))
                return
                
            cv_path = profile.cv.name
            self.stdout.write(f"User {username} has CV path: {cv_path}")
            
            # Create a test file to upload
            test_filename = 'replacement_cv.txt'
            with open(test_filename, 'w') as f:
                f.write(f'This is a replacement CV file for user {username}.\n')
                f.write(f'The original path was: {cv_path}\n')
                f.write('This file was created to test S3 storage integration.')
            
            self.stdout.write(f"Created replacement file: {test_filename}")
            
            # Upload using PrivateMediaStorage
            storage = PrivateMediaStorage()
            
            # Upload to the exact same path that's in the database
            self.stdout.write(f"Uploading to path: {cv_path}")
            with open(test_filename, 'rb') as f:
                saved_path = storage.save(cv_path, f)
                self.stdout.write(f"Saved to path: {saved_path}")
            
            self.stdout.write(f"Full S3 path should be: {storage.location}/{saved_path}")
            
            # Clean up
            os.remove(test_filename)
            self.stdout.write(f"Cleaned up local test file")
            
            self.stdout.write(self.style.SUCCESS(f"Successfully recreated CV file for {username}"))
            
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"User {username} not found"))
        except UserProfile.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"UserProfile for {username} not found"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {str(e)}")) 