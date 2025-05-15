from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.db.models import Prefetch
from ..models import UserProfile, EmployerProfile, JobApplication, SavedJob
from ..forms import UserProfileForm, EmployerProfileForm
import logging

logger = logging.getLogger(__name__)

@login_required
def profile(request):
    """
    Handle user profile view and updates
    """
    user_profile = request.user.userprofile
    is_employer = user_profile.role == 'employer'
    
    # Initialize forms
    user_form = UserProfileForm(instance=user_profile)
    employer_form = None
    
    if is_employer:
        employer_profile = user_profile.employer_profile
        employer_form = EmployerProfileForm(instance=employer_profile)
    
    if request.method == 'POST':
        # Determine which form was submitted
        form_type = request.POST.get('form_type')
        
        if form_type == 'user_profile':
            # Process user profile form
            user_form = UserProfileForm(request.POST, request.FILES, instance=user_profile)
            
            if user_form.is_valid():
                user_form.save()
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': True})
                messages.success(request, "Your profile has been updated.")
                return redirect('profile')
            else:
                # If the form is invalid, display errors
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'error': ' '.join([error for errors in user_form.errors.values() for error in errors])
                    })
                for field, errors in user_form.errors.items():
                    for error in errors:
                        messages.error(request, f"{error}")
                
                # Create a fresh employer form if needed
                if is_employer:
                    employer_form = EmployerProfileForm(instance=employer_profile)
        
        elif form_type == 'employer_profile' and is_employer:
            # Process employer profile form
            employer_form = EmployerProfileForm(request.POST, request.FILES, instance=employer_profile)
            
            if employer_form.is_valid():
                employer_form.save()
                messages.success(request, "Your company profile has been updated.")
                return redirect('profile')
            else:
                # If the form is invalid, display errors
                for field, errors in employer_form.errors.items():
                    for error in errors:
                        messages.error(request, f"{error}")
                
                # Create a fresh user profile form
                user_form = UserProfileForm(instance=user_profile)
    
    # Get user's job applications if they are a candidate
    applications = None
    saved_jobs = None
    if user_profile.role == 'candidate':
        applications = JobApplication.objects.filter(user=request.user).select_related('job').order_by('-applied_at')
        saved_jobs = SavedJob.objects.filter(user=request.user).select_related('job').order_by('-saved_at')
    
    context = {
        'user_form': user_form,
        'employer_form': employer_form,
        'applications': applications,
        'saved_jobs': saved_jobs,
    }
    
    return render(request, 'core/profile.html', context)

@login_required
@require_POST
def remove_cv(request):
    """
    Remove the CV file from user profile
    """
    try:
        # Get user profile with select_related for more efficient querying
        user_profile = UserProfile.objects.select_related('user').get(user=request.user)
        
        # Delete the file
        if user_profile.cv:
            user_profile.cv.delete()
        
        # Update the profile
        user_profile.cv = None
        user_profile.cv_consent = False
        user_profile.cv_share_with_employers = False
        user_profile.save(update_fields=['cv', 'cv_consent', 'cv_share_with_employers'])  # Only update specific fields
        
        return JsonResponse({'success': True})
    except Exception as e:
        logger.error(f"Error removing CV: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=400) 