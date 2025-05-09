from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from ..forms import RegistrationForm
from ..models import UserProfile

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
    
    return render(request, 'core/login.html', {'form': form})

def logout_view(request):
    """Handle user logout"""
    logout(request)
    return redirect('job_list')

def register(request):
    """Handle user registration"""
    if request.user.is_authenticated:
        return redirect('job_list')
    
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Create a UserProfile for the new user
            UserProfile.objects.create(
                user=user,
                role='candidate'
            )
            
            # Log the user in after registration
            login(request, user)
            messages.success(request, "Registration successful. Welcome to Jobsy!")
            return redirect('job_list')
        else:
            # Display form errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{error}")
    else:
        form = RegistrationForm()
    
    return render(request, 'core/register.html', {'form': form}) 