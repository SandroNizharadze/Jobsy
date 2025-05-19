#!/bin/bash

# Kill any existing server
pkill -f runserver || true

# Make sure we're using production mode
if grep -q "DEBUG=True" .env; then
  echo "Setting DEBUG=False in .env file for production mode..."
  sed -i '' 's/DEBUG=True/DEBUG=False/' .env
fi

# Make sure we're using S3 for media storage
if grep -q "USE_S3=False" .env; then
  echo "Setting USE_S3=True in .env file for S3 storage..."
  sed -i '' 's/USE_S3=False/USE_S3=True/' .env
fi

# Use S3 for both media and static files
export USE_S3=True
export DEBUG=False
export USE_S3_FOR_STATIC=True

# Load other S3 vars
source $(dirname "$0")/export_s3_env.sh

echo "Starting Django production server with:"
echo "  - DEBUG mode: disabled (production mode)"
echo "  - S3 media storage: enabled (for uploads)"
echo "  - Static files: served from S3 (USE_S3_FOR_STATIC=True)"

# Collect static files first
echo "Collecting static files to S3..."
python manage.py collectstatic --noinput

# Start the server
python manage.py runserver 