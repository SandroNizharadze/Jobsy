from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.urls import reverse
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
from django.views.decorators.http import require_POST
from ..models import JobListing, UserProfile, EmployerProfile, JobApplication
from ..forms import UserProfileForm, EmployerProfileForm, JobListingForm, RegistrationForm
import logging
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Q, Count

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

def is_admin(user):
    return user.is_superuser or (hasattr(user, 'userprofile') and user.userprofile.role == 'admin')

def home_redirect(request):
    if request.user.is_authenticated and is_employer(request.user):
        return redirect('employer_home')
    return redirect('job_list')

def job_list(request):
    # Only show approved jobs to the public
    jobs = JobListing.objects.filter(status='approved').order_by('-posted_at')
    
    # Initialize filtering context variables
    filtered = False
    active_filters = {}
    filter_remove_urls = {}
    show_filters = 'show_filters' in request.GET
    
    # Search by title or company
    if 'search' in request.GET and request.GET['search']:
        search_term = request.GET['search']
        jobs = jobs.filter(
            Q(title__icontains=search_term) | 
            Q(company__icontains=search_term) |
            Q(description__icontains=search_term)
        )
        filtered = True
        active_filters['საძიებო სიტყვა'] = search_term
        filter_remove_urls['საძიებო სიტყვა'] = remove_from_query_string(request.GET, 'search')
    
    # Filter by location
    if 'location' in request.GET and request.GET['location']:
        location = request.GET['location']
        jobs = jobs.filter(location=location)
        filtered = True
        active_filters['ლოკაცია'] = location
        filter_remove_urls['ლოკაცია'] = remove_from_query_string(request.GET, 'location')
    
    # Filter by category
    if 'category' in request.GET and request.GET['category']:
        category = request.GET['category']
        jobs = jobs.filter(category=category)
        filtered = True
        active_filters['კატეგორია'] = category
        filter_remove_urls['კატეგორია'] = remove_from_query_string(request.GET, 'category')
    
    # Filter by experience
    if 'experience' in request.GET and request.GET['experience']:
        experience = request.GET['experience']
        jobs = jobs.filter(experience=experience)
        filtered = True
        active_filters['გამოცდილება'] = {
            'entry': 'დამწყები',
            'mid': 'საშუალო',
            'senior': 'პროფესიონალი'
        }.get(experience, experience)
        filter_remove_urls['გამოცდილება'] = remove_from_query_string(request.GET, 'experience')
    
    # Filter by minimum salary
    if 'salary_min' in request.GET and request.GET['salary_min'] and int(request.GET['salary_min']) > 0:
        salary_min = request.GET['salary_min']
        jobs = jobs.filter(salary_min__gte=salary_min)
        filtered = True
        active_filters['მინიმალური ანაზღაურება'] = f"₾ {salary_min}"
        filter_remove_urls['მინიმალური ანაზღაურება'] = remove_from_query_string(request.GET, 'salary_min')
    
    # Filter by job preferences (employment type)
    if 'job_preferences' in request.GET and request.GET['job_preferences']:
        preferences = request.GET['job_preferences'].split(',')
        jobs = jobs.filter(job_preferences__in=preferences)
        filtered = True
        active_filters['სამუშაოს ტიპი'] = ', '.join(preferences)
        filter_remove_urls['სამუშაოს ტიპი'] = remove_from_query_string(request.GET, 'job_preferences')
    
    # Get unique categories and locations for filter dropdowns
    all_categories = JobListing.objects.order_by('category').values_list('category', flat=True).distinct()
    all_locations = JobListing.objects.order_by('location').values_list('location', flat=True).distinct()
    
    # Get job preferences for checkboxes
    job_preferences = []
    if 'job_preferences' in request.GET:
        job_preferences = request.GET['job_preferences'].split(',')
    
    # Only use pagination on the main page (when filters are NOT being shown)
    if not show_filters:
        # Pagination for main page only
        paginator = Paginator(jobs, 9)  # Show 9 jobs per page
        page_number = request.GET.get('page', 1)
        try:
            jobs_page = paginator.page(page_number)
        except (PageNotAnInteger, EmptyPage):
            jobs_page = paginator.page(1)
    else:
        # No pagination when filters are shown - display all jobs
        jobs_page = jobs
    
    is_employer_user = is_employer(request.user)
    
    context = {
        'jobs': jobs_page,
        'is_employer': is_employer_user,
        'categories': all_categories,
        'locations': all_locations,
        'job_preferences': job_preferences,
        'filtered': filtered,
        'active_filters': active_filters,
        'filter_remove_urls': filter_remove_urls,
        'show_filters': show_filters,
    }
    
    # If this is an AJAX request, only render the job listings partial
    if request.GET.get('ajax') == '1':
        return render(request, 'core/job_list.html', context)
    else:
        return render(request, 'core/job_list.html', context)

