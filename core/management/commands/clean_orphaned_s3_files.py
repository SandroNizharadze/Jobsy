import boto3
from django.core.management.base import BaseCommand
from django.conf import settings
from core.models import UserProfile
import logging
import os

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Find and optionally delete orphaned CV files in S3 bucket'

    def add_arguments(self, parser):
        parser.add_argument(
            '--delete',
            action='store_true',
            help='Delete orphaned files (default is to only list them)',
        )
        parser.add_argument(
            '--prefix',
            default='media/private/cvs/',
            help='The S3 prefix to check for orphaned files',
        )

    def handle(self, *args, **options):
        # Check if S3 is enabled
        if not hasattr(settings, 'USE_S3') or not settings.USE_S3:
            self.stdout.write(self.style.ERROR('S3 storage is not enabled. Aborting check.'))
            return
        
        delete_mode = options['delete']
        prefix = options['prefix']
        
        if delete_mode:
            self.stdout.write(self.style.WARNING(f'DELETION MODE ENABLED - orphaned files will be removed from S3!'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Scan mode - orphaned files will be listed but NOT deleted'))
        
        self.stdout.write(f'Checking S3 files with prefix: {prefix}')
        
        # Initialize S3 client
        s3 = boto3.client(
            's3',
            region_name=settings.AWS_S3_REGION_NAME,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        
        try:
            # List objects in bucket
            response = s3.list_objects_v2(
                Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                Prefix=prefix
            )
            
            # Check if any files were found
            if 'Contents' not in response:
                self.stdout.write(self.style.WARNING(f'No files found with prefix {prefix}'))
                return
            
            # Get all CV filenames from the database
            db_cv_files = set()
            for profile in UserProfile.objects.exclude(cv__isnull=True).exclude(cv=''):
                if profile.cv:
                    cv_name = profile.cv.name.strip()
                    db_cv_files.add(cv_name)
                    
                    # Also add alternative path formats to handle different storage patterns
                    if cv_name.startswith('cvs/'):
                        db_cv_files.add(cv_name)
                        db_cv_files.add(f"media/private/{cv_name}")
                        db_cv_files.add(f"private/{cv_name}")
                    elif not any(cv_name.startswith(p) for p in ['media/', 'private/']):
                        db_cv_files.add(f"media/private/cvs/{os.path.basename(cv_name)}")
                        db_cv_files.add(f"private/cvs/{os.path.basename(cv_name)}")
            
            self.stdout.write(f'Found {len(db_cv_files)} CV files in database')
            
            # Track orphaned files
            orphaned_files = []
            
            # Check each S3 file
            for obj in response['Contents']:
                s3_key = obj['Key']
                
                # Skip the directory itself
                if s3_key.endswith('/'):
                    continue
                
                # Extract the filename for comparison
                s3_path_components = [
                    s3_key,  # Full path
                    s3_key.replace(prefix, ''),  # Without prefix
                    s3_key.split('/')[-1],  # Just filename
                    f"cvs/{s3_key.split('/')[-1]}"  # cvs/filename
                ]
                
                # Check if file is referenced in database
                is_referenced = False
                for path_to_check in s3_path_components:
                    if path_to_check in db_cv_files:
                        is_referenced = True
                        break
                
                if not is_referenced:
                    orphaned_files.append({
                        'key': s3_key,
                        'size': obj['Size'],
                        'last_modified': obj['LastModified']
                    })
            
            # Report findings
            if orphaned_files:
                self.stdout.write(self.style.WARNING(f'Found {len(orphaned_files)} orphaned files:'))
                self.stdout.write('-' * 80)
                self.stdout.write(f'{"Key":<60} {"Size":<10} {"Last Modified"}')
                self.stdout.write('-' * 80)
                
                for file in orphaned_files:
                    self.stdout.write(f'{file["key"]:<60} {file["size"]:<10} {file["last_modified"]}')
                
                # Delete if requested
                if delete_mode:
                    self.stdout.write(self.style.WARNING('\nDeleting orphaned files...'))
                    
                    for file in orphaned_files:
                        try:
                            s3.delete_object(
                                Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                                Key=file['key']
                            )
                            self.stdout.write(f'Deleted: {file["key"]}')
                        except Exception as e:
                            self.stdout.write(self.style.ERROR(f'Error deleting {file["key"]}: {str(e)}'))
                    
                    self.stdout.write(self.style.SUCCESS(f'\nDeleted {len(orphaned_files)} orphaned files'))
                else:
                    self.stdout.write(self.style.WARNING('\nTo delete these files, run the command with --delete'))
            else:
                self.stdout.write(self.style.SUCCESS('No orphaned files found!'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}')) 