import logging
import boto3
from botocore.exceptions import ClientError
from django.http import HttpResponseRedirect, HttpResponseNotFound, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.conf import settings
from ..models import UserProfile

logger = logging.getLogger(__name__)

@login_required
def serve_cv_file(request, user_id=None):
    """
    Serve a CV file securely by generating a temporary signed URL and redirecting to it.
    If user_id is None, serves the current user's CV.
    If user_id is provided, only employers can access other users' CVs, and only if
    they have the permission to view them.
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
            # User wants to see someone else's CV - must be an employer with permission
            try:
                # Check if the requesting user is an employer
                if not hasattr(request.user, 'userprofile') or request.user.userprofile.role != 'employer':
                    logger.warning(f"Non-employer user {request.user.username} attempted to access another user's CV")
                    return HttpResponseForbidden("You don't have permission to access this CV")
                
                # Get the target user's profile
                target_profile = UserProfile.objects.get(user_id=user_id)
                
                # Check if the target user has allowed CV sharing with employers
                if not target_profile.cv_consent or not target_profile.cv_share_with_employers:
                    logger.warning(f"User {user_id} has not consented to share their CV")
                    return HttpResponseForbidden("This user has not consented to share their CV")
                
                # Check if this specific employer has permission to view this CV
                employer_profile = request.user.userprofile.employerprofile
                if employer_profile not in target_profile.cv_visible_to.all():
                    logger.warning(f"Employer {request.user.username} is not authorized to view CV for user {user_id}")
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