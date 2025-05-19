#!/bin/bash

# Load secrets from .env.s3 file
if [ -f .env.s3 ]; then
    echo "Loading environment variables from .env.s3 file..."
    
    # Use grep to extract values but keep them as separate exports for better security
    export USE_S3=$(grep -E "^USE_S3=" .env.s3 | cut -d "=" -f2 | tr -d '%')
    export DEBUG=$(grep -E "^DEBUG=" .env.s3 | cut -d "=" -f2 | tr -d '%')
    export AWS_ACCESS_KEY_ID=$(grep -E "^AWS_ACCESS_KEY_ID=" .env.s3 | cut -d "=" -f2 | tr -d '%')
    export AWS_SECRET_ACCESS_KEY=$(grep -E "^AWS_SECRET_ACCESS_KEY=" .env.s3 | cut -d "=" -f2 | tr -d '%')
    export AWS_STORAGE_BUCKET_NAME=$(grep -E "^AWS_STORAGE_BUCKET_NAME=" .env.s3 | cut -d "=" -f2 | tr -d '%')
    export AWS_S3_REGION_NAME=$(grep -E "^AWS_S3_REGION_NAME=" .env.s3 | cut -d "=" -f2 | tr -d '%')
    
    echo "S3 environment variables loaded successfully!"
    echo "AWS_ACCESS_KEY_ID: ${AWS_ACCESS_KEY_ID:0:3}..."
    echo "AWS_STORAGE_BUCKET_NAME: $AWS_STORAGE_BUCKET_NAME"
    echo "AWS_S3_REGION_NAME: $AWS_S3_REGION_NAME"
    echo "USE_S3: $USE_S3"
    echo "DEBUG: $DEBUG"
else
    echo "Error: .env.s3 file not found!"
    exit 1
fi
