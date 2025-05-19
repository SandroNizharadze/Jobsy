#!/usr/bin/env python
import os
import sys
import django
import boto3
from botocore.exceptions import ClientError

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jobsy.settings')
django.setup()

from django.conf import settings

def check_s3_configuration():
    """Check if the S3 configuration is complete and correct"""
    print("Checking S3 configuration...")
    
    # Check if S3 is enabled
    if not hasattr(settings, 'USE_S3') or not settings.USE_S3:
        print("ERROR: S3 is not enabled in settings (USE_S3 is False or not set)")
        return False
    
    # Check if AWS credentials are set
    missing_vars = []
    for var in ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_STORAGE_BUCKET_NAME', 'AWS_S3_REGION_NAME']:
        if not hasattr(settings, var) or not getattr(settings, var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"ERROR: Missing S3 configuration variables: {', '.join(missing_vars)}")
        return False
    
    print("S3 configuration is complete.")
    print(f"- AWS_STORAGE_BUCKET_NAME: {settings.AWS_STORAGE_BUCKET_NAME}")
    print(f"- AWS_S3_REGION_NAME: {settings.AWS_S3_REGION_NAME}")
    print(f"- DEFAULT_FILE_STORAGE: {settings.DEFAULT_FILE_STORAGE}")
    if hasattr(settings, 'USE_S3_FOR_STATIC'):
        print(f"- USE_S3_FOR_STATIC: {settings.USE_S3_FOR_STATIC}")
    print(f"- STATIC_URL: {settings.STATIC_URL}")
    print(f"- MEDIA_URL: {settings.MEDIA_URL}")
    
    return True

def check_s3_connection():
    """Test the connection to S3 and check bucket permissions"""
    print("\nTesting S3 connection...")
    
    try:
        # Create a boto3 client
        s3 = boto3.client(
            's3',
            region_name=settings.AWS_S3_REGION_NAME,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        
        # Test listing objects in the bucket
        response = s3.list_objects_v2(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
            MaxKeys=5
        )
        
        # If we reach here, connection was successful
        print("✅ Successfully connected to S3 bucket")
        
        # Check if we can list objects
        if 'Contents' in response:
            print(f"✅ Found {len(response['Contents'])} objects in the bucket (listing first 5)")
            for obj in response['Contents'][:5]:
                print(f"  - {obj['Key']} ({obj['Size']} bytes)")
        else:
            print("✅ Bucket exists but is empty")
        
        # Test writing a temp file
        test_key = 'test-file-delete-me.txt'
        print(f"\nTesting write permissions by creating temporary file: {test_key}")
        
        try:
            s3.put_object(
                Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                Key=test_key,
                Body=b'This is a test file. It can be safely deleted.'
            )
            print("✅ Successfully wrote test file to S3")
            
            # Verify we can read the file back
            s3.get_object(
                Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                Key=test_key
            )
            print("✅ Successfully verified file exists and is readable")
            
            # Clean up by deleting the file
            s3.delete_object(
                Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                Key=test_key
            )
            print("✅ Successfully deleted test file")
            
            print("\nS3 connection and permissions test passed!")
            return True
            
        except ClientError as e:
            print(f"❌ Error during S3 write test: {str(e)}")
            return False
            
    except ClientError as e:
        print(f"❌ Failed to connect to S3: {str(e)}")
        return False

if __name__ == "__main__":
    print("S3 Configuration Checker")
    print("=======================")
    
    # Check configuration
    if not check_s3_configuration():
        print("\nConfiguration check failed. Please check your .env file and S3 settings.")
        sys.exit(1)
    
    # Check connection
    if not check_s3_connection():
        print("\nConnection test failed. Please check your credentials and bucket permissions.")
        sys.exit(2)
    
    print("\nAll checks passed! S3 is properly configured and working.") 