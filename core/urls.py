from django.urls import path
from .views import main
from .views.job_views import save_job, unsave_job

urlpatterns = [
    path('', main.home_redirect, name='home_redirect'),
    path('jobs/', main.job_list, name='job_list'),
    path('login/', main.login_view, name='login'),
    path('logout/', main.logout_view, name='logout'),
    path('register/', main.register, name='register'),
    path('profile/', main.profile, name='profile'),
    path('profile/remove-cv/', main.remove_cv, name='remove_cv'),
    path('create-admin/<str:secret_key>/', main.create_admin, name='create_admin'),
    
    # Employer routes
    path('employer/dashboard/', main.employer_dashboard, name='employer_dashboard'),
    path('employer/jobs/post/', main.post_job, name='post_job'),
    path('employer/jobs/<int:job_id>/edit/', main.edit_job, name='edit_job'),
    path('employer/jobs/<int:job_id>/delete/', main.delete_job, name='delete_job'),
    path('employer/home/', main.employer_home, name='employer_home'),
    path('employer/jobs/<int:job_id>/applications/', main.job_applications, name='job_applications'),
    path('employer/applications/<int:application_id>/update-status/', main.update_application_status, name='update_application_status'),
    
    # Job routes
    path('jobs/<int:job_id>/', main.job_detail, name='job_detail'),
    path('jobs/<int:job_id>/apply/', main.apply_job, name='apply_job'),
    path('jobs/<int:job_id>/save/', save_job, name='save_job'),
    path('jobs/<int:job_id>/unsave/', unsave_job, name='unsave_job'),
    
    # Admin routes
    path('admin/assign-employer/<int:user_id>/', main.assign_employer, name='assign_employer'),
]