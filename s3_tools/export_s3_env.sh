#!/bin/bash

# This script exports AWS S3 environment variables from .env file
# It is used by development.sh and run_with_s3.sh scripts

# Check if .env file exists
ENV_FILE=$(dirname "$0")/../.env
if [ ! -f "$ENV_FILE" ]; then
    echo "ERROR: .env file not found at $ENV_FILE"
    exit 1
fi

# Function to extract and export a variable from .env file
extract_and_export() {
    local var_name=$1
    local var_value=$(grep "^$var_name=" "$ENV_FILE" | cut -d '=' -f 2-)
    
    # Remove quotes if present
    var_value=$(echo "$var_value" | sed -e 's/^"//' -e 's/"$//' -e "s/^'//" -e "s/'$//")
    
    if [ -n "$var_value" ]; then
        export $var_name="$var_value"
        echo "Exported $var_name"
    else
        echo "WARNING: $var_name not found in .env file"
    fi
}

# Extract and export S3 variables
echo "Loading S3 environment variables from $ENV_FILE"
extract_and_export "AWS_ACCESS_KEY_ID"
extract_and_export "AWS_SECRET_ACCESS_KEY"
extract_and_export "AWS_STORAGE_BUCKET_NAME"
extract_and_export "AWS_S3_REGION_NAME"

# Display S3 status
if [ -n "$AWS_ACCESS_KEY_ID" ] && [ -n "$AWS_SECRET_ACCESS_KEY" ] && [ -n "$AWS_STORAGE_BUCKET_NAME" ]; then
    echo "S3 credentials loaded successfully"
else
    echo "WARNING: Some S3 credentials may be missing"
fi
