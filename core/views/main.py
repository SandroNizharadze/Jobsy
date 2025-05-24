"""
Legacy module that re-exports view functions from modular files.
This maintains backward compatibility while transitioning to a modular structure.
"""

from django.shortcuts import redirect
from .auth_views import login_view, logout_view, register, is_employer
from .job_views import job_list, job_detail, apply_job, remove_from_query_string
from .employer_views import (
    employer_home, employer_dashboard,
    post_job, edit_job, delete_job,
    job_applications, update_application_status,
    get_job_details
)
from .profile_views import profile, remove_cv
from .admin_views import create_admin, assign_employer, is_admin

# Re-export utility functions for backward compatibility
def home_redirect(request):
    """Redirect to appropriate home page based on user role"""
    if request.user.is_authenticated:
        return redirect('profile')
    return redirect('job_list')

# Import required modules to support the above functions
from django.shortcuts import redirect, render

# Import the pricing models
from core.models import PricingPackage

def pricing(request):
    """Display the pricing packages page"""
    pricing_packages = PricingPackage.objects.filter(is_active=True).prefetch_related('features').order_by('display_order')
    return render(request, 'core/pricing_tailwind.html', {'pricing_packages': pricing_packages})