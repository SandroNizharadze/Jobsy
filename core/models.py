from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
import logging
from django.db import transaction
from datetime import timedelta

# Import storage backends if S3 is enabled
if hasattr(settings, 'USE_S3') and settings.USE_S3:
    from jobsy.storage_backends import PublicMediaStorage, PrivateMediaStorage
else:
    PublicMediaStorage = None
    PrivateMediaStorage = None

logger = logging.getLogger(__name__)

class SoftDeletionQuerySet(models.QuerySet):
    def delete(self):
        return super().update(deleted_at=timezone.now())
        
    def hard_delete(self):
        return super().delete()
        
    def alive(self):
        return self.filter(deleted_at=None)
        
    def deleted(self):
        return self.exclude(deleted_at=None)

class SoftDeletionManager(models.Manager):
    def __init__(self, *args, **kwargs):
        self.with_deleted = kwargs.pop('with_deleted', False)
        super().__init__(*args, **kwargs)
        
    def get_queryset(self):
        if self.with_deleted:
            return SoftDeletionQuerySet(self.model, using=self._db)
        return SoftDeletionQuerySet(self.model, using=self._db).filter(deleted_at=None)
        
    def hard_delete(self):
        return self.get_queryset().hard_delete()
        
    def deleted(self):
        return self.get_queryset().deleted()

class SoftDeletionModel(models.Model):
    deleted_at = models.DateTimeField(blank=True, null=True, verbose_name=_("წაშლის თარიღი"))
    
    objects = SoftDeletionManager()
    all_objects = SoftDeletionManager(with_deleted=True)
    
    class Meta:
        abstract = True
        
    def delete(self, using=None, keep_parents=False):
        self.deleted_at = timezone.now()
        self.save()
        
    def hard_delete(self):
        super().delete()

class JobListing(SoftDeletionModel):
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
    expires_at = models.DateTimeField(null=True, blank=True, db_index=True, verbose_name=_("ვადის გასვლის თარიღი"))
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
    georgian_language_only = models.BooleanField(choices=[(True, 'კი'), (False, 'არა')], default=False, verbose_name=_("პოზიციაზე მოთხოვნილია მხოლოდ ქართული ენის ცოდნა"))

    def __str__(self):
        return f"{self.title} at {self.company}"

    def is_expired(self):
        """Check if the job posting has expired"""
        if not self.expires_at:
            return False
        return timezone.now() >= self.expires_at

    class Meta:
        ordering = ['-posted_at']
        indexes = [
            models.Index(fields=['status', 'category']),
            models.Index(fields=['status', 'location']),
            models.Index(fields=['employer', 'status']),
            models.Index(fields=['expires_at']),
        ]
        verbose_name = _("ვაკანსია")
        verbose_name_plural = _("ვაკანსიები")

class RejectionReason(models.Model):
    """Model for predefined rejection reasons"""
    REASON_CHOICES = [
        ('არასაკმარისი_გამოცდილება', _("არასაკმარისი გამოცდილება")),
        ('უნარების_ნაკლებობა', _("უნარების ნაკლებობა")),
        ('განათლების_შეუსაბამობა', _("განათლების შეუსაბამობა")),
        ('არარელევანტური_სამუშაო_ისტორია', _("არარელევანტური სამუშაო ისტორია")),
        ('ლოკაცია', _("ლოკაცია")),
        ('სერთიფიკატების_ლიცენზიების_ნაკლებობა', _("სერთიფიკატების/ლიცენზიების ნაკლებობა")),
        ('მოთხოვნებთან_შეუსაბამო_მიღწევები', _("მოთხოვნებთან შეუსაბამო მიღწევები")),
        ('სივის_ფორმატის_სტრუქტურის_ხარვეზები', _("სივის ფორმატის/სტრუქტურის ხარვეზები")),
        ('არასაკმარისი_ინფორმაცია', _("არასაკმარისი ინფორმაცია")),
        ('გადაჭარბებული_ინფორმაცია', _("გადაჭარბებული ინფორმაცია")),
        ('კარიერული_მიზნების_შეუსაბამობა', _("კარიერული მიზნების შეუსაბამობა")),
        ('ენის_ცოდნის_ნაკლებობა', _("ენის ცოდნის ნაკლებობა")),
        ('არარეალისტური_ხელფასის_მოლოდინი', _("არარეალისტური ხელფასის მოლოდინი")),
    ]
    
    name = models.CharField(max_length=100, choices=REASON_CHOICES, unique=True, verbose_name=_("მიზეზი"))
    
    def __str__(self):
        return self.get_name_display()
    
    class Meta:
        verbose_name = _("უარის მიზეზი")
        verbose_name_plural = _("უარის მიზეზები")