def remove_from_query_string(query_dict, param):
    """Helper function to remove a parameter from query string"""
    query_dict = query_dict.copy()
    query_dict.pop(param, None)
    return '?' + query_dict.urlencode() if query_dict else '?'

def login_view(request):
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
    logout(request)
    return redirect('job_list')

def register(request):
    if request.user.is_authenticated:
        return redirect('job_list')
    
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Check if UserProfile already exists before creating
            user_profile, created = UserProfile.objects.get_or_create(
                user=user,
                defaults={'role': 'user'}  # Only set default role when creating new profile
            )
            
            # Specify the authentication backend when logging in
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            login(request, user)
            return redirect('job_list')
    else:
        form = RegistrationForm()
    
    return render(request, 'core/register.html', {'form': form})

@login_required
def profile(request):
    user_profile = request.user.userprofile
    
    # Show a single success message if CV was removed
    if request.GET.get('cv_removed') == '1':
        messages.success(request, "Your CV has been removed.")
    
    employer_form = None  # Always define this, even for candidates

    if request.method == 'POST':
        if is_employer(request.user):
            employer_profile, created = EmployerProfile.objects.get_or_create(user_profile=user_profile)
            user_form = UserProfileForm(request.POST, request.FILES, instance=user_profile)
            employer_form = EmployerProfileForm(request.POST, request.FILES, instance=employer_profile)
            
            # AJAX CV upload
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                if user_form.is_valid() and employer_form.is_valid():
                    user_form.save()
                    employer_form.save()
                    return JsonResponse({
                        'success': True,
                        'cv_url': user_profile.cv.url if user_profile.cv else '',
                        'remove_cv_url': reverse('remove_cv')
                    })
                else:
                    errors = []
                    for field, error_list in user_form.errors.items():
                        errors.extend(error_list)
                    for field, error_list in employer_form.errors.items():
                        errors.extend(error_list)
                    return JsonResponse({'success': False, 'errors': ' '.join(errors)}, status=400)

            if user_form.is_valid() and employer_form.is_valid():
                user_form.save()
                employer_form.save()
                # Only show profile updated message if not redirected from CV removal
                if not request.GET.get('cv_removed'):
                    messages.success(request, "Profile updated successfully!")
                return redirect('profile')
            else:
                messages.error(request, "Please correct the errors below.")
        else:
            user_form = UserProfileForm(request.POST, request.FILES, instance=user_profile)
            # AJAX CV upload
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                if user_form.is_valid():
                    user_form.save()
                    return JsonResponse({
                        'success': True,
                        'cv_url': user_profile.cv.url if user_profile.cv else '',
                        'remove_cv_url': reverse('remove_cv')
                    })
                else:
                    errors = []
                    for field, error_list in user_form.errors.items():
                        errors.extend(error_list)
                    return JsonResponse({'success': False, 'errors': ' '.join(errors)}, status=400)
            if user_form.is_valid():
                user_form.save()
                if not request.GET.get('cv_removed'):
                    messages.success(request, "Profile updated successfully!")
                return redirect('profile')
            else:
                messages.error(request, "Please correct the errors below.")
            employer_form = None  # Explicitly set for candidates
    else:
        user_form = UserProfileForm(instance=user_profile)
        if is_employer(request.user):
            employer_profile, created = EmployerProfile.objects.get_or_create(user_profile=user_profile)
            employer_form = EmployerProfileForm(instance=employer_profile)
        else:
            employer_form = None
    
    return render(request, 'core/profile.html', {
        'user_form': user_form,
        'employer_form': employer_form,
        'is_employer': is_employer(request.user),
    })

@login_required
@user_passes_test(is_employer)
def employer_jobs(request):
    employer_profile = request.user.userprofile.employer_profile
    jobs = JobListing.objects.filter(employer=employer_profile).order_by('-posted_at')
    
    if request.method == 'POST':
        form = JobListingForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.employer = employer_profile
            job.company = employer_profile.company_name
            job.save()
            messages.success(request, "Job posted successfully!")
            return redirect('employer_jobs')
    else:
        form = JobListingForm()
    
    return render(request, 'core/employer_jobs.html', {
        'jobs': jobs,
        'form': form
    })

