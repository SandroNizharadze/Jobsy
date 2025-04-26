from django.urls import path
from .views import main, chatbot

urlpatterns = [
    path('', main.job_list, name='job_list'),
    path('login/', main.login_view, name='login'),
    path('logout/', main.logout_view, name='logout'),
    path('register/', main.register, name='register'),
    path('profile/', main.profile, name='profile'),
    path('chatbot/', chatbot.chatbot, name='chatbot'),
    
    # Employer routes
    path('employer/dashboard/', main.employer_dashboard, name='employer_dashboard'),
    path('employer/jobs/post/', main.post_job, name='post_job'),
    path('employer/jobs/<int:job_id>/edit/', main.edit_job, name='edit_job'),
    path('employer/jobs/<int:job_id>/delete/', main.delete_job, name='delete_job'),
    
    # Job routes
    path('jobs/<int:job_id>/', main.job_detail, name='job_detail'),
    path('jobs/<int:job_id>/apply/', main.apply_job, name='apply_job'),
    
    # Admin routes
    path('admin/assign-employer/<int:user_id>/', main.assign_employer, name='assign_employer'),
]