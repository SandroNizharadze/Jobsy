"""
Legacy module that re-exports view functions from modular files.
This maintains backward compatibility while transitioning to a modular structure.
"""

from .auth_views import login_view, logout_view, register, is_employer
from .job_views import job_list, job_detail, apply_job, remove_from_query_string
from .employer_views import (
    employer_home, employer_dashboard, employer_jobs, 
    post_job, edit_job, delete_job
)
from .profile_views import profile, remove_cv
from .admin_views import create_admin, assign_employer, is_admin

# Re-export utility functions for backward compatibility
def home_redirect(request):
    """Redirect to appropriate home page based on user role"""
    if request.user.is_authenticated and is_employer(request.user):
        return redirect('employer_home')
    return redirect('job_list')

# Import required modules to support the above functions
from django.shortcuts import redirect