@login_required
def employer_dashboard(request):
    if not is_employer(request.user):
        messages.error(request, "You don't have permission to access the employer dashboard. Please contact an administrator to get employer access.")
        return redirect('job_list')
    
    try:
        employer_profile = request.user.userprofile.employer_profile
        jobs = JobListing.objects.filter(employer=employer_profile).order_by('-posted_at')
        form = JobListingForm()
        
        return render(request, 'core/employer_dashboard.html', {
            'jobs': jobs,
            'form': form,
            'employer_profile': employer_profile
        })
    except EmployerProfile.DoesNotExist:
        messages.error(request, "Your employer profile is not properly set up. Please contact an administrator.")
        return redirect('job_list')

@login_required
def post_job(request):
    if not is_employer(request.user):
        messages.error(request, "Only employers can post jobs. Please contact an administrator to get employer access.")
        return redirect('job_list')
    
    if request.method == 'POST':
        form = JobListingForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.employer = request.user.userprofile.employer_profile
            job.company = request.user.userprofile.employer_profile.company_name
            job.status = 'pending_review'
            job.admin_feedback = ''
            job.save()
            messages.success(request, "Job submitted for review! An admin will review and approve it soon.")
            return redirect('employer_dashboard')
        else:
            messages.error(request, "Please correct the errors below.")
            return redirect('employer_dashboard')
    
    return redirect('employer_dashboard')

@login_required
def edit_job(request, job_id):
    if not is_employer(request.user):
        messages.error(request, "Only employers can edit jobs. Please contact an administrator to get employer access.")
        return redirect('job_list')
    
    job = get_object_or_404(JobListing, id=job_id)
    if job.employer != request.user.userprofile.employer_profile:
        raise PermissionDenied("You can only edit your own job listings.")
    
    if request.method == 'POST':
        form = JobListingForm(request.POST, instance=job)
        if form.is_valid():
            form.save()
            messages.success(request, "Job updated successfully!")
            return redirect('employer_dashboard')
        else:
            messages.error(request, "Please correct the errors below.")
            return redirect('employer_dashboard')
    
    # For GET requests, return job details as JSON
    return JsonResponse({
        'id': job.id,
        'title': job.title,
        'description': job.description,
        'interests': job.interests,
        'fields': job.fields,
        'experience': job.experience,
        'job_preferences': job.job_preferences,
    })

@login_required
@require_POST
def delete_job(request, job_id):
    if not is_employer(request.user):
        messages.error(request, "Only employers can delete jobs. Please contact an administrator to get employer access.")
        return redirect('job_list')
    
    job = get_object_or_404(JobListing, id=job_id)
    if job.employer != request.user.userprofile.employer_profile:
        raise PermissionDenied("You can only delete your own job listings.")
    
    job.delete()
    messages.success(request, "Job deleted successfully!")
    return JsonResponse({'status': 'success'})

