import os
from django.core.management.base import BaseCommand
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
from core.models import UserProfile, EmployerProfile, JobApplication
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Migrate existing media files to S3'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Only show what would be migrated without actually migrating',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        print(f"Checking S3 settings...")
        print(f"USE_S3 from environment: {os.environ.get('USE_S3', 'NOT SET')}")
        print(f"Storage backend: {default_storage.__class__.__name__}")
        
        # Check if we're using S3 storage
        is_s3_enabled = (hasattr(settings, 'AWS_STORAGE_BUCKET_NAME') and 
                          hasattr(settings, 'AWS_ACCESS_KEY_ID') and 
                          hasattr(settings, 'AWS_SECRET_ACCESS_KEY'))
        
        if not is_s3_enabled:
            self.stderr.write('S3 storage is not enabled in settings')
            return
            
        self.stdout.write(self.style.NOTICE('Starting migration of files to S3'))
        
        # Migrate profile pictures
        self.stdout.write(self.style.NOTICE('Migrating profile pictures...'))
        self._migrate_model_field(UserProfile, 'profile_picture', dry_run)
        
        # Migrate CVs
        self.stdout.write(self.style.NOTICE('Migrating CVs...'))
        self._migrate_model_field(UserProfile, 'cv', dry_run)
        
        # Migrate company logos
        self.stdout.write(self.style.NOTICE('Migrating company logos...'))
        self._migrate_model_field(EmployerProfile, 'company_logo', dry_run)
        
        # Migrate resumes
        self.stdout.write(self.style.NOTICE('Migrating resumes...'))
        self._migrate_model_field(JobApplication, 'resume', dry_run)
        
        self.stdout.write(self.style.SUCCESS('Migration complete!'))
    
    def _migrate_model_field(self, model, field_name, dry_run):
        """Migrate files from a specific model field to S3."""
        items = model.objects.exclude(**{f'{field_name}': ''}).exclude(**{f'{field_name}': None})
        count = items.count()
        self.stdout.write(f'Found {count} {field_name} files to migrate')
        
        for i, item in enumerate(items):
            file_field = getattr(item, field_name)
            if not file_field:
                continue
                
            try:
                file_path = file_field.path
                if not os.path.exists(file_path):
                    self.stdout.write(self.style.WARNING(f'File not found: {file_path}'))
                    continue
                    
                file_name = os.path.basename(file_path)
                s3_key = f'{file_field.field.upload_to}{file_name}'
                
                self.stdout.write(f'Migrating {i+1}/{count}: {file_name}')
                
                if not dry_run:
                    try:
                        # Open and read the file
                        with open(file_path, 'rb') as f:
                            file_content = f.read()
                        
                        # Create a proper ContentFile instead of passing bytes directly
                        content_file = ContentFile(file_content)
                        
                        # Upload to S3 using default_storage
                        new_path = default_storage.save(s3_key, content_file)
                        self.stdout.write(self.style.SUCCESS(f'Migrated to {new_path}'))
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'Error migrating {file_path}: {str(e)}'))
                else:
                    self.stdout.write(self.style.SUCCESS(f'Would migrate {file_path} to {s3_key}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error processing {field_name} for item {item.id}: {str(e)}')) 