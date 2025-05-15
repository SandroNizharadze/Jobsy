from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from django.conf import settings
from django.utils.translation import gettext_lazy as _

class JobListing(models.Model):
    CATEGORY_CHOICES = [
        ('მენეჯმენტი/ადმინისტრირება', _('მენეჯმენტი/ ადმინისტრირება')),
        ('მარკეტინგი', _('მარკეტინგი')),
        ('ფინანსები', _('ფინანსები')),
        ('გაყიდვები/მომხმარებელთან ურთიერთობა', _('გაყიდვები/მომხმარებელთან ურთიერთობა')),
        ('IT/პროგრამირება', _('IT/პროგრამირება')),
        ('დიზაინი', _('დიზაინი')),
        ('ჰორეკა/კვება', _('ჰორეკა/კვება')),
        ('დაცვა', _('დაცვა')),
        ('სილამაზე/მოდა', _('სილამაზე/მოდა')),
        ('მშენებლობა', _('მშენებლობა')),
        ('მედიცინა', _('მედიცინა')),
        ('განათლება', _('განათლება')),
        ('სამართალი', _('სამართალი')),
        ('ტურიზმი', _('ტურიზმი')),
        ('ლოჯისტიკა/დისტრიბუცია', _('ლოჯისტიკა/დისტრიბუცია')),
        ('საბანკო საქმე', _('საბანკო საქმე')),
        ('აზარტული', _('აზარტული')),
    ]
    
    LOCATION_CHOICES = [
        ('დისტანციური', _('დისტანციური')),
        ('თბილისი', _('თბილისი')),
        ('აჭარა', _('აჭარა')),
        ('აფხაზეთი', _('აფხაზეთი')),
        ('სვანეთი', _('სვანეთი')),
        ('სამეგრელო', _('სამეგრელო')),
        ('კახეთი', _('კახეთი')),
        ('ლეჩხუმი', _('ლეჩხუმი')),
        ('რაჭა', _('რაჭა')),
        ('გურია', _('გურია')),
        ('ქვემო ქართლი', _('ქვემო ქართლი')),
        ('სამცხე-ჯავახეთი', _('სამცხე-ჯავახეთი')),
        ('შიდა ქართლი', _('შიდა ქართლი')),
        ('მცხეთა-მთიანეთი', _('მცხეთა-მთიანეთი')),
        ('იმერეთი', _('იმერეთი')),
    ]
    
    EXPERIENCE_CHOICES = [
        ('გამოცდილების გარეშე', _('გამოცდილების გარეშე')),
        ('დამწყები', _('დამწყები')),
        ('საშუალო დონე', _('საშუალო დონე')),
        ('პროფესიონალი', _('პროფესიონალი')),
    ]
    
    JOB_PREFERENCE_CHOICES = [
        ('სრული განაკვეთი', _('სრული განაკვეთი')),
        ('ნახევარი განაკვეთი', _('ნახევარი განაკვეთი')),
        ('ცვლები', _('ცვლები')),
    ]
    
    CONSIDERS_STUDENTS_CHOICES = [
        (True, _('კი')),
        (False, _('არა')),
    ]
    
    SALARY_TYPE_CHOICES = [
        ('თვეში', _('თვეში')),
        ('კვირაში', _('კვირაში')),
        ('დღეში', _('დღეში')),
        ('საათში', _('საათში')),
    ]

    title = models.CharField(max_length=100, db_index=True, verbose_name=_("ვაკანსიის დასახელება"))
    company = models.CharField(max_length=100, db_index=True, verbose_name=_("კომპანია"))
    description = models.TextField(verbose_name=_("ვაკანსიის აღწერა"))
    salary_min = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, db_index=True, verbose_name=_("მინიმალური ხელფასი"))
    salary_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name=_("მაქსიმალური ხელფასი"))
    salary_type = models.CharField(max_length=50, choices=SALARY_TYPE_CHOICES, default='თვეში', verbose_name=_("ხელფასის ტიპი"))
    category = models.CharField(max_length=100, choices=CATEGORY_CHOICES, db_index=True, verbose_name=_("კატეგორია"))
    location = models.CharField(max_length=100, choices=LOCATION_CHOICES, db_index=True, verbose_name=_("ლოკაცია"))
    employer = models.ForeignKey('EmployerProfile', on_delete=models.CASCADE, related_name='job_listings', verbose_name=_("დამსაქმებელი"))
    posted_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("გამოქვეყნების თარიღი"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("განახლების თარიღი"))
    interests = models.CharField(max_length=255, blank=True, verbose_name=_("ინტერესები"))
    fields = models.CharField(max_length=255, blank=True, verbose_name=_("სფეროები"))
    experience = models.CharField(max_length=100, choices=EXPERIENCE_CHOICES, db_index=True, verbose_name=_("გამოცდილება"))
    job_preferences = models.CharField(max_length=255, choices=JOB_PREFERENCE_CHOICES, verbose_name=_("სამუშაო გრაფიკი"))
    considers_students = models.BooleanField(default=False, choices=CONSIDERS_STUDENTS_CHOICES, verbose_name=_("განიხილავს სტუდენტებს"))
    STATUS_CHOICES = [
        ('pending_review', _('Pending Review')),
        ('approved', _('Approved')),
        ('rejected', _('Rejected')),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending_review', db_index=True, verbose_name=_("სტატუსი"))
    admin_feedback = models.TextField(blank=True, verbose_name=_("ადმინის უკუკავშირი"))
    PREMIUM_LEVEL_CHOICES = [
        ('standard', _('Standard')),
        ('premium', _('Premium')),
        ('premium_plus', _('Premium +')),
    ]
    premium_level = models.CharField(max_length=20, choices=PREMIUM_LEVEL_CHOICES, default='standard', db_index=True, verbose_name=_("პრემიუმ დონე"))

    def __str__(self):
        return f"{self.title} at {self.company}"

    class Meta:
        ordering = ['-posted_at']
        indexes = [
            models.Index(fields=['status', 'category']),
            models.Index(fields=['status', 'location']),
            models.Index(fields=['employer', 'status']),
        ]
        verbose_name = _("ვაკანსია")
        verbose_name_plural = _("ვაკანსიები")

class JobApplication(models.Model):
    STATUS_CHOICES = [
        ('განხილვის_პროცესში', _('განხილვის პროცესში')),
        ('გასაუბრება', _('გასაუბრება')),
        ('რეზერვი', _('რეზერვი')),
        ('pending', _('Pending')),
        ('reviewed', _('Reviewed')),
        ('interviewed', _('Interviewed')),
        ('offered', _('Offer Extended')),
        ('accepted', _('Offer Accepted')),
        ('rejected', _('Rejected')),
        ('withdrawn', _('Withdrawn')),
    ]
    
    job = models.ForeignKey(JobListing, on_delete=models.CASCADE, related_name='applications', verbose_name=_("ვაკანსია"))
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='applications', null=True, blank=True, verbose_name=_("მომხმარებელი"))
    guest_name = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("სტუმრის სახელი"))
    guest_email = models.EmailField(blank=True, null=True, verbose_name=_("სტუმრის ელ-ფოსტა"))
    cover_letter = models.TextField(verbose_name=_("მოტივაციის წერილი"))
    resume = models.FileField(upload_to='resumes/', verbose_name=_("რეზიუმე"))
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='განხილვის_პროცესში', db_index=True, verbose_name=_("სტატუსი"))
    applied_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("აპლიკაციის თარიღი"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("განახლების თარიღი"))
    
    class Meta:
        ordering = ['-applied_at']
        indexes = [
            models.Index(fields=['job', 'status']),
            models.Index(fields=['user', 'status']),
        ]
        verbose_name = _("აპლიკაცია")
        verbose_name_plural = _("აპლიკაციები")
    
    def __str__(self):
        return f"Application for {self.job.title} by {self.user.username if self.user else 'Guest'}"

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('candidate', _('Candidate')),
        ('employer', _('Employer')),
        ('admin', _('Admin')),
    ]
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name=_("მომხმარებელი"))
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='candidate', db_index=True, verbose_name=_("როლი"))
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True, verbose_name=_("პროფილის სურათი"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("შექმნის თარიღი"))
    # New fields for CV workflow
    cv = models.FileField(upload_to='cvs/', blank=True, null=True, verbose_name=_("CV"))
    cv_consent = models.BooleanField(default=False, verbose_name=_("CV-ის გაზიარების თანხმობა"))
    cv_share_with_employers = models.BooleanField(default=False, verbose_name=_("CV-ის გაზიარება დამსაქმებლებთან"))
    cv_visible_to = models.ManyToManyField('EmployerProfile', blank=True, related_name='visible_candidate_cvs', verbose_name=_("CV-ის ხილვადობა"))

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

    class Meta:
        verbose_name = _("მომხმარებლის პროფილი")
        verbose_name_plural = _("მომხმარებლების პროფილები")

