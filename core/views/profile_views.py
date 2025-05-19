from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.db.models import Prefetch, Q
from ..models import UserProfile, EmployerProfile, JobApplication, SavedJob
from ..forms import UserProfileForm, EmployerProfileForm
import logging
import os
import tempfile
import traceback
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from jobsy.storage_backends import PrivateMediaStorage

logger = logging.getLogger(__name__)

@login_required
def profile(request):
    """
    Display and manage user profile
    """
    if not request.user.is_authenticated:
        return redirect('login')
    
    # Get or create user profile
    try:
        user_profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        user_profile = UserProfile(user=request.user)
        user_profile.save()
    
    # Check if it's an AJAX request for CV upload
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    # Handle profile form
    if request.method == 'POST' and ('profile_form' in request.POST or is_ajax):
        logger.info(f"Processing profile form for user {request.user.username} (AJAX: {is_ajax})")
        
        # Enhanced logging for file uploads
        logger.info(f"Request POST data: {dict(request.POST)}")
        logger.info(f"Request FILES: {list(request.FILES.keys())}")
        
        # Log individual file details
        for file_key, file_obj in request.FILES.items():
            logger.info(f"File '{file_key}': name={file_obj.name}, size={file_obj.size}, content_type={file_obj.content_type}")
        
        # Special handling for direct CV upload via AJAX
        if is_ajax and 'cv' in request.FILES:
            logger.info(f"Processing direct CV upload via AJAX")
            try:
                cv_file = request.FILES['cv']
                logger.info(f"Received CV file: {cv_file.name}, size: {cv_file.size}, type: {cv_file.content_type}")
                
                # First check if S3 is enabled
                if hasattr(settings, 'USE_S3') and settings.USE_S3:
                    logger.info(f"S3 is enabled")
                    # Use PrivateMediaStorage for CV files
                    storage = PrivateMediaStorage()
                    file_path = f"cvs/{cv_file.name}"
                    logger.info(f"Saving CV file to S3 at path: {file_path}")
                    
                    # Write the file to a temporary file first to ensure it's valid
                    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                        for chunk in cv_file.chunks():
                            temp_file.write(chunk)
                        temp_path = temp_file.name
                    
                    # Read the file back and upload to S3
                    with open(temp_path, 'rb') as f:
                        file_data = f.read()
                        # Save directly to S3 using the private storage
                        storage.save(file_path, ContentFile(file_data))
                    
                    # Update the user profile with the new CV path
                    user_profile.cv.name = file_path
                    user_profile.save(update_fields=['cv'])
                    
                    # Clean up the temporary file
                    os.unlink(temp_path)
                else:
                    logger.info(f"S3 is not enabled, using default storage")
                    # Write the file to a temporary file first to ensure it's valid
                    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                        for chunk in cv_file.chunks():
                            temp_file.write(chunk)
                        temp_path = temp_file.name
                    
                    logger.info(f"Wrote CV file to temporary path: {temp_path}")
                    
                    # Read the file back
                    with open(temp_path, 'rb') as f:
                        file_data = f.read()
                    
                    # Save directly to the user profile using ContentFile
                    user_profile.cv.save(cv_file.name, ContentFile(file_data))
                    
                    # Clean up the temporary file
                    os.unlink(temp_path)
                
                # Verify the file was saved
                logger.info(f"CV saved. Path in database: {user_profile.cv.name}")
                
                # Verify the file exists in storage
                if user_profile.cv and hasattr(user_profile.cv, 'storage'):
                    if user_profile.cv.storage.exists(user_profile.cv.name):
                        logger.info(f"Verified file exists at {user_profile.cv.name}")
                        # Success!
                        return JsonResponse({'success': True})
                    else:
                        logger.error(f"File does not exist in storage: {user_profile.cv.name}")
                        return JsonResponse({'success': False, 'error': 'File was not saved to storage properly.'})
                
                return JsonResponse({'success': True})
            except Exception as e:
                logger.error(f"Error uploading CV via AJAX: {str(e)}")
                logger.error(traceback.format_exc())
                return JsonResponse({'success': False, 'error': f"Upload error: {str(e)}"})
        
        # Process the standard form
        form = UserProfileForm(request.POST, request.FILES, instance=user_profile)
        if form.is_valid():
            try:
                # Enhanced S3 logging
                if hasattr(settings, 'USE_S3') and settings.USE_S3:
                    logger.info(f"S3 is enabled: {settings.USE_S3}")
                    logger.info(f"S3 Bucket: {settings.AWS_STORAGE_BUCKET_NAME}")
                    logger.info(f"S3 Region: {settings.AWS_S3_REGION_NAME}")
                else:
                    logger.info("S3 is not enabled for this request")
                
                # Log request.FILES content
                logger.info(f"Request FILES: {[f for f in request.FILES]}")
                if 'cv' in request.FILES:
                    cv_file = request.FILES['cv']
                    logger.info(f"CV file details - Name: {cv_file.name}, Size: {cv_file.size}, Content Type: {cv_file.content_type}")
                
                # Temporarily save the instance without committing
                updated_profile = form.save(commit=False)
                
                # Handle file uploads specifically for S3 if needed
                logger.info(f"Handling profile form with files: {bool(request.FILES)}")
                
                # Special handling for profile_picture if present
                if 'profile_picture' in request.FILES:
                    logger.info("Processing new profile picture")
                    # The model field definitions for S3 in core/models.py should handle this automatically
                    updated_profile.profile_picture = request.FILES['profile_picture']
                
                # Special handling for CV if present
                if 'cv' in request.FILES and hasattr(settings, 'USE_S3') and settings.USE_S3:
                    logger.info("Processing new CV with S3 storage")
                    cv_file = request.FILES['cv']
                    
                    # Use PrivateMediaStorage directly for CV files
                    storage = PrivateMediaStorage()
                    file_path = f"cvs/{cv_file.name}"
                    
                    # Save the file to S3
                    storage.save(file_path, cv_file)
                    
                    # Update the model with the file path
                    updated_profile.cv.name = file_path
                else:
                    # For non-S3 storage or if no new CV
                    if 'cv' in request.FILES:
                        logger.info("Processing new CV with standard storage")
                        updated_profile.cv = request.FILES['cv']
                
                # Save the updated profile
                updated_profile.save()
                logger.info(f"Profile saved successfully. CV path: {updated_profile.cv.name if updated_profile.cv else 'None'}")
                
                # Verify the file actually exists in storage after saving
                if updated_profile.cv:
                    cv_path = updated_profile.cv.name
                    try:
                        # For S3, use the appropriate storage
                        if hasattr(settings, 'USE_S3') and settings.USE_S3:
                            storage = PrivateMediaStorage()
                            if storage.exists(cv_path):
                                logger.info(f"Verified CV file exists at {cv_path} in S3")
                                
                                # Additional S3 verification
                                import boto3
                                s3 = boto3.client(
                                    's3',
                                    region_name=settings.AWS_S3_REGION_NAME,
                                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
                                )
                                s3_path = f"{storage.location}/{cv_path}"
                                logger.info(f"S3 file path: {s3_path}")
                                try:
                                    s3.head_object(
                                        Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                                        Key=s3_path
                                    )
                                    logger.info(f"Successfully verified file in S3 bucket at {s3_path}")
                                except Exception as e:
                                    logger.error(f"Error verifying file in S3: {str(e)}")
                            else:
                                logger.error(f"CV file not found in S3 storage after save: {cv_path}")
                        else:
                            # Use default storage for non-S3
                            if default_storage.exists(cv_path):
                                logger.info(f"Verified CV file exists at {cv_path}")
                            else:
                                logger.error(f"CV file not found in default storage after save: {cv_path}")
                    except Exception as e:
                        logger.error(f"Error verifying CV file: {str(e)}")
                
                # Respond to AJAX requests
                if is_ajax:
                    logger.info("Returning JSON success response for AJAX request")
                    return JsonResponse({'success': True})
                
                # Return success for non-AJAX requests
                messages.success(request, "Profile updated successfully!")
                return redirect('profile')
            except Exception as e:
                logger.error(f"Error updating profile: {str(e)}", exc_info=True)  # Include full traceback
                if is_ajax:
                    return JsonResponse({'success': False, 'error': str(e)})
                messages.error(request, f"Error updating profile: {str(e)}")
        else:
            if is_ajax:
                # Return form errors for AJAX requests
                logger.error(f"Form validation errors: {form.errors}")
                return JsonResponse({
                    'success': False, 
                    'error': ', '.join([f"{field}: {error}" for field, errors in form.errors.items() for error in errors])
                })
            else:
                logger.warning(f"Form validation failed (non-AJAX): {form.errors}")
    else:
        form = UserProfileForm(instance=user_profile)
    
    # Get filter parameters
    name_filter = request.GET.get('name', '')
    status_filter = request.GET.get('status', '')
    tab = request.GET.get('tab')
    
    # Start with all user's applications
    applications_query = JobApplication.objects.filter(user=request.user)
    
    # Apply name filter if provided
    if name_filter:
        name_filter_q = Q(job__title__icontains=name_filter)
        # Also search in job_title for deleted jobs
        name_filter_q |= Q(job_title__icontains=name_filter)
        # Search in company name as well
        name_filter_q |= Q(job__company__icontains=name_filter)
        name_filter_q |= Q(job_company__icontains=name_filter)
        
        applications_query = applications_query.filter(name_filter_q)
    
    # Apply status filter if provided
    if status_filter:
        applications_query = applications_query.filter(status=status_filter)
    
    # Get applications ordered by most recent first
    applications = applications_query.order_by('-applied_at')
    
    # Get user's saved jobs
    saved_jobs = SavedJob.objects.filter(user=request.user).order_by('-saved_at')
    
    # Determine if employer profile form should be shown
    show_employer_form = (user_profile.role == 'employer')
    employer_form = None
    
    # Handle employer form if needed
    if show_employer_form:
        try:
            employer_profile = user_profile.employer_profile
        except EmployerProfile.DoesNotExist:
            employer_profile = EmployerProfile(user_profile=user_profile)
            employer_profile.save()
        
        if request.method == 'POST' and 'employer_form' in request.POST:
            employer_form = EmployerProfileForm(request.POST, request.FILES, instance=employer_profile)
            if employer_form.is_valid():
                try:
                    # Temporarily save the instance without committing
                    updated_employer = employer_form.save(commit=False)
                    
                    # Handle company_logo upload specifically for S3 if needed
                    if 'company_logo' in request.FILES:
                        logger.info("Processing new company logo")
                        updated_employer.company_logo = request.FILES['company_logo']
                    
                    # Save the updated employer profile
                    updated_employer.save()
                    
                    # Return success message and redirect
                    messages.success(request, "Employer profile updated successfully!")
                    return redirect('profile')
                except Exception as e:
                    logger.error(f"Error updating employer profile: {str(e)}")
                    messages.error(request, f"Error updating employer profile: {str(e)}")
            else:
                employer_form = EmployerProfileForm(instance=employer_profile)
    
    context = {
        'user_profile': user_profile,
        'profile_form': form,
        'applications': applications,
        'saved_jobs': saved_jobs,
        'show_employer_form': show_employer_form,
        'employer_form': employer_form,
        'active_tab': tab,
        'name_filter': name_filter,
        'status_filter': status_filter,
        'using_s3': hasattr(settings, 'USE_S3') and settings.USE_S3,
    }
    
    return render(request, 'core/profile.html', context)

