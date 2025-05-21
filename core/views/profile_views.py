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
    
    # Handle form submission
    if request.method == 'POST':
        form_type = request.POST.get('form_type')
        
        if form_type == 'user_profile':
            form = UserProfileForm(request.POST, request.FILES, instance=user_profile)
            if form.is_valid():
                form.save()
                if is_ajax:
                    return JsonResponse({'success': True})
                messages.success(request, "Profile updated successfully!")
                return redirect('edit_profile')
        
        elif form_type == 'employer_form' and user_profile.role == 'employer':
            employer_form = EmployerProfileForm(request.POST, request.FILES, instance=user_profile.employer_profile)
            if employer_form.is_valid():
                employer_form.save()
                messages.success(request, "Company profile updated successfully!")
                return redirect('edit_profile')
    
    # Get filters from query params
    name_filter = request.GET.get('name', '')
    status_filter = request.GET.get('status', '')
    tab = request.GET.get('tab', 'profile')
    template_param = request.GET.get('template', '')
    
    # Get user's applications with proper joins
    applications = JobApplication.objects.filter(
        user=request.user
    ).select_related(
        'job',
        'job__employer'
    ).order_by('-applied_at')
    
    # Apply name filter if provided
    if name_filter:
        name_filter_q = Q(job__title__icontains=name_filter)
        # Also search in job_title for deleted jobs
        name_filter_q |= Q(job_title__icontains=name_filter)
        # Search in company name as well
        name_filter_q |= Q(job__company__icontains=name_filter)
        name_filter_q |= Q(job_company__icontains=name_filter)
        applications = applications.filter(name_filter_q)
    
    # Apply status filter if provided
    if status_filter:
        applications = applications.filter(status=status_filter)
    
    # Get user's saved jobs with proper joins
    saved_jobs = SavedJob.objects.filter(
        user=request.user
    ).select_related(
        'job',
        'job__employer'
    ).order_by('-saved_at')
    
    # Determine if employer profile form should be shown
    is_employer = (user_profile.role == 'employer')
    employer_form = None
    if is_employer:
        try:
            employer_form = EmployerProfileForm(instance=user_profile.employer_profile)
        except EmployerProfile.DoesNotExist:
            pass
    
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
        template = 'core/employer_edit_profile_tailwind.html'
    elif template_param == 'user':
        template = 'core/user_profile_tailwind.html'
    elif is_employer:
        template = 'core/employer_edit_profile_tailwind.html'
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
        messages.success(request, "CV removed successfully.")
        return redirect('edit_profile')
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