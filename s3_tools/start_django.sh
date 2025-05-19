#!/bin/bash

# Load variables from .env.s3 into the environment
export $(grep -v '^#' $(dirname "$0")/../.env.s3 | sed 's/%//' | xargs)

# Verify S3 is enabled
echo "S3 enabled: $USE_S3"
echo "AWS bucket: $AWS_STORAGE_BUCKET_NAME"
echo "AWS region: $AWS_S3_REGION_NAME"

# Launch the Django server
cd "$(dirname "$0")/.." && python manage.py runserver 