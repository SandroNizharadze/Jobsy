#!/bin/bash

# First, kill any existing server
pkill -f runserver || true

# Source S3 environment variables
source $(dirname "$0")/export_s3_env.sh

# Check if environment variables are properly set
if [ "$USE_S3" != "True" ]; then
  echo "ERROR: USE_S3 is not set to True. Check your .env.s3 file."
  exit 1
fi

# Log S3 settings
echo "Starting Django server with S3 storage enabled:"
echo "AWS_STORAGE_BUCKET_NAME: $AWS_STORAGE_BUCKET_NAME"
echo "AWS_S3_REGION_NAME: $AWS_S3_REGION_NAME"
echo "DEFAULT_FILE_STORAGE: jobsy.storage_backends.PrivateMediaStorage"

# Start the Django server
cd "$(dirname "$0")/.." && python manage.py runserver 