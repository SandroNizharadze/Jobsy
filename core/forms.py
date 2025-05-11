from django import forms
from django.contrib.auth.models import User
from .models import UserProfile, EmployerProfile, JobListing
from django.contrib.auth.forms import UserCreationForm
from django.core.files.uploadedfile import UploadedFile

class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'password1']
        widgets = {
            'username': forms.HiddenInput(),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Name'}),
            'password1': forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make username field hidden and populate it with email value
        self.fields['username'].required = False
        # Remove password2 field
        del self.fields['password2']
        # Remove password validation messages
        self.fields['password1'].help_text = None
        self.fields['password1'].error_messages = {
            'required': 'Please enter your password.',
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with that email already exists.")
        if User.objects.filter(username=email).exists():
            raise forms.ValidationError("A user with that email already exists.")
        return email

    def clean_password1(self):
        password = self.cleaned_data.get('password1')
        if len(password) < 4:
            raise forms.ValidationError("Password must be at least 4 characters long.")
        return password

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        if email:
            # Set username to be the same as email
            cleaned_data['username'] = email
        return cleaned_data

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['profile_picture', 'cv']
        widgets = {
            'profile_picture': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'cv': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx'
            }),
        }
        help_texts = {
            'cv': 'Upload your CV (PDF, DOC, DOCX).',
        }

    def clean_profile_picture(self):
        profile_picture = self.cleaned_data.get('profile_picture')
        # Only validate if a new file is being uploaded
        if profile_picture and isinstance(profile_picture, UploadedFile):
            if profile_picture.size > 5 * 1024 * 1024:  # 5MB limit
                raise forms.ValidationError("Image file too large ( > 5MB )")
            if not profile_picture.content_type.startswith('image/'):
                raise forms.ValidationError("File is not an image")
        return profile_picture

class EmployerProfileForm(forms.ModelForm):
    class Meta:
        model = EmployerProfile
        fields = ('company_name', 'company_website', 'company_description', 'company_logo',
                 'company_size', 'industry', 'location')
        widgets = {
            'company_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your company name'
            }),
            'company_website': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://www.example.com'
            }),
            'company_description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe your company...'
            }),
            'company_logo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'company_size': forms.Select(attrs={'class': 'form-control'}),
            'industry': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'E.g., Technology, Healthcare, Finance'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'City, Country'
            }),
        }

    def clean_company_logo(self):
        company_logo = self.cleaned_data.get('company_logo')
        # Only validate if a new file is being uploaded
        if company_logo and isinstance(company_logo, UploadedFile):
            if company_logo.size > 5 * 1024 * 1024:  # 5MB limit
                raise forms.ValidationError("Image file too large ( > 5MB )")
            if not company_logo.content_type.startswith('image/'):
                raise forms.ValidationError("File is not an image")
        return company_logo

class JobListingForm(forms.ModelForm):
    class Meta:
        model = JobListing
        fields = (
            'title', 'description', 'location', 'salary_min', 'salary_max', 'salary_type',
            'category', 'interests', 'fields', 'experience', 'job_preferences'
        )
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Job Title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Describe the job...'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Location'}),
            'salary_min': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Minimum Salary'}),
            'salary_max': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Maximum Salary'}),
            'salary_type': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. per month'}),
            'category': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Category'}),
            'interests': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Python, Django, React'}),
            'fields': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Relevant fields'}),
            'experience': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Entry, Mid, Senior'}),
            'job_preferences': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. remote, full-time, contract'}),
        }