class JobApplication(models.Model):
    STATUS_CHOICES = [
        ('განხილვის_პროცესში', _('განხილვის პროცესში')),
        ('გასაუბრება', _('გასაუბრება')),
        ('რეზერვი', _('რეზერვი')),
    ]
    
    job = models.ForeignKey(JobListing, on_delete=models.SET_NULL, null=True, related_name='applications', verbose_name=_("ვაკანსია"))
    job_title = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("ვაკანსიის სათაური"))
    job_company = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("კომპანია"))
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='applications', null=True, blank=True, verbose_name=_("მომხმარებელი"))
    guest_name = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("სტუმრის სახელი"))
    guest_email = models.EmailField(blank=True, null=True, verbose_name=_("სტუმრის ელ-ფოსტა"))
    cover_letter = models.TextField(verbose_name=_("მოტივაციის წერილი"))
    # Use PrivateMediaStorage for sensitive resume files when S3 is enabled
    if PrivateMediaStorage:
        resume = models.FileField(
            upload_to='resumes/', 
            storage=PrivateMediaStorage(),
            verbose_name=_("რეზიუმე")
        )
    else:
        resume = models.FileField(
            upload_to='resumes/', 
            verbose_name=_("რეზიუმე")
        )
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='განხილვის_პროცესში', db_index=True, verbose_name=_("სტატუსი"))
    applied_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("აპლიკაციის თარიღი"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("განახლების თარიღი"))
    is_read = models.BooleanField(default=False, db_index=True, verbose_name=_("წაკითხულია"))
    rejection_reasons = models.ManyToManyField(RejectionReason, blank=True, related_name='applications', verbose_name=_("უარის მიზეზები"))
    feedback = models.TextField(blank=True, verbose_name=_("უკუკავშირი"))
    
    def save(self, *args, **kwargs):
        if self.job and (not self.job_title or not self.job_company):
            self.job_title = self.job.title
            self.job_company = self.job.company
        super().save(*args, **kwargs)
    
    class Meta:
        ordering = ['-applied_at']
        indexes = [
            models.Index(fields=['job', 'status']),
            models.Index(fields=['user', 'status']),
        ]
        verbose_name = _("აპლიკაცია")
        verbose_name_plural = _("აპლიკაციები")
    
    def __str__(self):
        job_info = self.job_title if self.job is None else self.job.title
        user_info = self.user.username if self.user else 'Guest'
        return f"Application for {job_info} by {user_info}"

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('candidate', _('Candidate')),
        ('employer', _('Employer')),
        ('admin', _('Admin')),
    ]
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name=_("მომხმარებელი"))
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='candidate', db_index=True, verbose_name=_("როლი"))
    
    # Use PublicMediaStorage for profile pictures when S3 is enabled
    if PublicMediaStorage:
        profile_picture = models.ImageField(
            upload_to='profile_pictures/', 
            storage=PublicMediaStorage(),
            blank=True, 
            null=True, 
            verbose_name=_("პროფილის სურათი")
        )
    else:
        profile_picture = models.ImageField(
            upload_to='profile_pictures/', 
            blank=True, 
            null=True, 
            verbose_name=_("პროფილის სურათი")
        )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("შექმნის თარიღი"))
    
    # Use PrivateMediaStorage for CV files when S3 is enabled
    if PrivateMediaStorage:
        cv = models.FileField(
            upload_to='cvs/', 
            storage=PrivateMediaStorage(),
            blank=True, 
            null=True, 
            verbose_name=_("CV")
        )
    else:
        cv = models.FileField(
            upload_to='cvs/', 
            blank=True, 
            null=True, 
            verbose_name=_("CV")
        )

    def __str__(self):
        return self.user.username

    def is_profile_complete(self):
        """Check if the profile is complete enough to apply for jobs."""
        return True

    def save(self, *args, **kwargs):
        """Override save method to create employer profile if role changes to employer."""
        logger.info(f"Saving UserProfile for {self.user.username} with role {self.role}")
        
        is_new = self.pk is None
        old_role = None
        
        if not is_new:
            try:
                old_instance = UserProfile.objects.get(pk=self.pk)
                old_role = old_instance.role
                logger.info(f"Previous role was: {old_role}")
            except Exception as e:
                logger.error(f"Error getting old role: {e}")
        
        # Ensure the save completes 
        super().save(*args, **kwargs)
        
        # Always create/check employer profile if the role is 'employer'
        if self.role == 'employer':
            logger.info(f"Creating employer profile for {self.user.username}")
            try:
                employer_profile, created = EmployerProfile.objects.get_or_create(user_profile=self)
                action = "Created new" if created else "Using existing"
                logger.info(f"{action} employer profile (id: {employer_profile.pk})")
            except Exception as e:
                logger.error(f"Error creating/getting employer profile: {e}")

    class Meta:
        verbose_name = _("მომხმარებლის პროფილი")
        verbose_name_plural = _("მომხმარებლების პროფილები")

