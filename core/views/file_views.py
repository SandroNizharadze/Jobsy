import logging
import boto3
from botocore.exceptions import ClientError
from django.http import HttpResponseRedirect, HttpResponseNotFound, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.conf import settings
from ..models import UserProfile, JobApplication

logger = logging.getLogger(__name__)

@login_required
def serve_cv_file(request, user_id=None):
    """
    Serve a CV file securely by generating a temporary signed URL and redirecting to it.
    If user_id is None, serves the current user's CV.
    If user_id is provided, only employers who have received the CV through a job application can access it.
    """
    try:
        # Determine which CV to serve
        if user_id is None or int(user_id) == request.user.id:
            # User wants to see their own CV
            try:
                user_profile = request.user.userprofile
            except UserProfile.DoesNotExist:
                logger.error(f"User {request.user.username} has no profile")
                return HttpResponseNotFound("Profile not found")
        else:
            # User wants to see someone else's CV - must be an employer with a job application
            try:
                # Check if the requesting user is an employer
                if not hasattr(request.user, 'userprofile') or request.user.userprofile.role != 'employer':
                    logger.warning(f"Non-employer user {request.user.username} attempted to access another user's CV")
                    return HttpResponseForbidden("You don't have permission to access this CV")
                
                # Get the target user's profile
                target_profile = UserProfile.objects.get(user_id=user_id)
                
                # Check if this employer has any job applications from this user
                employer_profile = request.user.userprofile.employer_profile
                has_application = JobApplication.objects.filter(
                    user_id=user_id,
                    job__employer=employer_profile
                ).exists()
                
                if not has_application:
                    logger.warning(f"Employer {request.user.username} attempted to access CV for user {user_id} without an application")
                    return HttpResponseForbidden("You don't have permission to access this CV")
                
                user_profile = target_profile
            except UserProfile.DoesNotExist:
                logger.error(f"Target user {user_id} profile not found")
                return HttpResponseNotFound("Target user profile not found")
        
        # Check if the user has a CV
        if not user_profile.cv:
            logger.warning(f"User {user_profile.user.username} has no CV")
            return HttpResponseNotFound("No CV found for this user")
        
        # If S3 is not enabled, just use the standard URL
        if not getattr(settings, 'USE_S3', False):
            return HttpResponseRedirect(user_profile.cv.url)
        
        # For S3, create a signed URL directly with boto3
        try:
            s3_client = boto3.client(
                's3',
                region_name=settings.AWS_S3_REGION_NAME,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
            )
            
            # Get the file path - this should handle both configurations
            if hasattr(user_profile.cv, 'storage') and hasattr(user_profile.cv.storage, 'location'):
                # Use full path with storage location
                file_key = f"{user_profile.cv.storage.location}/{user_profile.cv.name}"
                
                # Sometimes we get duplicate media/ prefixes, so clean that up
                file_key = file_key.replace('media/media/', 'media/')
            else:
                # Fallback to just the name
                file_key = user_profile.cv.name
            
            logger.info(f"Generating signed URL for S3 key: {file_key}")
            
            # Generate a signed URL valid for 1 hour
            signed_url = s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
                    'Key': file_key,
                },
                ExpiresIn=3600  # 1 hour in seconds
            )
            
            logger.info(f"Generated signed URL successfully")
            
            # Redirect to the signed URL
            return HttpResponseRedirect(signed_url)
            
        except ClientError as e:
            logger.error(f"Error generating presigned URL: {str(e)}")
            return HttpResponseNotFound("Error accessing the file")
            
    except Exception as e:
        logger.error(f"Error serving CV file: {str(e)}")
        return HttpResponseNotFound("Error accessing the file") 