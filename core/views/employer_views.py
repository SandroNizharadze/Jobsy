from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.db.models import Count
from ..models import JobListing, EmployerProfile, JobApplication
from ..forms import JobListingForm, EmployerProfileForm
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

@login_required
@user_passes_test(is_employer)
def employer_home(request):
    """
    Display the employer dashboard home page
    """
    # Get the employer profile
    employer_profile = request.user.userprofile.employer_profile
    
    # Get statistics for employer's jobs
    job_stats = {
        'total': JobListing.objects.filter(employer=employer_profile).count(),
        'active': JobListing.objects.filter(employer=employer_profile, status='approved').count(),
        'pending': JobListing.objects.filter(employer=employer_profile, status='pending_review').count(),
        'applications': JobApplication.objects.filter(job__employer=employer_profile).count(),
    }
    
    # Recent applications
    recent_applications = JobApplication.objects.filter(
        job__employer=employer_profile
    ).order_by('-applied_at')[:5]
    
    context = {
        'employer_profile': employer_profile,
        'job_stats': job_stats,
        'recent_applications': recent_applications,
    }
    
    return render(request, 'core/employer_home.html', context)

@login_required
@user_passes_test(is_employer)
def employer_dashboard(request):
    """
    Display the employer dashboard with detailed analytics
    """
    # Get the employer profile
    employer_profile = request.user.userprofile.employer_profile
    
    # Get all jobs by this employer
    jobs = JobListing.objects.filter(employer=employer_profile)
    
    # Count applications per job
    job_applications = JobListing.objects.filter(
        employer=employer_profile
    ).annotate(application_count=Count('applications'))
    
    context = {
        'employer_profile': employer_profile,
        'jobs': jobs,
        'job_applications': job_applications,
    }
    
    return render(request, 'core/employer_dashboard.html', context)

@login_required
@user_passes_test(is_employer)
def employer_jobs(request):
    """
    Display all jobs posted by the employer
    """
    # Get the employer profile
    employer_profile = request.user.userprofile.employer_profile
    
    # Get all jobs by this employer
    jobs = JobListing.objects.filter(employer=employer_profile).order_by('-posted_at')
    
    context = {
        'jobs': jobs,
    }
    
    return render(request, 'core/employer_jobs.html', context)

@login_required
@user_passes_test(is_employer)
def post_job(request):
    """
    Handle job posting form submission
    """
    if request.method == 'POST':
        form = JobListingForm(request.POST)
        if form.is_valid():
            # Create the job but don't save to DB yet
            job = form.save(commit=False)
            
            # Set the employer and company
            employer_profile = request.user.userprofile.employer_profile
            job.employer = employer_profile
            job.company = employer_profile.company_name
            
            # Save to DB
            job.save()
            
            messages.success(request, "Job posting submitted for review!")
            return redirect('employer_jobs')
    else:
        form = JobListingForm()
    
    context = {
        'form': form,
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
        return redirect('employer_jobs')
    
    if request.method == 'POST':
        form = JobListingForm(request.POST, instance=job)
        if form.is_valid():
            # Update job but don't save yet
            updated_job = form.save(commit=False)
            
            # If the job was already approved and is being modified, set it back to pending review
            if job.status == 'approved':
                updated_job.status = 'pending_review'
                messages.info(request, "Your job has been updated and is pending review again.")
            
            # Save changes
            updated_job.save()
            
            return redirect('employer_jobs')
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
        return redirect('employer_jobs')
    
    # Delete the job
    job.delete()
    
    messages.success(request, "Job listing has been deleted.")
    return redirect('employer_jobs') 