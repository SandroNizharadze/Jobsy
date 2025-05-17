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
    
    # Handle profile form
    if request.method == 'POST' and 'profile_form' in request.POST:
        form = UserProfileForm(request.POST, request.FILES, instance=user_profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully!")
            return redirect('profile')
    else:
        form = UserProfileForm(instance=user_profile)
    
    # Get user's job applications
    applications = JobApplication.objects.filter(user=request.user).order_by('-applied_at')
    
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
                employer_form.save()
                messages.success(request, "Employer profile updated successfully!")
                return redirect('profile')
        else:
            employer_form = EmployerProfileForm(instance=employer_profile)
    
    context = {
        'user_profile': user_profile,
        'profile_form': form,
        'applications': applications,
        'saved_jobs': saved_jobs,
        'show_employer_form': show_employer_form,
        'employer_form': employer_form,
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