@login_required
@user_passes_test(is_admin)
def assign_employer(request, user_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    user_profile = get_object_or_404(UserProfile, user_id=user_id)
    user_profile.role = 'employer'
    user_profile.save()
    
    # Create employer profile
    EmployerProfile.objects.get_or_create(user_profile=user_profile)
    
    messages.success(request, f"{user_profile.user.get_full_name()} has been assigned as an employer.")
    return JsonResponse({'status': 'success'})

def job_detail(request, job_id):
    job = get_object_or_404(JobListing, id=job_id)
    is_employer_user = request.user.is_authenticated and is_employer(request.user)
    is_job_owner = is_employer_user and job.employer == request.user.userprofile.employer_profile if is_employer_user else False
    
    # Get similar jobs based on fields and interests, only show approved
    similar_jobs = JobListing.objects.exclude(id=job_id).filter(
        fields=job.fields,
        interests=job.interests,
        status='approved'
    ).order_by('-posted_at')[:5]
    
    return render(request, 'core/job_detail.html', {
        'job': job,
        'is_employer': is_employer_user,
        'is_job_owner': is_job_owner,
        'similar_jobs': similar_jobs,
    })

def apply_job(request, job_id):
    job = get_object_or_404(JobListing, id=job_id)

    # Check if user is employer - employers shouldn't apply for jobs
    if is_employer(request.user):
        messages.error(request, "Employers cannot apply for jobs.")
        return redirect('job_detail', job_id=job_id)

    user_profile = request.user.userprofile if request.user.is_authenticated else None

    # Prevent duplicate applications for authenticated users
    if request.user.is_authenticated and JobApplication.objects.filter(job=job, user=request.user).exists():
        messages.error(request, "You have already applied to this job.")
        return redirect('job_detail', job_id=job_id)

    if request.method == 'POST':
        if request.user.is_authenticated:
            cover_letter = request.POST.get('cover_letter', '').strip()
            if user_profile and user_profile.cv:
                JobApplication.objects.create(
                    job=job,
                    user=request.user,
                    resume=user_profile.cv,
                    cover_letter=cover_letter
                )
                if not cover_letter:
                    messages.success(request, "Your application was submitted. (Cover letter was optional and not provided.)")
                else:
                    messages.success(request, "Your application was submitted successfully.")
                return redirect('job_detail', job_id=job_id)
            else:
                resume = request.FILES.get('resume')
                if not resume:
                    messages.error(request, "Please provide a resume.")
                    return redirect('job_detail', job_id=job_id)
                JobApplication.objects.create(
                    job=job,
                    user=request.user,
                    cover_letter=cover_letter,
                    resume=resume
                )
                messages.success(request, "Your application has been submitted successfully!")
                return redirect('job_detail', job_id=job_id)
        else:
            applicant_name = request.POST.get('applicant_name', '').strip()
            applicant_email = request.POST.get('applicant_email', '').strip()
            cover_letter = request.POST.get('cover_letter', '').strip()
            resume = request.FILES.get('resume')
            
            if not applicant_name or not applicant_email or not resume:
                messages.error(request, "Please provide your name, email, and resume.")
                return redirect('job_detail', job_id=job_id)
                
            JobApplication.objects.create(
                job=job,
                guest_name=applicant_name,
                guest_email=applicant_email,
                cover_letter=cover_letter,
                resume=resume,
                status='pending'
            )
            messages.success(request, "Your application has been submitted successfully!")
            return redirect('job_detail', job_id=job_id)
    return redirect('job_detail', job_id=job_id)

@login_required
@user_passes_test(is_employer)
def employer_home(request):
    employer_profile = request.user.userprofile.employer_profile
    jobs = JobListing.objects.filter(employer=employer_profile)
    total_jobs = jobs.count()
    total_applicants = JobApplication.objects.filter(job__in=jobs).count()
    recent_applicants = JobApplication.objects.filter(job__in=jobs).order_by('-applied_at')[:5]
    jobs_expiring_soon = jobs.order_by('posted_at')[:3]
    
    # Applicants per job
    avg_applicants = round(total_applicants / total_jobs, 3) if total_jobs > 0 else 0

    context = {
        'employer_profile': employer_profile,
        'total_jobs': total_jobs,
        'total_applicants': total_applicants,
        'recent_applicants': recent_applicants,
        'jobs_expiring_soon': jobs_expiring_soon,
        'avg_applicants': avg_applicants,
    }
    return render(request, 'core/employer_home.html', context)

@login_required
@require_POST
def remove_cv(request):
    user_profile = request.user.userprofile
    if user_profile.role != 'candidate':
        messages.error(request, "Only candidates can remove their CV.")
        return redirect('profile')
    user_profile.cv.delete(save=False)
    user_profile.cv = None
    user_profile.save()
    # Use Django's redirect with a GET param to show a single success message
    return redirect(f'{reverse("profile")}?cv_removed=1')

def create_admin(request, secret_key):
    """
    Creates an admin user if the secret key matches
    """
    if secret_key != "3!rk4uta2qj@xis7_^sv8u=34*pd$-%b3&!fd)":
        return JsonResponse({"error": "Invalid secret key"}, status=403)
    
    try:
        admin_username = 'admin'
        admin_email = 'admin@example.com'
        admin_password = 'admin123'
        
        # Create or update the admin user
        try:
            admin_user = User.objects.get(username=admin_username)
            admin_user.is_staff = True
            admin_user.is_superuser = True
            admin_user.set_password(admin_password)
            admin_user.save()
            status = f"Admin user '{admin_username}' updated."
        except User.DoesNotExist:
            User.objects.create_superuser(
                username=admin_username,
                email=admin_email,
                password=admin_password
            )
            status = f"Admin user '{admin_username}' created."
        
        # Ensure UserProfile exists
        admin_user = User.objects.get(username=admin_username)
        profile, created = UserProfile.objects.get_or_create(
            user=admin_user,
            defaults={'role': 'admin'}
        )
        profile_status = f"UserProfile {'created' if created else 'exists'} for '{admin_username}'."
        
        return JsonResponse({
            "success": True,
            "status": status,
            "profile_status": profile_status
        })
    except Exception as e:
        return JsonResponse({
            "error": str(e)
        }, status=500)