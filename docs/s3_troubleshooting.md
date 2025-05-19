# S3 Storage Troubleshooting Guide

This guide provides instructions for diagnosing and fixing issues with AWS S3 storage integration in the Jobsy application.

## Prerequisites

Ensure your S3 environment variables are properly set. The application uses the following variables:

- `USE_S3=True` - Enable S3 storage
- `AWS_ACCESS_KEY_ID` - Your AWS access key
- `AWS_SECRET_ACCESS_KEY` - Your AWS secret key  
- `AWS_STORAGE_BUCKET_NAME` - The S3 bucket name
- `AWS_S3_REGION_NAME` - The S3 region (e.g., us-east-1)

You can use the `export_s3_env.sh` script to set these variables.

## Diagnostic Tools

The following management commands have been created to help diagnose and fix S3 storage issues:

### 1. Check S3 Configuration

```bash
python manage.py test_s3_upload
```

This will attempt to upload a test file to S3 to verify that your credentials and configuration are working correctly.

### 2. Check CV Files in S3

```bash
python manage.py check_s3_permissions --cv-only
```

This tool will:
- List all CV files stored in the database
- Check if those files exist in the S3 bucket
- Report any discrepancies between the database and S3

For a more detailed analysis including ACLs (Access Control Lists):

```bash
python manage.py check_s3_permissions --cv-only --check-acls
```

### 3. Fix Missing CV Files

If you have CV files in the database that are missing from S3, you can create placeholder files with:

```bash
# Dry run (report only)
python manage.py fix_missing_cvs --dry-run

# Fix all missing files
python manage.py fix_missing_cvs --fix-all

# Fix for a specific user
python manage.py fix_missing_cvs --username=johndoe
```

This will create placeholder text files at the expected S3 paths to allow the application to function while users re-upload their actual CV files.

### 4. Enable Detailed S3 Logging

To enable detailed logging for all S3 operations:

```bash
python manage.py add_s3_logging
```

This will set up extensive logging for boto3, botocore, s3transfer, and Django storages, which will help in diagnosing upload issues.

## Common Issues and Solutions

### 1. Files Not Appearing in S3 Bucket

**Symptoms:**
- CV files are recorded in the database
- The file upload appears to succeed
- Files are not visible in the S3 bucket

**Solutions:**
- Check if S3 is properly enabled (`USE_S3=True`)
- Verify the S3 region is correctly set with no trailing characters
- Run `python manage.py fix_missing_cvs --dry-run` to identify missing files
- Check application logs for S3 upload errors

### 2. Permission Denied Errors

**Symptoms:**
- Error messages containing "Access Denied" when uploading files
- Users unable to download their CV files

**Solutions:**
- Verify AWS credentials have proper permissions
- Run `python manage.py check_s3_permissions --check-acls` to review bucket and object permissions
- Check that the S3 bucket policy allows the necessary operations

### 3. CORS Issues

**Symptoms:**
- File uploads fail from browser but work from server-side scripts
- Console errors related to cross-origin resource sharing

**Solutions:**
- Ensure the S3 bucket has proper CORS configuration
- Run `python manage.py check_s3_permissions` to verify CORS settings

## Manually Testing S3 Upload

If you need to test S3 uploads for a specific user:

```python
# In Django shell
python manage.py shell

# Then run:
from django.contrib.auth.models import User
from core.models import UserProfile
from django.core.files.base import ContentFile

# Get user profile
user = User.objects.get(username='username_here')
profile = UserProfile.objects.get(user=user)

# Create test file and upload
test_content = ContentFile(b'Test CV file content')
profile.cv.save('test_cv.txt', test_content)

# Verify file exists in storage
print(f"CV path: {profile.cv.name}")
print(f"CV URL: {profile.cv.url}")
```

## Verifying S3 Files via AWS CLI

You can also use the AWS CLI to verify files in your bucket:

```bash
# List files in bucket
aws s3 ls s3://your-bucket-name/ --recursive

# Download a specific file
aws s3 cp s3://your-bucket-name/media/private/cvs/filename.pdf ./downloaded_file.pdf
```

## Resetting S3 Integration

If you need to completely reset and test the S3 integration:

1. Backup your database
2. Clear CV fields in the database: `UserProfile.objects.all().update(cv=None)`
3. Verify S3 environment variables
4. Run the test upload command: `python manage.py test_s3_upload`
5. Have users re-upload their CV files 