import os
from django.core.management.base import BaseCommand
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Add detailed S3 and boto3 logging to the project'

    def add_arguments(self, parser):
        parser.add_argument(
            '--level',
            type=str,
            default='DEBUG',
            choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
            help='Logging level (default: DEBUG)',
        )

    def handle(self, *args, **options):
        log_level = options['level']
        
        self.stdout.write(f"Setting up S3 and boto3 logging at {log_level} level...")
        
        # Configure boto3 logging
        boto3_logger = logging.getLogger('boto3')
        boto3_logger.setLevel(getattr(logging, log_level))
        
        botocore_logger = logging.getLogger('botocore')
        botocore_logger.setLevel(getattr(logging, log_level))
        
        s3transfer_logger = logging.getLogger('s3transfer')
        s3transfer_logger.setLevel(getattr(logging, log_level))
        
        # Configure storage backend logging
        storage_logger = logging.getLogger('storages')
        storage_logger.setLevel(getattr(logging, log_level))
        
        # Add a dedicated file handler for S3 logs
        log_dir = os.path.join(settings.BASE_DIR, 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        s3_log_file = os.path.join(log_dir, 's3.log')
        file_handler = logging.FileHandler(s3_log_file)
        file_handler.setLevel(getattr(logging, log_level))
        
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        
        boto3_logger.addHandler(file_handler)
        botocore_logger.addHandler(file_handler)
        s3transfer_logger.addHandler(file_handler)
        storage_logger.addHandler(file_handler)
        
        # Create a sample S3 test log entry
        storage_logger.debug("S3 logging has been initialized")
        
        self.stdout.write(self.style.SUCCESS(f"S3 logging enabled at {log_level} level"))
        self.stdout.write(f"Log file created at: {s3_log_file}")
        
        # Create /logs/.gitignore if it doesn't exist
        gitignore_path = os.path.join(log_dir, '.gitignore')
        if not os.path.exists(gitignore_path):
            with open(gitignore_path, 'w') as f:
                f.write("# Ignore all log files\n")
                f.write("*.log\n")
            self.stdout.write("Created logs/.gitignore to exclude log files from version control")

        # Print instructions for permanent logging
        self.stdout.write(self.style.WARNING("\nTo make S3 logging permanent, add this to settings.py:"))
        code_block = '''
# S3 Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        's3_file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 's3.log'),
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'boto3': {
            'handlers': ['console', 's3_file'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'botocore': {
            'handlers': ['console', 's3_file'],
            'level': 'DEBUG',
            'propagate': True,
        },
        's3transfer': {
            'handlers': ['console', 's3_file'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'storages': {
            'handlers': ['console', 's3_file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
'''
        self.stdout.write(code_block) 