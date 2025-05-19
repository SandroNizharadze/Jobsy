import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# AWS S3 Configuration
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME', 'jobsy-media-files')
AWS_S3_REGION_NAME = os.environ.get('AWS_S3_REGION_NAME', 'us-east-1')  # Change to your preferred region
AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=86400',  # 1 day cache
}
AWS_LOCATION = 'static'
# Enable query string auth for private files while keeping it disabled for public files
AWS_QUERYSTRING_AUTH = True  # Enable signed URLs for private files
AWS_QUERYSTRING_EXPIRE = 3600  # Set URL expiration to 1 hour (optional)

# Media files configuration
# Use PrivateMediaStorage for all media files by default
# This ensures CV uploads go to the private storage
DEFAULT_FILE_STORAGE = 'jobsy.storage_backends.PrivateMediaStorage'

# When S3 is enabled, override local media settings
# This ensures that Django doesn't try to write files locally
MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/media/'
MEDIA_ROOT = None  # Don't use local media directory when S3 is enabled

# Print S3 settings for debugging
print(f"AWS_ACCESS_KEY_ID: {'*' * 8 if AWS_ACCESS_KEY_ID else 'NOT SET'}")
print(f"AWS_SECRET_ACCESS_KEY: {'*' * 8 if AWS_SECRET_ACCESS_KEY else 'NOT SET'}")
print(f"AWS_STORAGE_BUCKET_NAME: {AWS_STORAGE_BUCKET_NAME}")
print(f"AWS_S3_REGION_NAME: {AWS_S3_REGION_NAME}")

# Use S3 for static files only if explicitly configured
USE_S3_FOR_STATIC = os.environ.get('USE_S3_FOR_STATIC', 'False') == 'True'

if USE_S3_FOR_STATIC:
    # Static files configuration for S3
    STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/{AWS_LOCATION}/'
    print(f"Using S3 for static files: {STATIC_URL}")
else:
    # Keep local static files by default (especially important for admin CSS)
    STATIC_URL = '/static/'
    STATIC_ROOT = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'staticfiles')
    STATICFILES_DIRS = [
        os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static'),
    ]
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
    print(f"Using local storage for static files: {STATIC_URL}") 