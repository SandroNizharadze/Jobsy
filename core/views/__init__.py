# Import views to make them available from the views package
from .auth_views import login_view, logout_view, register
from .job_views import job_list, job_detail, apply_job
from .employer_views import (
    employer_home, employer_dashboard, employer_jobs, 
    post_job, edit_job, delete_job
)
from .profile_views import profile, remove_cv
from .admin_views import create_admin, assign_employer

# For backward compatibility
from .main import * 