from django.test import TestCase
from django.contrib.auth.models import User
from core.models import UserProfile, EmployerProfile, JobListing, JobApplication
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from datetime import timedelta


class UserProfileModelTest(TestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        # Get the automatically created profile instead of creating a new one
        try:
            self.user_profile = UserProfile.objects.get(user=self.user)
        except UserProfile.DoesNotExist:
            self.user_profile = UserProfile.objects.create(user=self.user, role='candidate')
        
    def test_user_profile_exists(self):
        """Test that a UserProfile exists for the user"""
        self.assertIsNotNone(self.user_profile)
        self.assertEqual(self.user_profile.user, self.user)
        
    def test_user_profile_str_method(self):
        """Test the string representation of a UserProfile"""
        self.assertEqual(str(self.user_profile), self.user.username)
        
    def test_role_change_to_employer_creates_employer_profile(self):
        """Test that changing role to 'employer' creates an EmployerProfile"""
        self.user_profile.role = 'employer'
        self.user_profile.save()
        
        # Check if an EmployerProfile was created
        self.assertTrue(hasattr(self.user_profile, 'employer_profile'))
        self.assertEqual(self.user_profile.employer_profile.user_profile, self.user_profile)


class EmployerProfileModelTest(TestCase):
    def setUp(self):
        # Create a test user and user profile
        self.user = User.objects.create_user(
            username='employer',
            email='employer@example.com',
            password='employerpass'
        )
        # Get the automatically created profile instead of creating a new one
        try:
            self.user_profile = UserProfile.objects.get(user=self.user)
            self.user_profile.role = 'employer'
            self.user_profile.save()
        except UserProfile.DoesNotExist:
            self.user_profile = UserProfile.objects.create(user=self.user, role='employer')
        
    def test_employer_profile_exists(self):
        """Test that an EmployerProfile exists for the user with employer role"""
        self.assertTrue(hasattr(self.user_profile, 'employer_profile'))
        
    def test_employer_profile_str_method(self):
        """Test the string representation of an EmployerProfile"""
        employer_profile = self.user_profile.employer_profile
        employer_profile.company_name = 'Test Company'
        employer_profile.save()
        self.assertEqual(str(employer_profile), "Test Company (employer)")


class JobListingModelTest(TestCase):
    def setUp(self):
        # Create a test employer
        self.user = User.objects.create_user('employer', 'employer@example.com', 'employerpass')
        # Get the automatically created profile instead of creating a new one
        try:
            self.user_profile = UserProfile.objects.get(user=self.user)
            self.user_profile.role = 'employer'
            self.user_profile.save()
        except UserProfile.DoesNotExist:
            self.user_profile = UserProfile.objects.create(user=self.user, role='employer')
            
        self.employer_profile = self.user_profile.employer_profile
        self.employer_profile.company_name = 'Test Company'
        self.employer_profile.save()
        
    def test_job_listing_creation(self):
        """Test that a JobListing can be created with required fields"""
        job = JobListing.objects.create(
            title='Test Job',
            company=self.employer_profile.company_name,
            description='This is a test job description',
            employer=self.employer_profile,
            status='approved'
        )
        self.assertEqual(job.title, 'Test Job')
        self.assertEqual(job.company, 'Test Company')
        self.assertEqual(job.employer, self.employer_profile)
        
    def test_job_listing_str_method(self):
        """Test the string representation of a JobListing"""
        job = JobListing.objects.create(
            title='Test Job',
            company=self.employer_profile.company_name,
            description='This is a test job description',
            employer=self.employer_profile
        )
        self.assertEqual(str(job), "Test Job at Test Company")


class JobApplicationModelTest(TestCase):
    def setUp(self):
        # Create test users
        self.employer_user = User.objects.create_user('employer', 'employer@example.com', 'employerpass')
        
        # Get the automatically created profile for employer instead of creating a new one
        try:
            self.employer_profile = UserProfile.objects.get(user=self.employer_user)
            self.employer_profile.role = 'employer'
            self.employer_profile.save()
        except UserProfile.DoesNotExist:
            self.employer_profile = UserProfile.objects.create(user=self.employer_user, role='employer')
            
        self.company = self.employer_profile.employer_profile
        self.company.company_name = 'Test Company'
        self.company.save()
        
        self.candidate_user = User.objects.create_user('candidate', 'candidate@example.com', 'candidatepass')
        
        # Get the automatically created profile for candidate instead of creating a new one
        try:
            self.candidate_profile = UserProfile.objects.get(user=self.candidate_user)
        except UserProfile.DoesNotExist:
            self.candidate_profile = UserProfile.objects.create(user=self.candidate_user, role='candidate')
        
        # Create a test job
        self.job = JobListing.objects.create(
            title='Test Job',
            company=self.company.company_name,
            description='This is a test job description',
            employer=self.company,
            status='approved'
        )
        
        # Create a test resume file
        self.resume = SimpleUploadedFile("resume.pdf", b"file content", content_type="application/pdf")
        
    def test_job_application_creation(self):
        """Test that a JobApplication can be created with required fields"""
        application = JobApplication.objects.create(
            job=self.job,
            user=self.candidate_user,
            cover_letter='Test cover letter',
            resume=self.resume
        )
        self.assertEqual(application.job, self.job)
        self.assertEqual(application.user, self.candidate_user)
        self.assertEqual(application.status, 'pending')
        
    def test_job_application_str_method(self):
        """Test the string representation of a JobApplication"""
        application = JobApplication.objects.create(
            job=self.job,
            user=self.candidate_user,
            cover_letter='Test cover letter',
            resume=self.resume
        )
        self.assertEqual(str(application), f"Application for Test Job by candidate")
        
    def test_guest_application_creation(self):
        """Test that a guest user can create a JobApplication"""
        application = JobApplication.objects.create(
            job=self.job,
            guest_name='Guest User',
            guest_email='guest@example.com',
            cover_letter='Test cover letter',
            resume=self.resume
        )
        self.assertEqual(application.job, self.job)
        self.assertEqual(application.guest_name, 'Guest User')
        self.assertEqual(application.guest_email, 'guest@example.com')
        self.assertIsNone(application.user) 