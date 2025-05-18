# AWS S3 Migration Instructions

## Prerequisites
1. Make sure you have created an S3 bucket in AWS
2. Make sure you have created an IAM user with S3 permissions
3. Make sure you have the IAM user's access key and secret key

## Step 1: Update your environment variables
Edit the export_s3_env.sh script with your actual AWS credentials:
```
export AWS_ACCESS_KEY_ID=your_actual_access_key_id
export AWS_SECRET_ACCESS_KEY=your_actual_secret_access_key
export AWS_STORAGE_BUCKET_NAME=jobsy-media-files
export AWS_S3_REGION_NAME=eu-north-1  # Or your actual region
export USE_S3=True
export DEBUG=False
```

## Step 2: Run the export script
```
source export_s3_env.sh
```

## Step 3: Create folders in your S3 bucket
In the AWS S3 console, create these folders in your bucket:
- static
- media/public
- media/private

## Step 4: Collect static files to S3
```
python manage.py collectstatic --noinput
```

## Step 5: Run a dry run of the migration
```
python manage.py migrate_to_s3 --dry-run
```

## Step 6: If everything looks good, run the actual migration
```
python manage.py migrate_to_s3
```

## Step 7: Update your Render environment variables
In your Render dashboard, add these environment variables:
- AWS_ACCESS_KEY_ID=your_actual_access_key_id
- AWS_SECRET_ACCESS_KEY=your_actual_secret_access_key
- AWS_STORAGE_BUCKET_NAME=jobsy-media-files
- AWS_S3_REGION_NAME=eu-north-1
- USE_S3=True
- DEBUG=False

## Step 8: Deploy to Render
Deploy your application to Render with the updated settings.

## Troubleshooting
If you encounter issues:
1. Check that your AWS credentials are correct
2. Check that your bucket name is correct 
3. Check that CORS is configured properly on your S3 bucket
4. Check that your bucket policy allows access from your application 