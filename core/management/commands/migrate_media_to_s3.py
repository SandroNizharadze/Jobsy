import os
import shutil
from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.files.base import ContentFile
from core.models import UserProfile
from jobsy.storage_backends import PrivateMediaStorage
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Migrate CV files from local media directory to S3'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Just show what would be done without actually doing it',
        )
        parser.add_argument(
            '--clean',
            action='store_true',
            help='Delete local media directory after migration',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        clean = options['clean']
        
        self.stdout.write(self.style.SUCCESS('Starting CV media migration to S3'))
        
        # Check if S3 is enabled
        if not hasattr(settings, 'USE_S3') or not settings.USE_S3:
            self.stdout.write(self.style.ERROR('S3 storage is not enabled. Aborting migration.'))
            return
        
        # Get path to media directory
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        media_dir = os.path.join(base_dir, 'media')
        cv_dir = os.path.join(media_dir, 'cvs')
        
        self.stdout.write(f"Base directory: {base_dir}")
        self.stdout.write(f"Media directory: {media_dir}")
        self.stdout.write(f"CV directory: {cv_dir}")
        
        if not os.path.exists(cv_dir):
            self.stdout.write(f"CV directory not found: {cv_dir}")
            cv_files = []
        else:
            # Get list of all CV files
            cv_files = []
            for root, dirs, files in os.walk(cv_dir):
                for file in files:
                    if not file.startswith('.'):  # Skip hidden files
                        rel_path = os.path.join(os.path.relpath(root, media_dir), file)
                        cv_files.append((os.path.join(root, file), rel_path))
        
        self.stdout.write(f"Found {len(cv_files)} CV files in local media directory")
        
        # Initialize the S3 storage
        s3_storage = PrivateMediaStorage()
        
        # Process each file
        migrated = 0
        errors = 0
        
        for local_path, rel_path in cv_files:
            self.stdout.write(f"Processing: {rel_path}")
            
            try:
                if dry_run:
                    self.stdout.write(self.style.SUCCESS(f"[DRY RUN] Would migrate {rel_path} to S3"))
                else:
                    # Read the file
                    with open(local_path, 'rb') as f:
                        file_content = f.read()
                    
                    # Upload to S3
                    s3_path = rel_path
                    s3_storage.save(s3_path, ContentFile(file_content))
                    
                    self.stdout.write(self.style.SUCCESS(f"Migrated {rel_path} to S3"))
                    
                    # Check if this file is referenced in the database
                    profiles = UserProfile.objects.filter(cv__endswith=os.path.basename(local_path))
                    
                    for profile in profiles:
                        self.stdout.write(f"Found reference in profile for user: {profile.user.username}")
                        
                        # Calculate the full path as it should be in S3
                        correct_s3_path = f"cvs/{os.path.basename(local_path)}"
                        
                        # Update the profile to use the S3 path
                        if profile.cv.name != correct_s3_path:
                            if not dry_run:
                                old_path = profile.cv.name
                                profile.cv.name = correct_s3_path
                                profile.save(update_fields=['cv'])
                                self.stdout.write(f"Updated database path from {old_path} to {correct_s3_path}")
                            else:
                                self.stdout.write(f"[DRY RUN] Would update database path to {correct_s3_path}")
                    
                    migrated += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error processing {rel_path}: {str(e)}"))
                errors += 1
        
        # Summary
        self.stdout.write(self.style.SUCCESS(f"\nMigration Summary:"))
        self.stdout.write(f"Total files processed: {len(cv_files)}")
        self.stdout.write(f"Successfully migrated: {migrated}")
        self.stdout.write(f"Errors: {errors}")
        
        # Clean up the local media directory if requested
        if clean and not dry_run and len(cv_files) > 0 and errors == 0:
            try:
                self.stdout.write(f"Cleaning up local CV directory: {cv_dir}")
                shutil.rmtree(cv_dir)
                self.stdout.write(self.style.SUCCESS(f"Removed local CV directory"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error removing local CV directory: {str(e)}"))
        elif clean and dry_run:
            self.stdout.write(f"[DRY RUN] Would remove local CV directory: {cv_dir}")
        
        # Recommendations
        self.stdout.write(self.style.SUCCESS(f"\nRecommendations:"))
        self.stdout.write(f"1. Test that CV upload works with S3 storage")
        self.stdout.write(f"2. Verify CV files are accessible from user profiles")
        self.stdout.write(f"3. If everything works correctly, you can delete the local media directory with:")
        self.stdout.write(f"   python manage.py migrate_media_to_s3 --clean") 