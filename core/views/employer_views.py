from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.db.models import Count, Prefetch, Q, Case, When, Value, IntegerField
from ..models import JobListing, EmployerProfile, JobApplication, UserProfile
from ..forms import JobListingForm, EmployerProfileForm
import logging
from django.utils import timezone
from datetime import timedelta
from django.http import HttpResponseForbidden, JsonResponse

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

@login_required
@user_passes_test(is_employer)
def employer_home(request):
    """
    Display the employer metrics/summary page (not job management)
    """
    employer_profile = request.user.userprofile.employer_profile
    jobs = JobListing.objects.filter(employer=employer_profile)

    # Metrics
    total_jobs = jobs.count()
    active_jobs = jobs.filter(status='approved').count()
    total_applicants = JobApplication.objects.filter(job__employer=employer_profile).count()
    unread_applicants = JobApplication.objects.filter(job__employer=employer_profile, is_read=False).count()
    avg_applicants = round(total_applicants / total_jobs, 2) if total_jobs > 0 else 0
    # Jobs expiring soon (example: jobs expiring in next 7 days)
    soon = timezone.now() + timedelta(days=7)
    jobs_expiring_soon = jobs.filter(expiry_date__lte=soon, expiry_date__gte=timezone.now()) if hasattr(jobs.first(), 'expiry_date') else []
    
    # All jobs for this employer ordered by most recent first
    all_jobs = jobs.order_by('-posted_at')
    
    # Sort jobs by status (approved first, then pending review, then rejected)
    all_jobs = jobs.annotate(
        status_order=Case(
            When(status='approved', then=Value(1)),
            When(status='pending_review', then=Value(2)),
            When(status='rejected', then=Value(3)),
            default=Value(4),
            output_field=IntegerField(),
        ),
        unread_applications_count=Count(
            'applications',
            filter=Q(applications__is_read=False)
        )
    ).order_by('status_order', '-posted_at')
    
    # Recent applicants (last 5)
    recent_applicants = JobApplication.objects.filter(
        job__employer=employer_profile
    ).select_related('job', 'user').order_by('-applied_at')[:5]

    context = {
        'employer_profile': employer_profile,
        'total_jobs': total_jobs,
        'active_jobs': active_jobs,
        'total_applicants': total_applicants,
        'unread_applicants': unread_applicants,
        'avg_applicants': avg_applicants,
        'jobs_expiring_soon': jobs_expiring_soon,
        'all_jobs': all_jobs,
        'recent_applicants': recent_applicants,
    }
    return render(request, 'core/employer_home.html', context)

@login_required
@user_passes_test(is_employer)
def employer_dashboard(request):
    """
    Display the employer dashboard with detailed analytics
    """
    employer_profile = request.user.userprofile.employer_profile

    # All jobs for this employer with application counts
    jobs = JobListing.objects.filter(employer=employer_profile).annotate(
        applications_count=Count('applications')
    )

    # Metrics
    active_jobs = jobs.filter(status='approved').count()
    total_applicants = JobApplication.objects.filter(job__employer=employer_profile).count()
    avg_applicants = (
        total_applicants / active_jobs if active_jobs > 0 else 0
    )
    # Jobs expiring soon (example: jobs expiring in next 7 days)
    soon = timezone.now() + timedelta(days=7)
    jobs_expiring_soon = jobs.filter(expiry_date__lte=soon, expiry_date__gte=timezone.now()).count() if hasattr(jobs.first(), 'expiry_date') else 0

    # Recent applicants (last 5)
    recent_applicants = JobApplication.objects.filter(
        job__employer=employer_profile
    ).select_related('user', 'job').order_by('-applied_at')[:5]

    context = {
        'employer_profile': employer_profile,
        'jobs': jobs,
        'active_jobs': active_jobs,
        'total_applicants': total_applicants,
        'avg_applicants': avg_applicants,
        'jobs_expiring_soon': jobs_expiring_soon,
        'recent_applicants': recent_applicants,
    }
    return render(request, 'core/employer_dashboard.html', context)

@login_required
@user_passes_test(is_employer)
def post_job(request):
    """
    Handle job posting form submission
    """
    # Get premium level from URL parameter if available
    premium_level = request.GET.get('premium_level', 'standard')
    
    # Validate premium level value
    if premium_level not in ['standard', 'premium', 'premium_plus']:
        premium_level = 'standard'
    
    if request.method == 'POST':
        form = JobListingForm(request.POST)
        if form.is_valid():
            # Create the job but don't save to DB yet
            job = form.save(commit=False)
            
            # Set the employer and company
            employer_profile = request.user.userprofile.employer_profile
            job.employer = employer_profile
            job.company = employer_profile.company_name
            
            # Ensure georgian_language_only is set
            if job.georgian_language_only is None:
                job.georgian_language_only = False
            
            # Save to DB
            job.save()
            
            messages.success(request, "Job posting submitted for review!")
            return redirect('employer_dashboard')
    else:
        # Initialize form with premium level from URL
        form = JobListingForm(initial={'premium_level': premium_level})
    
    context = {
        'form': form,
        'selected_premium_level': premium_level,
    }
    
    return render(request, 'core/post_job.html', context)