class EmployerProfile(SoftDeletionModel):
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
    company_id = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("საიდენტიფიკაციო კოდი"))
    phone_number = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("მობილურის ნომერი"))
    company_website = models.URLField(blank=True, verbose_name=_("კომპანიის ვებსაიტი"))
    company_description = models.TextField(blank=True, verbose_name=_("კომპანიის აღწერა"))
    # Use PublicMediaStorage for company logos when S3 is enabled
    if PublicMediaStorage:
        company_logo = models.ImageField(
            upload_to='company_logos/', 
            storage=PublicMediaStorage(),
            blank=True, 
            null=True, 
            verbose_name=_("კომპანიის ლოგო")
        )
    else:
        company_logo = models.ImageField(
            upload_to='company_logos/', 
            blank=True, 
            null=True, 
            verbose_name=_("კომპანიის ლოგო")
        )
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

    @classmethod
    def create_for_user(cls, user, company_name="", company_id=None, phone_number=None):
        """
        Create an EmployerProfile for a user, ensuring the UserProfile has the right role.
        This is a convenience method for the registration process.
        """
        with transaction.atomic():
            # First ensure user profile exists with employer role
            try:
                profile = UserProfile.objects.get(user=user)
                # Update role if needed
                if profile.role != 'employer':
                    profile.role = 'employer'
                    profile.save()
                    logger.info(f"Updated existing UserProfile for {user.username} to role 'employer'")
            except UserProfile.DoesNotExist:
                # Create new profile with employer role
                profile = UserProfile.objects.create(user=user, role='employer')
                logger.info(f"Created new UserProfile for {user.username} with role 'employer'")
            
            # Now create/update employer profile
            try:
                employer_profile = cls.objects.get(user_profile=profile)
                # Update fields if provided
                if company_name:
                    employer_profile.company_name = company_name
                if company_id:
                    employer_profile.company_id = company_id
                if phone_number:
                    employer_profile.phone_number = phone_number
                employer_profile.save()
                logger.info(f"Updated existing EmployerProfile for {user.username}")
                return employer_profile
            except cls.DoesNotExist:
                # Create new employer profile
                employer_profile = cls.objects.create(
                    user_profile=profile,
                    company_name=company_name,
                    company_id=company_id,
                    phone_number=phone_number
                )
                logger.info(f"Created new EmployerProfile for {user.username}")
                return employer_profile

class SavedJob(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='saved_jobs', verbose_name=_("მომხმარებელი"))
    job = models.ForeignKey('JobListing', on_delete=models.SET_NULL, null=True, related_name='saved_by', verbose_name=_("ვაკანსია"))
    # Store job details for historical record
    job_title = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("ვაკანსიის სათაური"))
    job_company = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("კომპანია"))
    saved_at = models.DateTimeField(auto_now_add=True, verbose_name=_("შენახვის თარიღი"))

    def save(self, *args, **kwargs):
        # Save job details for historical record
        if self.job and (not self.job_title or not self.job_company):
            self.job_title = self.job.title
            self.job_company = self.job.company
        super().save(*args, **kwargs)

    class Meta:
        unique_together = ('user', 'job')
        verbose_name = _("შენახული ვაკანსია")
        verbose_name_plural = _("შენახული ვაკანსიები")
        ordering = ['-saved_at']

    def __str__(self):
        job_info = self.job_title if self.job is None else self.job.title
        return f"{self.user.username} - {job_info}"

# Add signals to ensure user profile and employer profile are properly created
@receiver(post_save, sender=UserProfile)
def ensure_employer_profile(sender, instance, created, **kwargs):
    """
    Ensure that when a UserProfile is saved with the 'employer' role,
    an EmployerProfile is created.
    """
    logger.info(f"Signal: UserProfile saved for {instance.user.username} with role {instance.role}")
    
    if instance.role == 'employer':
        try:
            if hasattr(instance, 'employer_profile'):
                logger.info(f"EmployerProfile already exists for {instance.user.username}")
            else:
                logger.info(f"Creating new EmployerProfile for {instance.user.username}")
                employer_profile = EmployerProfile.objects.create(user_profile=instance)
                logger.info(f"Created EmployerProfile with ID {employer_profile.id}")
        except Exception as e:
            logger.error(f"Error in ensure_employer_profile: {str(e)}")

@receiver(post_save, sender=JobListing)
def set_job_expiration(sender, instance, **kwargs):
    """
    Set the job expiration date to 30 days after approval.
    This is triggered when a job's status changes to 'approved'.
    """
    if instance.status == 'approved' and not instance.expires_at:
        # Set expiration to 30 days from now
        instance.expires_at = timezone.now() + timedelta(days=30)
        # Save without triggering this signal again
        JobListing.objects.filter(pk=instance.pk).update(expires_at=instance.expires_at)