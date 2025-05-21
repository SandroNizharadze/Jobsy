from django.shortcuts import render, redirect, get_object_or_404
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
from jobsy.storage_backends import PrivateMediaStorage, PublicMediaStorage

logger = logging.getLogger(__name__)

@login_required
def profile(request):
    """
    Display and manage user profile based on role
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
    
    # Initialize form
    form = UserProfileForm(instance=user_profile)
    
    # Handle profile picture upload
    if request.method == 'POST' and request.POST.get('form_type') == 'user_profile':
        form = UserProfileForm(request.POST, request.FILES, instance=user_profile)
        if form.is_valid():
            try:
                # Handle profile picture upload
                if 'profile_picture' in request.FILES:
                    logger.info("Processing new profile picture")
                    
                    # Special handling for S3 storage
                    if hasattr(settings, 'USE_S3') and settings.USE_S3:
                        logger.info("Processing profile picture with S3 storage")
                        profile_picture = request.FILES['profile_picture']
                        
                        # Use PublicMediaStorage for profile pictures
                        storage = PublicMediaStorage()
                        file_path = f"profile_pictures/{profile_picture.name}"
                        
                        # Save the file to S3
                        storage.save(file_path, profile_picture)
                        
                        # Update the model with the file path
                        user_profile.profile_picture.name = file_path
                    else:
                        # For non-S3 storage
                        user_profile.profile_picture = request.FILES['profile_picture']
                
                # Save the updated profile
                user_profile.save()
                
                # Return success message and redirect
                messages.success(request, "Profile updated successfully!")
                return redirect('profile')
            except Exception as e:
                logger.error(f"Error updating profile: {str(e)}")
                messages.error(request, f"Error updating profile: {str(e)}")
    
    # Get filter parameters
    name_filter = request.GET.get('name', '')
    status_filter = request.GET.get('status', '')
    tab = request.GET.get('tab', 'profile')
    template_param = request.GET.get('template', '')
    
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
    is_employer = (user_profile.role == 'employer')
    employer_form = None
    
    # Handle employer form if needed
    if is_employer:
        try:
            employer_profile = user_profile.employer_profile
        except EmployerProfile.DoesNotExist:
            employer_profile = EmployerProfile(user_profile=user_profile)
            employer_profile.save()
        
        if request.method == 'POST' and request.POST.get('form_type') == 'employer_form':
            employer_form = EmployerProfileForm(request.POST, request.FILES, instance=employer_profile)
            if employer_form.is_valid():
                try:
                    # Temporarily save the instance without committing
                    updated_employer = employer_form.save(commit=False)
                    
                    # Handle profile picture upload for employer
                    if 'profile_picture' in request.FILES:
                        logger.info("Processing new profile picture for employer")
                        
                        # Special handling for S3 storage
                        if hasattr(settings, 'USE_S3') and settings.USE_S3:
                            logger.info("Processing profile picture with S3 storage")
                            profile_picture = request.FILES['profile_picture']
                            
                            # Use PublicMediaStorage for profile pictures
                            storage = PublicMediaStorage()
                            file_path = f"profile_pictures/{profile_picture.name}"
                            
                            # Save the file to S3
                            storage.save(file_path, profile_picture)
                            
                            # Update the model with the file path
                            user_profile.profile_picture.name = file_path
                        else:
                            # For non-S3 storage
                            user_profile.profile_picture = request.FILES['profile_picture']
                        
                        # Save the user profile with the new picture
                        user_profile.save()
                    
                    # Handle company logo upload
                    if 'company_logo' in request.FILES:
                        logger.info("Processing new company logo")
                        
                        # Special handling for S3 storage
                        if hasattr(settings, 'USE_S3') and settings.USE_S3:
                            logger.info("Processing company logo with S3 storage")
                            company_logo = request.FILES['company_logo']
                            
                            # Use PublicMediaStorage for company logos
                            storage = PublicMediaStorage()
                            file_path = f"company_logos/{company_logo.name}"
                            
                            # Save the file to S3
                            storage.save(file_path, company_logo)
                            
                            # Update the model with the file path
                            updated_employer.company_logo.name = file_path
                        else:
                            # For non-S3 storage
                            updated_employer.company_logo = request.FILES['company_logo']
                    
                    # Save the employer profile
                    updated_employer.save()
                    
                    # Return success message and redirect
                    messages.success(request, "Employer profile updated successfully!")
                    return redirect('profile')
                except Exception as e:
                    logger.error(f"Error updating employer profile: {str(e)}")
                    messages.error(request, f"Error updating employer profile: {str(e)}")
            # Don't reset the form on validation errors
        else:
            employer_form = EmployerProfileForm(instance=employer_profile)
    
    context = {
        'user_profile': user_profile,
        'profile_form': form,
        'applications': applications,
        'saved_jobs': saved_jobs,
        'employer_form': employer_form,
        'active_tab': tab,
        'name_filter': name_filter,
        'status_filter': status_filter,
        'using_s3': hasattr(settings, 'USE_S3') and settings.USE_S3,
    }
    
    # Choose template based on user role or template parameter
    if template_param == 'employer':
        template = 'core/employer_profile_tailwind.html'
    elif template_param == 'user':
        template = 'core/user_profile_tailwind.html'
    elif is_employer:
        template = 'core/employer_profile_tailwind.html'
    else:
        template = 'core/user_profile_tailwind.html'
    
    return render(request, template, context)

@login_required
@require_POST
def remove_cv(request):
    """
    Remove CV file from user profile and storage
    """
    try:
        # Get the user's profile
        user_profile = request.user.userprofile
        
        # Check if there is a CV to remove
        if not user_profile.cv:
            logger.warning(f"No CV found to remove for user {request.user.username}")
            return JsonResponse({'success': False, 'error': 'No CV found'}, status=400)
        
        # Get the CV file path
        cv_path = user_profile.cv.name
        logger.info(f"Attempting to remove CV: {cv_path} for user {request.user.username}")
        
        # Delete from storage (handling both S3 and local storage)
        try:
            if hasattr(settings, 'USE_S3') and settings.USE_S3:
                # For S3 storage
                logger.info(f"Using S3 storage to delete file: {cv_path}")
                storage = PrivateMediaStorage()
                if storage.exists(cv_path):
                    storage.delete(cv_path)
                    logger.info(f"Successfully deleted CV from S3: {cv_path}")
                else:
                    logger.warning(f"CV file not found in S3: {cv_path}")
            else:
                # For local storage
                logger.info(f"Using local storage to delete file")
                if default_storage.exists(cv_path):
                    default_storage.delete(cv_path)
                    logger.info(f"Successfully deleted CV from local storage: {cv_path}")
                else:
                    logger.warning(f"CV file not found in local storage: {cv_path}")
        except Exception as e:
            # Log the error but continue to update the profile
            logger.error(f"Error deleting CV file: {str(e)}")
            logger.error(traceback.format_exc())
        
        # Update the profile fields regardless of delete success
        user_profile.cv = None
        user_profile.save(update_fields=['cv'])
        
        logger.info(f"CV successfully removed for user {request.user.username}")
        return JsonResponse({'success': True})
    except Exception as e:
        logger.error(f"Error removing CV: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
def get_application_rejection_reasons(request, application_id):
    """API endpoint to get rejection reasons for an application"""
    # Get the application and verify ownership
    application = get_object_or_404(JobApplication, id=application_id)
    
    # Check if the application belongs to the current user
    if application.user != request.user:
        return JsonResponse({'error': 'You do not have permission to view this application'}, status=403)
    
    # Get rejection reasons with their display names
    reasons = [reason.get_name_display() for reason in application.rejection_reasons.all()]
    
    # Return as JSON
    return JsonResponse({
        'reasons': reasons,
        'feedback': application.feedback
    })