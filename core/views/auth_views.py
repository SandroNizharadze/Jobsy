from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from ..forms import RegistrationForm, EmployerRegistrationForm
from ..models import UserProfile, EmployerProfile
import logging

logger = logging.getLogger(__name__)

def is_employer(user):
    """
    Check if a user has employer role and associated employer profile
    """
    try:
        return (user.is_authenticated and 
                hasattr(user, 'userprofile') and 
                user.userprofile.role == 'employer' and
                hasattr(user.userprofile, 'employer_profile'))
    except:
        return False

def login_view(request):
    """Handle user login with email or username"""
    if request.user.is_authenticated:
        if is_employer(request.user):
            return redirect('employer_home')
        return redirect('job_list')
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            
            # Try to authenticate with username (which is email in our case)
            user = authenticate(username=username, password=password)
            
            # If that fails, try to find user by email and authenticate with their username
            if user is None:
                try:
                    user_by_email = User.objects.get(email=username)
                    user = authenticate(username=user_by_email.username, password=password)
                except User.DoesNotExist:
                    user = None
            
            if user is not None:
                # Ensure backend is set
                if not hasattr(user, 'backend'):
                    user.backend = 'django.contrib.auth.backends.ModelBackend'
                login(request, user)
                if is_employer(user):
                    return redirect('employer_home')
                return redirect('job_list')
            else:
                messages.error(request, "Invalid email or password.")
        else:
            messages.error(request, "Invalid email or password.")
    else:
        form = AuthenticationForm()
    
    return render(request, 'core/login_tailwind.html', {'form': form})

def logout_view(request):
    """Handle user logout"""
    logout(request)
    return redirect('job_list')

def register(request):
    """Handle user registration for both candidates and employers"""
    if request.user.is_authenticated:
        return redirect('job_list')
    
    if request.method == 'POST':
        # Get user_type directly from POST data 
        user_type = request.POST.get('user_type', 'candidate')
        logger.info(f"Registration attempt with user_type: {user_type}")
        
        # Override ROLE based on user selection - this is crucial
        if user_type not in ['candidate', 'employer']:
            user_type = 'candidate'  # Default to candidate if invalid value
            logger.warning(f"Invalid user_type detected, defaulting to candidate")
        
        # We'll use a transaction to ensure everything happens atomically
        from django.db import transaction
        
        if user_type == 'employer':
            form = RegistrationForm(request.POST)
            employer_form = EmployerRegistrationForm(request.POST)
            
            logger.info(f"Processing employer registration")
            
            if form.is_valid() and employer_form.is_valid():
                try:
                    with transaction.atomic():
                        # Create the user first
                        user = form.save()
                        logger.info(f"Created user {user.username} (email: {user.email})")
                        
                        # Use the updated helper method to safely create/update profiles
                        # This handles any possible race conditions with signals
                        # First check if a UserProfile exists before calling create_for_user
                        try:
                            if UserProfile.objects.filter(user=user).exists():
                                # If a profile exists but is not an employer, update it
                                profile = UserProfile.objects.get(user=user)
                                if profile.role != 'employer':
                                    profile.role = 'employer'
                                    profile.save()
                                    logger.info(f"Updated existing profile for {user.username} to employer role")
                                    
                                # Now ensure an employer profile exists with our data
                                employer_profile, created = EmployerProfile.objects.get_or_create(
                                    user_profile=profile,
                                    defaults={
                                        'company_name': employer_form.cleaned_data.get('company_name'),
                                        'company_id': employer_form.cleaned_data.get('company_id'),
                                        'phone_number': employer_form.cleaned_data.get('phone_number')
                                    }
                                )
                                if not created:
                                    # Update existing employer profile
                                    employer_profile.company_name = employer_form.cleaned_data.get('company_name')
                                    employer_profile.company_id = employer_form.cleaned_data.get('company_id')
                                    employer_profile.phone_number = employer_form.cleaned_data.get('phone_number')
                                    employer_profile.save()
                                logger.info(f"{'Created' if created else 'Updated'} employer profile for {user.username}")
                            else:
                                # No profile exists, use our helper method
                                employer_profile = EmployerProfile.create_for_user(
                                    user=user,
                                    company_name=employer_form.cleaned_data.get('company_name'),
                                    company_id=employer_form.cleaned_data.get('company_id'),
                                    phone_number=employer_form.cleaned_data.get('phone_number')
                                )
                                logger.info(f"Created new employer profile for {user.username}")
                        except Exception as e:
                            logger.error(f"Error handling profiles: {str(e)}", exc_info=True)
                            raise
                            
                        # Verify the role was set correctly
                        user.refresh_from_db()
                        logger.info(f"Final role check: User {user.username} has role {user.userprofile.role}")
                        
                        # Log in the user
                        user.backend = 'django.contrib.auth.backends.ModelBackend'
                        login(request, user)
                        
                        # Final verification after login
                        logger.info(f"After login: User {user.username} has role {user.userprofile.role}")
                        
                except Exception as e:
                    logger.error(f"Error during employer registration: {str(e)}", exc_info=True)
                    messages.error(request, f"Registration error: {str(e)}")
                    return render(request, 'core/register_tailwind.html', {
                        'form': form,
                        'employer_form': employer_form
                    })
                
                messages.success(request, "Registration successful! You can now post jobs after admin approval.")
                return redirect('employer_dashboard')
            else:
                # Handle form errors
                logger.warning(f"Form validation errors: {form.errors} / {employer_form.errors}")
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{error}")
                for field, errors in employer_form.errors.items():
                    for error in errors:
                        messages.error(request, f"{error}")
                # Re-render the form with the employer form
                employer_form = EmployerRegistrationForm(request.POST)
        else:
            # Regular candidate registration
            form = RegistrationForm(request.POST)
            if form.is_valid():
                try:
                    with transaction.atomic():
                        # Create the user
                        user = form.save()
                        logger.info(f"Created candidate user {user.username}")
                        
                        # Create or get UserProfile with candidate role
                        # Using get_or_create to handle the case where signals already created the profile
                        profile, created = UserProfile.objects.get_or_create(
                            user=user,
                            defaults={'role': 'candidate'}
                        )
                        
                        # Make sure the role is set to candidate regardless
                        if not created and profile.role != 'candidate':
                            profile.role = 'candidate'
                            profile.save()
                            
                        logger.info(f"{'Created' if created else 'Using existing'} UserProfile with role 'candidate' for {user.username}")
                        
                        # Log in the user
                        user.backend = 'django.contrib.auth.backends.ModelBackend'
                        login(request, user)
                        
                        # Final verification after login
                        logger.info(f"After login: User {user.username} has role {user.userprofile.role}")
                except Exception as e:
                    logger.error(f"Error during candidate registration: {str(e)}", exc_info=True)
                    messages.error(request, f"Registration error: {str(e)}")
                    return render(request, 'core/register_tailwind.html', {
                        'form': form,
                        'employer_form': None
                    })
                
                messages.success(request, "Registration successful. Welcome to Jobsy!")
                return redirect('job_list')
            else:
                # Display form errors
                logger.warning(f"Form validation errors: {form.errors}")
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{error}")
    else:
        form = RegistrationForm()
        employer_form = EmployerRegistrationForm()
    
    return render(request, 'core/register_tailwind.html', {
        'form': form,
        'employer_form': employer_form
    }) 