@login_required
@require_POST
def remove_cv(request):
    """
    Remove the CV file from user profile and S3 bucket
    """
    try:
        logger.info(f"Starting CV removal for user {request.user.username}")
        # Get user profile with select_related for more efficient querying
        user_profile = UserProfile.objects.select_related('user').get(user=request.user)
        
        # Store the file path before deleting
        if user_profile.cv:
            file_name = user_profile.cv.name
            logger.info(f"User has CV: {file_name}")
            
            # For S3 storage, we need to delete the file from S3 first
            if hasattr(settings, 'USE_S3') and settings.USE_S3:
                try:
                    logger.info(f"Attempting to delete file from S3: {file_name}")
                    
                    # Use the same storage backend as used for upload
                    storage = PrivateMediaStorage()
                    
                    # Check if file exists in S3
                    if storage.exists(file_name):
                        storage.delete(file_name)
                        logger.info(f"Successfully deleted file from S3: {file_name}")
                        
                        # Also check and delete with the full path if needed
                        if hasattr(storage, 'location'):
                            s3_path = f"{storage.location}/{file_name}"
                            logger.info(f"Also checking for file at full path: {s3_path}")
                            
                            # Use boto3 to verify deletion
                            import boto3
                            s3 = boto3.client(
                                's3',
                                region_name=settings.AWS_S3_REGION_NAME,
                                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
                            )
                            try:
                                # Try to delete using the full path as well, just in case
                                s3.delete_object(
                                    Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                                    Key=s3_path
                                )
                                logger.info(f"Also deleted file using full S3 path if it existed")
                            except Exception as s3_err:
                                logger.warning(f"Note: Additional deletion attempt failed (this is expected if the file was already properly deleted): {str(s3_err)}")
                    else:
                        logger.warning(f"File does not exist in S3 storage: {file_name}")
                except Exception as e:
                    logger.error(f"Error deleting file from S3: {str(e)}")
                    # Continue with the profile update even if the file deletion fails
                    # The file will be orphaned in S3 but the user experience will not be broken
            else:
                # For local storage, use the standard delete method
                try:
                    file_path = user_profile.cv.path
                    logger.info(f"Attempting to delete local file: {file_path}")
                    user_profile.cv.delete(save=False)
                    logger.info("Successfully deleted file using standard method")
                except Exception as e:
                    logger.error(f"Error with standard file delete: {str(e)}")
        else:
            logger.warning(f"User {request.user.username} has no CV to remove")
        
        # Update the profile fields regardless of delete success
        user_profile.cv = None
        user_profile.cv_consent = False
        user_profile.cv_share_with_employers = False
        user_profile.save(update_fields=['cv', 'cv_consent', 'cv_share_with_employers'])
        
        logger.info(f"CV successfully removed for user {request.user.username}")
        return JsonResponse({'success': True})
    except Exception as e:
        logger.error(f"Error removing CV: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=400)