class EmployerProfile(models.Model):
    COMPANY_SIZE_CHOICES = [
        ('1-10', _('1-10 employees')),
        ('11-50', _('11-50 employees')),
        ('51-200', _('51-200 employees')),
        ('201-500', _('201-500 employees')),
        ('501-1000', _('501-1000 employees')),
        ('1001+', _('1001+ employees')),
    ]
    
    user_profile = models.OneToOneField(UserProfile, on_delete=models.CASCADE, related_name='employer_profile', verbose_name=_("მომხმარებლის პროფილი"))
    company_name = models.CharField(max_length=100, blank=True, db_index=True, verbose_name=_("კომპანიის დასახელება"))
    company_website = models.URLField(blank=True, verbose_name=_("კომპანიის ვებსაიტი"))
    company_description = models.TextField(blank=True, verbose_name=_("კომპანიის აღწერა"))
    company_logo = models.ImageField(upload_to='company_logos/', blank=True, null=True, verbose_name=_("კომპანიის ლოგო"))
    company_size = models.CharField(max_length=50, choices=COMPANY_SIZE_CHOICES, blank=True, verbose_name=_("კომპანიის ზომა"))
    industry = models.CharField(max_length=100, blank=True, db_index=True, verbose_name=_("ინდუსტრია"))
    location = models.CharField(max_length=100, blank=True, db_index=True, verbose_name=_("მდებარეობა"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("შექმნის თარიღი"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("განახლების თარიღი"))

    def __str__(self):
        return f"{self.company_name} ({self.user_profile.user.username})"
        
    class Meta:
        verbose_name = _("დამსაქმებლის პროფილი")
        verbose_name_plural = _("დამსაქმებლების პროფილები")