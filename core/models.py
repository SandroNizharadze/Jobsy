from django.db import models
from django.contrib.auth.models import User

class JobListing(models.Model):
    title = models.CharField(max_length=200)
    company = models.CharField(max_length=100)
    description = models.TextField()
    interests = models.CharField(max_length=200, help_text="Required skills or interests", blank=True)
    fields = models.CharField(max_length=200, help_text="Relevant fields", blank=True)
    experience = models.CharField(max_length=100, choices=[
        ('entry-level', 'Entry Level'),
        ('junior', 'Junior'),
        ('mid-level', 'Mid-Level'),
        ('senior', 'Senior'),
        ('lead', 'Lead/Principal'),
    ], blank=True)
    job_preferences = models.CharField(max_length=200, help_text="Job type preferences (e.g., remote, full-time)", blank=True)
    employer = models.ForeignKey('EmployerProfile', on_delete=models.CASCADE, related_name='job_listings', null=True, blank=True)
    posted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-posted_at']

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('user', 'Job Seeker'),
        ('employer', 'Employer'),
        ('admin', 'Admin'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    interests = models.CharField(max_length=200, blank=True, help_text="E.g., AI, web development, cybersecurity")
    fields = models.CharField(max_length=200, blank=True, help_text="E.g., software engineering, data science")
    experience = models.CharField(max_length=100, blank=True, choices=[
        ('entry-level', 'Entry Level'),
        ('junior', 'Junior'),
        ('mid-level', 'Mid-Level'),
        ('senior', 'Senior'),
        ('lead', 'Lead/Principal'),
    ])
    job_preferences = models.CharField(max_length=200, blank=True, help_text="E.g., remote, full-time, startup")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

    def is_complete(self):
        return all([
            self.interests.strip() != '',
            self.fields.strip() != '',
            self.experience.strip() != '',
            self.job_preferences.strip() != '',
        ])

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        old_instance = None if is_new else UserProfile.objects.get(pk=self.pk)
        
        # Save the profile first
        super().save(*args, **kwargs)
        
        # If role was changed to employer or this is a new employer profile
        if (is_new and self.role == 'employer') or (not is_new and old_instance.role != 'employer' and self.role == 'employer'):
            # Create employer profile if it doesn't exist
            from .models import EmployerProfile
            EmployerProfile.objects.get_or_create(
                user_profile=self,
                defaults={
                    'company_name': f"{self.user.get_full_name()}'s Company",
                    'company_description': 'Company description not set',
                    'industry': 'Not specified',
                    'location': 'Not specified',
                    'company_size': '1-10'
                }
            )

class EmployerProfile(models.Model):
    user_profile = models.OneToOneField(UserProfile, on_delete=models.CASCADE, related_name='employer_profile')
    company_name = models.CharField(max_length=200)
    company_website = models.URLField(blank=True)
    company_description = models.TextField()
    company_logo = models.ImageField(upload_to='company_logos/', null=True, blank=True)
    company_size = models.CharField(max_length=50, choices=[
        ('1-10', '1-10 employees'),
        ('11-50', '11-50 employees'),
        ('51-200', '51-200 employees'),
        ('201-500', '201-500 employees'),
        ('501-1000', '501-1000 employees'),
        ('1001+', '1001+ employees'),
    ])
    industry = models.CharField(max_length=100)
    location = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.company_name}'s Profile"