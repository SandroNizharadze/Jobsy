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
AWS_DEFAULT_ACL = 'public-read'  # For public files like company logos, profile pictures
AWS_LOCATION = 'static'
AWS_QUERYSTRING_AUTH = False  # Don't add complex authentication-related query parameters to URLs

# Static files configuration
STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/{AWS_LOCATION}/'

# Media files configuration
DEFAULT_FILE_STORAGE = 'jobsy.storage_backends.PublicMediaStorage'

# Print S3 settings for debugging
print(f"AWS_ACCESS_KEY_ID: {'*' * 8 if AWS_ACCESS_KEY_ID else 'NOT SET'}")
print(f"AWS_SECRET_ACCESS_KEY: {'*' * 8 if AWS_SECRET_ACCESS_KEY else 'NOT SET'}")
print(f"AWS_STORAGE_BUCKET_NAME: {AWS_STORAGE_BUCKET_NAME}")
print(f"AWS_S3_REGION_NAME: {AWS_S3_REGION_NAME}")
print(f"STATIC_URL: {STATIC_URL}")

# Keep local static files for development
if os.environ.get('DEBUG', 'True') == 'True':
    print("Debug mode detected, using local storage for static files")
    STATIC_URL = '/static/'
    STATIC_ROOT = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'staticfiles')
    STATICFILES_DIRS = [
        os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static'),
    ]
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
else:
    print("Production mode detected, using S3 for all storage") 