from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from ..models import JobListing, JobApplication
from ..forms import JobListingForm
import logging

logger = logging.getLogger(__name__)

def remove_from_query_string(query_dict, param):
    """Helper function to remove a parameter from query string"""
    query_dict = query_dict.copy()
    query_dict.pop(param, None)
    return '?' + query_dict.urlencode() if query_dict else '?'

def job_list(request):
    """
    Display the job listing page with filtering options
    """
    # Only show approved jobs to the public
    # Use select_related to fetch employer in the same query
    jobs = JobListing.objects.filter(status='approved').select_related('employer').order_by('-posted_at')
    
    # Initialize filtering context variables
    filtered = False
    active_filters = {}
    filter_remove_urls = {}
    show_filters = 'show_filters' in request.GET
    
    # Apply filters based on request parameters
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
    
    if 'location' in request.GET and request.GET['location']:
        location = request.GET['location']
        jobs = jobs.filter(location=location)
        filtered = True
        active_filters['ლოკაცია'] = location
        filter_remove_urls['ლოკაცია'] = remove_from_query_string(request.GET, 'location')
    
    if 'category' in request.GET and request.GET['category']:
        category = request.GET['category']
        jobs = jobs.filter(category=category)
        filtered = True
        active_filters['კატეგორია'] = category
        filter_remove_urls['კატეგორია'] = remove_from_query_string(request.GET, 'category')
    
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
    
    if 'salary_min' in request.GET and request.GET['salary_min'] and int(request.GET['salary_min']) > 0:
        salary_min = request.GET['salary_min']
        jobs = jobs.filter(salary_min__gte=salary_min)
        filtered = True
        active_filters['მინიმალური ანაზღაურება'] = f"₾ {salary_min}"
        filter_remove_urls['მინიმალური ანაზღაურება'] = remove_from_query_string(request.GET, 'salary_min')
    
    if 'job_preferences' in request.GET and request.GET['job_preferences']:
        preferences = request.GET['job_preferences'].split(',')
        jobs = jobs.filter(job_preferences__in=preferences)
        filtered = True
        active_filters['სამუშაოს ტიპი'] = ', '.join(preferences)
        filter_remove_urls['სამუშაოს ტიპი'] = remove_from_query_string(request.GET, 'job_preferences')
    
    # Get unique categories and locations for filter dropdowns - use distinct() with values_list for optimization
    all_categories = JobListing.objects.filter(status='approved').values_list('category', flat=True).distinct()
    all_locations = JobListing.objects.filter(status='approved').values_list('location', flat=True).distinct()
    
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
    
    # Check if user is an employer
    is_employer_user = False
    if request.user.is_authenticated:
        try:
            is_employer_user = (request.user.userprofile.role == 'employer' and 
                               hasattr(request.user.userprofile, 'employer_profile'))
        except:
            pass
    
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

def job_detail(request, job_id):
    """
    Display details for a specific job listing
    """
    # Use select_related to fetch employer in the same query
    job = get_object_or_404(JobListing.objects.select_related('employer'), id=job_id, status='approved')
    
    # Get similar jobs based on category and experience, only show approved
    similar_jobs = JobListing.objects.filter(
        status='approved',
        category=job.category
    ).exclude(id=job_id).select_related('employer').order_by('-posted_at')[:5]
    
    context = {
        'job': job,
        'similar_jobs': similar_jobs,
    }
    return render(request, 'core/job_detail.html', context)

def apply_job(request, job_id):
    """
    Handle job application submission
    """
    # Use select_related to fetch employer in the same query
    job = get_object_or_404(JobListing.objects.select_related('employer'), id=job_id, status='approved')
    
    if request.method == 'POST':
        # Check if user is authenticated
        if request.user.is_authenticated:
            # Check if user has already applied
            existing_application = JobApplication.objects.filter(
                job=job,
                user=request.user
            ).exists()
            
            if existing_application:
                messages.warning(request, "You have already applied for this job.")
                return redirect('job_detail', job_id=job.id)
            
            # Process form data
            cover_letter = request.POST.get('cover_letter', '')
            resume_file = request.FILES.get('resume')
            
            if not cover_letter or not resume_file:
                messages.error(request, "Both cover letter and resume are required.")
                return redirect('job_detail', job_id=job.id)
            
            # Create application
            application = JobApplication.objects.create(
                job=job,
                user=request.user,
                cover_letter=cover_letter,
                resume=resume_file
            )
            
            messages.success(request, "Your application has been submitted successfully!")
            return redirect('job_detail', job_id=job.id)
        else:
            # Process guest application
            guest_name = request.POST.get('guest_name', '')
            guest_email = request.POST.get('guest_email', '')
            cover_letter = request.POST.get('cover_letter', '')
            resume_file = request.FILES.get('resume')
            
            if not all([guest_name, guest_email, cover_letter, resume_file]):
                messages.error(request, "All fields are required for guest application.")
                return redirect('job_detail', job_id=job.id)
            
            # Create guest application
            application = JobApplication.objects.create(
                job=job,
                guest_name=guest_name,
                guest_email=guest_email,
                cover_letter=cover_letter,
                resume=resume_file
            )
            
            messages.success(request, "Your application has been submitted successfully! Consider creating an account for better job tracking.")
            return redirect('job_detail', job_id=job.id)
    
    # If not POST, redirect to job detail page
    return redirect('job_detail', job_id=job.id) 