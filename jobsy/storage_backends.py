from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage
import os

class StaticStorage(S3Boto3Storage):
    location = 'static'
    querystring_auth = False  # No need for authentication on static files

class PublicMediaStorage(S3Boto3Storage):
    location = 'media/public'
    file_overwrite = False
    querystring_auth = False  # No need for authentication on public media files

class PrivateMediaStorage(S3Boto3Storage):
    location = 'media/private'
    file_overwrite = False
    custom_domain = False  # Use AWS S3 domain for signed URLs
    querystring_auth = True  # Ensure authentication is enabled for private files
    querystring_expire = 3600  # URL valid for 1 hour 