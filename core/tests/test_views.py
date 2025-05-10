from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from core.models import UserProfile, EmployerProfile, JobListing, JobApplication
from unittest.mock import patch


class JobListViewTest(TestCase):
    def setUp(self):
        # Create a test employer
        self.employer_user = User.objects.create_user('employer', 'employer@example.com', 'employerpass')
        
        # Get the automatically created profile or create it
        try:
            self.employer_profile = UserProfile.objects.get(user=self.employer_user)
            self.employer_profile.role = 'employer'
            self.employer_profile.save()
        except UserProfile.DoesNotExist:
            self.employer_profile = UserProfile.objects.create(user=self.employer_user, role='employer')
            
        self.company = self.employer_profile.employer_profile
        self.company.company_name = 'Test Company'
        self.company.location = 'Test City'
        self.company.industry = 'Technology'
        self.company.save()
        
        # Create some test jobs
        for i in range(5):
            JobListing.objects.create(
                title=f'Test Job {i+1}',
                company=self.company.company_name,
                description=f'Test job description {i+1}',
                employer=self.company,
                status='approved',
                category='ტექნოლოგია',
                location='Test City',
                experience='საშუალო'
            )
        
        # Create one job with pending status
        JobListing.objects.create(
            title='Pending Job',
            company=self.company.company_name,
            description='This job is pending approval',
            employer=self.company,
            status='pending_review',
            category='ტექნოლოგია',
            location='Test City'
        )
        
        self.client = Client()
    
    def test_job_list_view(self):
        """Test the job list view shows only approved jobs"""
        response = self.client.get(reverse('job_list'))
        
        # Check basic response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/job_list.html')
        
        # Check that only approved jobs are shown
        self.assertEqual(len(response.context['jobs']), 5)
        for job in response.context['jobs']:
            self.assertEqual(job.status, 'approved')
        
        # Check that pending jobs are not shown
        job_titles = [job.title for job in response.context['jobs']]
        self.assertNotIn('Pending Job', job_titles)
    
    def test_job_list_search_filter(self):
        """Test the job list view with search filter"""
        response = self.client.get(f"{reverse('job_list')}?search=Job 1")
        
        # Should match only one job
        self.assertEqual(len(response.context['jobs']), 1)
        self.assertEqual(response.context['jobs'][0].title, 'Test Job 1')
    
    def test_job_list_category_filter(self):
        """Test the job list view with category filter"""
        response = self.client.get(f"{reverse('job_list')}?category=ტექნოლოგია")
        
        # Should match all 5 approved jobs
        self.assertEqual(len(response.context['jobs']), 5)
        for job in response.context['jobs']:
            self.assertEqual(job.category, 'ტექნოლოგია')


class JobDetailViewTest(TestCase):
    def setUp(self):
        # Create a test employer
        self.employer_user = User.objects.create_user('employer', 'employer@example.com', 'employerpass')
        
        # Get the automatically created profile or create it
        try:
            self.employer_profile = UserProfile.objects.get(user=self.employer_user)
            self.employer_profile.role = 'employer'
            self.employer_profile.save()
        except UserProfile.DoesNotExist:
            self.employer_profile = UserProfile.objects.create(user=self.employer_user, role='employer')
            
        self.company = self.employer_profile.employer_profile
        self.company.company_name = 'Test Company'
        self.company.save()
        
        # Create a test job
        self.job = JobListing.objects.create(
            title='Test Job',
            company=self.company.company_name,
            description='Test job description',
            employer=self.company,
            status='approved',
            category='ტექნოლოგია',
            location='Test City'
        )
        
        # Create a pending job
        self.pending_job = JobListing.objects.create(
            title='Pending Job',
            company=self.company.company_name,
            description='This job is pending approval',
            employer=self.company,
            status='pending_review'
        )
        
        self.client = Client()
    
    def test_job_detail_view(self):
        """Test the job detail view for an approved job"""
        response = self.client.get(reverse('job_detail', args=[self.job.id]))
        
        # Check basic response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/job_detail.html')
        
        # Check job details
        self.assertEqual(response.context['job'], self.job)
    
    def test_job_detail_view_pending_job(self):
        """Test the job detail view for a pending job should return 404"""
        response = self.client.get(reverse('job_detail', args=[self.pending_job.id]))
        
        # Should return 404 as pending jobs are not visible
        self.assertEqual(response.status_code, 404)


class AuthViewsTest(TestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(
            username='testuser@example.com',
            email='testuser@example.com',
            password='testpassword'
        )
        
        # We don't need to create UserProfile since it should be created automatically
        # Check that profile exists
        self.assertTrue(hasattr(self.user, 'userprofile'))
        
        self.client = Client()
    
    def test_login_view(self):
        """Test the login view with valid credentials"""
        response = self.client.post(reverse('login'), {
            'username': 'testuser@example.com',
            'password': 'testpassword'
        })
        
        # Should redirect after successful login
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('job_list'))
        
        # Check that user is logged in
        user = response.wsgi_request.user
        self.assertTrue(user.is_authenticated)
    
    def test_login_view_invalid_credentials(self):
        """Test the login view with invalid credentials"""
        response = self.client.post(reverse('login'), {
            'username': 'testuser@example.com',
            'password': 'wrongpassword'
        })
        
        # Should stay on the login page
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/login.html')
        
        # User should not be logged in
        user = response.wsgi_request.user
        self.assertFalse(user.is_authenticated)
    
    @patch('core.views.auth_views.UserProfile.objects.create')
    @patch('core.views.auth_views.login')
    def test_register_view(self, mock_login, mock_create_profile):
        """Test the register view with valid data"""
        # Set up mocks
        mock_create_profile.return_value = None
        mock_login.return_value = None
        
        response = self.client.post(reverse('register'), {
            'email': 'newuser@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'password1': 'securepass123',
            'password2': 'securepass123'
        }, follow=True)
        
        # Should redirect after successful registration
        self.assertEqual(response.status_code, 200)  # Using follow=True to get the final response
        
        # Check that user was created
        self.assertTrue(User.objects.filter(email='newuser@example.com').exists())
        
        # Check that user profile was created
        user = User.objects.get(email='newuser@example.com')
        self.assertTrue(hasattr(user, 'userprofile'))
        
        # We patch the login function, but still verify the role
        self.assertEqual(user.userprofile.role, 'candidate')
        
        # Check that login was called
        mock_login.assert_called_once()
    
    def test_logout_view(self):
        """Test the logout view"""
        # First login
        self.client.login(username='testuser@example.com', password='testpassword')
        
        # Then logout
        response = self.client.get(reverse('logout'))
        
        # Should redirect after logout
        self.assertEqual(response.status_code, 302)
        
        # User should be logged out
        user = response.wsgi_request.user
        self.assertFalse(user.is_authenticated) 