@login_required
@user_passes_test(is_employer)
def edit_job(request, job_id):
    """
    Handle editing of an existing job listing
    """
    # Get the job and verify ownership
    job = get_object_or_404(JobListing, id=job_id)
    employer_profile = request.user.userprofile.employer_profile
    
    if job.employer != employer_profile:
        messages.error(request, "You don't have permission to edit this job.")
        return redirect('employer_dashboard')
    
    if request.method == 'POST':
        form = JobListingForm(request.POST, instance=job)
        if form.is_valid():
            # Update job but don't save yet
            updated_job = form.save(commit=False)
            
            # If the job was already approved and is being modified, set it back to pending review
            if job.status == 'approved':
                updated_job.status = 'pending_review'
                messages.info(request, "Your job has been updated and is pending review again.")
            
            # Ensure georgian_language_only is set
            if updated_job.georgian_language_only is None:
                updated_job.georgian_language_only = False
            
            # Save changes
            updated_job.save()
            
            return redirect('employer_dashboard')
    else:
        form = JobListingForm(instance=job)
    
    context = {
        'form': form,
        'job': job,
    }
    
    return render(request, 'core/edit_job.html', context)

@login_required
@user_passes_test(is_employer)
@require_POST
def delete_job(request, job_id):
    """
    Handle deletion of a job listing
    """
    # Get the job and verify ownership
    job = get_object_or_404(JobListing, id=job_id)
    employer_profile = request.user.userprofile.employer_profile
    
    if job.employer != employer_profile:
        messages.error(request, "You don't have permission to delete this job.")
        return redirect('employer_dashboard')
    
    # Delete the job
    job.delete()
    
    messages.success(request, "Job listing has been deleted.")
    return redirect('employer_dashboard')

@login_required
@user_passes_test(is_employer)
def job_applications(request, job_id):
    """
    Display all applications for a specific job
    """
    # Get the job and verify ownership
    job = get_object_or_404(JobListing, id=job_id)
    employer_profile = request.user.userprofile.employer_profile
    
    if job.employer != employer_profile:
        messages.error(request, "You don't have permission to view applications for this job.")
        return redirect('employer_dashboard')
    
    # Get applications for this job
    applications = JobApplication.objects.filter(job=job).select_related('user', 'job')
    
    # Apply filters if provided
    if 'status' in request.GET and request.GET['status']:
        applications = applications.filter(status=request.GET['status'])
    
    if 'search' in request.GET and request.GET['search']:
        search_query = request.GET['search']
        applications = applications.filter(
            Q(user__username__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(guest_name__icontains=search_query) |
            Q(guest_email__icontains=search_query)
        )
    
    # Sort applications by status with custom order
    applications = applications.annotate(
        status_order=Case(
            When(status='გასაუბრება', then=Value(1)),     # Interview - first priority
            When(status='განხილვის_პროცესში', then=Value(2)),  # In review - third priority
            When(status='რეზერვი', then=Value(3)),        # Reserve - second priority
            default=Value(4),
            output_field=IntegerField(),
        )
    ).order_by('status_order', '-applied_at')
    
    # Mark all applications as read
    unread_applications = applications.filter(is_read=False)
    if unread_applications.exists():
        unread_applications.update(is_read=True)
    
    context = {
        'job': job,
        'applications': applications,
    }
    
    return render(request, 'core/employer_applications.html', context)

@login_required
@user_passes_test(is_employer)
@require_POST
def update_application_status(request, application_id):
    """
    Update the status of a job application
    """
    # Get the application and verify permission
    application = get_object_or_404(JobApplication, id=application_id)
    employer_profile = request.user.userprofile.employer_profile
    
    # Check if the application belongs to a job owned by this employer
    if application.job.employer != employer_profile:
        return HttpResponseForbidden("You don't have permission to update this application.")
    
    # Update the status
    new_status = request.POST.get('status')
    if new_status in dict(JobApplication.STATUS_CHOICES):
        application.status = new_status
        application.save()
        messages.success(request, "Application status updated successfully.")
    else:
        messages.error(request, "Invalid status value provided.")
    
    # Redirect back to the applications page
    return redirect('job_applications', job_id=application.job.id) 

@login_required
@user_passes_test(is_employer)
def get_job_details(request, job_id):
    """
    API endpoint to return job details in JSON format
    """
    # Get the job and verify ownership
    job = get_object_or_404(JobListing, id=job_id)
    employer_profile = request.user.userprofile.employer_profile
    
    if job.employer != employer_profile:
        return JsonResponse({"error": "You don't have permission to edit this job."}, status=403)
    
    # Return job details as JSON
    job_data = {
        'title': job.title,
        'description': job.description,
        'location': job.location,
        'category': job.category,
        'salary_min': job.salary_min,
        'salary_max': job.salary_max,
        'salary_type': job.salary_type,
        'experience': job.experience,
        'job_preferences': job.job_preferences,
        'considers_students': job.considers_students,
        'georgian_language_only': job.georgian_language_only,
        'premium_level': job.premium_level,
    }
    
    return JsonResponse(job_data) 