from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from ..models import UserProfile, EmployerProfile
from ..forms import UserProfileForm, EmployerProfileForm
import logging

logger = logging.getLogger(__name__)

@login_required
def profile(request):
    """
    Display and handle updates to user profile
    """
    user = request.user
    user_profile, created = UserProfile.objects.get_or_create(user=user)
    
    # Check if user is an employer
    is_employer = user_profile.role == 'employer'
    
    # Get employer profile if applicable
    employer_profile = None
    if is_employer:
        employer_profile, created = EmployerProfile.objects.get_or_create(user_profile=user_profile)
    
    if request.method == 'POST':
        # Determine which form was submitted
        form_type = request.POST.get('form_type')
        
        if form_type == 'user_profile':
            # Process user profile form
            user_form = UserProfileForm(request.POST, request.FILES, instance=user_profile)
            
            if user_form.is_valid():
                user_form.save()
                messages.success(request, "Your profile has been updated.")
                return redirect('profile')
            else:
                # If the form is invalid, display errors
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
        else:
            # Invalid form type
            messages.error(request, "Invalid form submission.")
            
            # Create fresh forms
            user_form = UserProfileForm(instance=user_profile)
            if is_employer:
                employer_form = EmployerProfileForm(instance=employer_profile)
    else:
        # GET request - initialize forms
        user_form = UserProfileForm(instance=user_profile)
        
        if is_employer:
            employer_form = EmployerProfileForm(instance=employer_profile)
    
    # Prepare context for template
    context = {
        'user': user,
        'user_profile': user_profile,
        'user_form': user_form,
        'is_employer': is_employer,
    }
    
    # Add employer context if applicable
    if is_employer:
        context.update({
            'employer_profile': employer_profile,
            'employer_form': employer_form,
        })
    
    return render(request, 'core/profile.html', context)

@login_required
@require_POST
def remove_cv(request):
    """
    Remove the CV file from user profile
    """
    try:
        user_profile = request.user.userprofile
        
        # Delete the file
        if user_profile.cv:
            user_profile.cv.delete()
        
        # Update the profile
        user_profile.cv = None
        user_profile.cv_consent = False
        user_profile.cv_share_with_employers = False
        user_profile.save()
        
        return JsonResponse({'success': True})
    except Exception as e:
        logger.error(f"Error removing CV: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=400) 