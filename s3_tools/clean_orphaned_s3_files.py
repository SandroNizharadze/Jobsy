#!/usr/bin/env python
import os
import sys
import django
import boto3
from botocore.exceptions import ClientError
import argparse
from datetime import datetime, timedelta

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jobsy.settings')
django.setup()

from django.conf import settings
from core.models import UserProfile, EmployerProfile

def get_used_files():
    """Get a list of all files being used in the database"""
    used_files = set()
    
    # Get all CV files from user profiles
    for profile in UserProfile.objects.all():
        if profile.cv:
            used_files.add(profile.cv.name)
        if profile.profile_picture:
            used_files.add(profile.profile_picture.name)
    
    # Get all company logos from employer profiles
    for profile in EmployerProfile.objects.all():
        if profile.company_logo:
            used_files.add(profile.company_logo.name)
    
    return used_files

def list_s3_files(prefix=''):
    """List all files in the S3 bucket with the given prefix"""
    s3 = boto3.client(
        's3',
        region_name=settings.AWS_S3_REGION_NAME,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
    )
    
    paginator = s3.get_paginator('list_objects_v2')
    pages = paginator.paginate(
        Bucket=settings.AWS_STORAGE_BUCKET_NAME,
        Prefix=prefix
    )
    
    all_files = []
    for page in pages:
        if 'Contents' in page:
            for obj in page['Contents']:
                # Skip directories
                if not obj['Key'].endswith('/'):
                    all_files.append(obj)
    
    return all_files

def clean_orphaned_files(dry_run=True, days_old=None):
    """Clean orphaned files in S3 that are not referenced in the database"""
    print(f"S3 Orphaned Files Cleaner ({'DRY RUN' if dry_run else 'LIVE RUN'})")
    print("=" * 60)
    
    # Get all files being used in the database
    print("Fetching files referenced in the database...")
    used_files = get_used_files()
    print(f"Found {len(used_files)} files referenced in the database")
    
    # List all files in the S3 bucket
    print("\nFetching files from S3 bucket...")
    all_s3_files = list_s3_files()
    print(f"Found {len(all_s3_files)} files in the S3 bucket")
    
    # Find orphaned files
    orphaned_files = []
    age_limit = None
    if days_old:
        age_limit = datetime.now() - timedelta(days=days_old)
        print(f"\nLooking for orphaned files older than {days_old} days ({age_limit.strftime('%Y-%m-%d')})")
    else:
        print("\nLooking for orphaned files (regardless of age)")
    
    for s3_obj in all_s3_files:
        # Skip files in the static directory - those are handled by collectstatic
        if s3_obj['Key'].startswith('static/'):
            continue
        
        # For media files, add 'media/' prefix if not already present
        file_path = s3_obj['Key']
        if not (file_path.startswith('media/') or file_path.startswith('private/')):
            file_path = f"media/{file_path}"
        
        # Check if the file is being used
        if file_path not in used_files:
            # Check age if needed
            if age_limit and s3_obj['LastModified'] > age_limit:
                continue
                
            orphaned_files.append(s3_obj)
    
    print(f"Found {len(orphaned_files)} orphaned files")
    
    # Delete orphaned files
    if orphaned_files:
        print("\nOrphaned files:")
        total_size = 0
        for i, obj in enumerate(orphaned_files, 1):
            size_kb = obj['Size'] / 1024
            total_size += obj['Size']
            age = datetime.now() - obj['LastModified'].replace(tzinfo=None)
            print(f"{i}. {obj['Key']} ({size_kb:.2f} KB, {age.days} days old)")
        
        print(f"\nTotal space used by orphaned files: {total_size / (1024*1024):.2f} MB")
        
        if not dry_run:
            s3 = boto3.client(
                's3',
                region_name=settings.AWS_S3_REGION_NAME,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
            )
            
            print("\nDeleting orphaned files...")
            for i, obj in enumerate(orphaned_files, 1):
                try:
                    s3.delete_object(
                        Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                        Key=obj['Key']
                    )
                    print(f"Deleted {i}/{len(orphaned_files)}: {obj['Key']}")
                except ClientError as e:
                    print(f"Error deleting {obj['Key']}: {str(e)}")
            
            print(f"\nSuccessfully deleted {len(orphaned_files)} orphaned files")
        else:
            print("\nDRY RUN: No files were deleted. Run with --execute to actually delete files.")
    else:
        print("No orphaned files found. Your S3 bucket is clean!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clean orphaned files in S3 that are not referenced in the database")
    parser.add_argument('--execute', action='store_true', help='Actually delete the files (default is dry run)')
    parser.add_argument('--days', type=int, help='Only clean files older than this many days')
    args = parser.parse_args()
    
    clean_orphaned_files(dry_run=not args.execute, days_old=args.days) 