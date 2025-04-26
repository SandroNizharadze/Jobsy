from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import JobListing, UserProfile, EmployerProfile

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'User Profile'
    fields = ('role', 'profile_picture', 'interests', 'fields', 'experience', 'job_preferences')

class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('email', 'first_name', 'last_name', 'get_role', 'get_company')
    actions = ['make_employer']

    def get_role(self, obj):
        try:
            return obj.userprofile.get_role_display()
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
class EmployerProfileAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'get_employer_email', 'industry', 'company_size', 'location')
    search_fields = ('company_name', 'user_profile__user__email')
    list_filter = ('company_size', 'industry')

    def get_employer_email(self, obj):
        return obj.user_profile.user.email
    get_employer_email.short_description = 'Employer Email'

@admin.register(JobListing)
class JobListingAdmin(admin.ModelAdmin):
    list_display = ('title', 'company', 'get_employer', 'experience', 'posted_at')
    list_filter = ('experience', 'employer__company_name')
    search_fields = ('title', 'company', 'description')
    date_hierarchy = 'posted_at'

    def get_employer(self, obj):
        if obj.employer:
            return obj.employer.user_profile.user.email
        return '-'
    get_employer.short_description = 'Posted by'