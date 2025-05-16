from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import JobListing, UserProfile, EmployerProfile, JobApplication
from import_export.admin import ImportExportModelAdmin, ImportExportActionModelAdmin
from import_export import resources
from rangefilter.filters import DateRangeFilter

# Resources for model export
class JobListingResource(resources.ModelResource):
    class Meta:
        model = JobListing
        fields = ('id', 'title', 'company', 'description', 'salary_min', 'salary_max', 
                  'salary_type', 'category', 'location', 'posted_at', 'experience',
                  'job_preferences', 'considers_students', 'status', 'premium_level')

class EmployerProfileResource(resources.ModelResource):
    class Meta:
        model = EmployerProfile
        fields = ('id', 'company_name', 'company_id', 'phone_number', 'company_website', 
                 'company_description', 'company_size', 'industry', 'location', 
                 'user_profile__user__email', 'created_at')

class JobApplicationResource(resources.ModelResource):
    class Meta:
        model = JobApplication
        fields = ('id', 'job__title', 'job__company', 'user__email', 'guest_name', 
                 'guest_email', 'status', 'applied_at')

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'User Profile'
    fields = ('role', 'profile_picture')

class CustomUserAdmin(UserAdmin, ImportExportActionModelAdmin):
    inlines = (UserProfileInline,)
    list_display = ('email', 'first_name', 'last_name', 'get_role', 'get_company')
    actions = ['make_employer']

    def get_role(self, obj):
        try:
            role = obj.userprofile.role
            # Manual mapping instead of relying on get_role_display
            role_display = {
                'candidate': 'Candidate',
                'employer': 'Employer',
                'admin': 'Admin',
            }.get(role, role)
            return role_display
        except UserProfile.DoesNotExist:
            return '-'
    get_role.short_description = 'Role'

    def get_company(self, obj):
        try:
            if obj.userprofile.role == 'employer':
                return obj.userprofile.employer_profile.company_name
            return '-'
        except (UserProfile.DoesNotExist, EmployerProfile.DoesNotExist):
            return '-'
    get_company.short_description = 'Company'

    def make_employer(self, request, queryset):
        for user in queryset:
            try:
                profile = user.userprofile
            except UserProfile.DoesNotExist:
                profile = UserProfile.objects.create(user=user)
            
            profile.role = 'employer'
            profile.save()  # This will automatically create the EmployerProfile
        
        self.message_user(request, f"Successfully made {queryset.count()} users employers.")
    make_employer.short_description = "Make selected users employers"

# Unregister the default UserAdmin and register our custom one
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

@admin.register(EmployerProfile)
class EmployerProfileAdmin(ImportExportModelAdmin):
    resource_class = EmployerProfileResource
    list_display = ('company_name', 'get_employer_email', 'industry', 'company_size', 'location')
    search_fields = ('company_name', 'user_profile__user__email')
    list_filter = ('company_size', 'industry')

    def get_employer_email(self, obj):
        return obj.user_profile.user.email
    get_employer_email.short_description = 'Employer Email'

@admin.register(JobListing)
class JobListingAdmin(ImportExportModelAdmin):
    resource_class = JobListingResource
    list_display = ('title', 'company', 'get_employer', 'salary_range', 'location', 'premium_level', 'posted_at')
    list_filter = (('posted_at', DateRangeFilter), 'employer__company_name', 'location', 'premium_level', 'status')
    search_fields = ('title', 'company', 'description', 'location')
    date_hierarchy = 'posted_at'

    def salary_range(self, obj):
        if obj.salary_min and obj.salary_max:
            return f"{obj.salary_min} - {obj.salary_max} ₾ {obj.salary_type}"
        elif obj.salary_min:
            return f"{obj.salary_min} ₾ {obj.salary_type}"
        elif obj.salary_max:
            return f"{obj.salary_max} ₾ {obj.salary_type}"
        return '-'
    salary_range.short_description = 'Salary'

    def get_employer(self, obj):
        if obj.employer:
            return obj.employer.user_profile.user.email
        return '-'
    get_employer.short_description = 'Posted by'

@admin.register(JobApplication)
class JobApplicationAdmin(ImportExportModelAdmin):
    resource_class = JobApplicationResource
    list_display = ('get_job_title', 'get_company', 'get_applicant', 'status', 'applied_at')
    list_filter = (('applied_at', DateRangeFilter), 'status', 'job__title', 'job__company')
    search_fields = ('job__title', 'job__company', 'user__email', 'guest_name', 'guest_email')
    date_hierarchy = 'applied_at'
    
    def get_job_title(self, obj):
        return obj.job.title
    get_job_title.short_description = 'Job Title'
    
    def get_company(self, obj):
        return obj.job.company
    get_company.short_description = 'Company'
    
    def get_applicant(self, obj):
        if obj.user:
            return obj.user.email
        return f"{obj.guest_name} ({obj.guest_email})"
    get_applicant.short_description = 'Applicant'