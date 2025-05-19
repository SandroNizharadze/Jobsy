import boto3
from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    help = 'List files in the S3 bucket to verify uploads'

    def add_arguments(self, parser):
        parser.add_argument(
            '--prefix',
            default='media/private/cvs/',
            help='The prefix to filter by (e.g., media/private/cvs/)',
        )

    def handle(self, *args, **options):
        # Check if S3 is enabled
        if not hasattr(settings, 'USE_S3') or not settings.USE_S3:
            self.stdout.write(self.style.ERROR('S3 storage is not enabled. Aborting check.'))
            return
        
        prefix = options['prefix']
        self.stdout.write(self.style.SUCCESS(f'Listing S3 files with prefix: {prefix}'))
        
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
            
            # Display file information
            self.stdout.write(self.style.SUCCESS(f'Found {len(response["Contents"])} files:'))
            self.stdout.write('-' * 80)
            self.stdout.write(f'{"Key":<60} {"Size":<10} {"Last Modified"}')
            self.stdout.write('-' * 80)
            
            total_size = 0
            for obj in response['Contents']:
                key = obj['Key']
                size = obj['Size']
                last_modified = obj['LastModified']
                self.stdout.write(f'{key:<60} {size:<10} {last_modified}')
                total_size += size
            
            self.stdout.write('-' * 80)
            self.stdout.write(f'Total size: {total_size} bytes')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error accessing S3: {str(e)}')) 