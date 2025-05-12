from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from django.conf import settings

class JobListing(models.Model):
    title = models.CharField(max_length=100, db_index=True)
    company = models.CharField(max_length=100, db_index=True)
    description = models.TextField()
    salary_min = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, db_index=True)
    salary_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    salary_type = models.CharField(max_length=50, blank=True)
    category = models.CharField(max_length=100, blank=True, db_index=True)
    location = models.CharField(max_length=100, blank=True, db_index=True)
    employer = models.ForeignKey('EmployerProfile', on_delete=models.CASCADE, related_name='job_listings')
    posted_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    interests = models.CharField(max_length=255, blank=True)
    fields = models.CharField(max_length=255, blank=True)
    experience = models.CharField(max_length=100, blank=True, db_index=True)
    job_preferences = models.CharField(max_length=255, blank=True)
    STATUS_CHOICES = [
        ('pending_review', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending_review', db_index=True)
    admin_feedback = models.TextField(blank=True)
    PREMIUM_LEVEL_CHOICES = [
        ('standard', 'Standard'),
        ('premium', 'Premium'),
        ('premium_plus', 'Premium +'),
    ]
    premium_level = models.CharField(max_length=20, choices=PREMIUM_LEVEL_CHOICES, default='standard', db_index=True)

    def __str__(self):
        return f"{self.title} at {self.company}"

    class Meta:
        ordering = ['-posted_at']
        indexes = [
            models.Index(fields=['status', 'category']),
            models.Index(fields=['status', 'location']),
            models.Index(fields=['employer', 'status']),
        ]

class JobApplication(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('reviewed', 'Reviewed'),
        ('interviewed', 'Interviewed'),
        ('offered', 'Offer Extended'),
        ('accepted', 'Offer Accepted'),
        ('rejected', 'Rejected'),
        ('withdrawn', 'Withdrawn'),
    ]
    
    job = models.ForeignKey(JobListing, on_delete=models.CASCADE, related_name='applications')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='applications', null=True, blank=True)
    guest_name = models.CharField(max_length=255, blank=True, null=True)
    guest_email = models.EmailField(blank=True, null=True)
    cover_letter = models.TextField()
    resume = models.FileField(upload_to='resumes/')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    applied_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-applied_at']
        indexes = [
            models.Index(fields=['job', 'status']),
            models.Index(fields=['user', 'status']),
        ]
    
    def __str__(self):
        return f"Application for {self.job.title} by {self.user.username if self.user else 'Guest'}"

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('candidate', 'Candidate'),
        ('employer', 'Employer'),
        ('admin', 'Admin'),
    ]
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='candidate', db_index=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    # New fields for CV workflow
    cv = models.FileField(upload_to='cvs/', blank=True, null=True)
    cv_consent = models.BooleanField(default=False)
    cv_share_with_employers = models.BooleanField(default=False)
    cv_visible_to = models.ManyToManyField('EmployerProfile', blank=True, related_name='visible_candidate_cvs')

    def __str__(self):
        return self.user.username

    def is_profile_complete(self):
        """Check if the profile is complete enough to apply for jobs."""
        return True

    def save(self, *args, **kwargs):
        """Override save method to create employer profile if role changes to employer."""
        is_new = self.pk is None
        old_role = None
        
        if not is_new:
            old_instance = UserProfile.objects.get(pk=self.pk)
            old_role = old_instance.role
        
        super().save(*args, **kwargs)
        
        # Create employer profile if user is assigned employer role
        if (is_new and self.role == 'employer') or (old_role != 'employer' and self.role == 'employer'):
            EmployerProfile.objects.get_or_create(user_profile=self)

class EmployerProfile(models.Model):
    COMPANY_SIZE_CHOICES = [
        ('1-10', '1-10 employees'),
        ('11-50', '11-50 employees'),
        ('51-200', '51-200 employees'),
        ('201-500', '201-500 employees'),
        ('501-1000', '501-1000 employees'),
        ('1001+', '1001+ employees'),
    ]
    
    user_profile = models.OneToOneField(UserProfile, on_delete=models.CASCADE, related_name='employer_profile')
    company_name = models.CharField(max_length=100, blank=True, db_index=True)
    company_website = models.URLField(blank=True)
    company_description = models.TextField(blank=True)
    company_logo = models.ImageField(upload_to='company_logos/', blank=True, null=True)
    company_size = models.CharField(max_length=50, choices=COMPANY_SIZE_CHOICES, blank=True)
    industry = models.CharField(max_length=100, blank=True, db_index=True)
    location = models.CharField(max_length=100, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.company_name} ({self.user_profile.user.username})"