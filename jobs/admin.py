# from django.contrib import admin
# from .models import Job, Application
# from django.contrib.auth.models import User
# from django.db.models import Count
#
# # Inline admin for displaying Applications related to a Job
# class ApplicationInline(admin.TabularInline):
#     """
#     Inline admin to display read-only applicant information for a specific job.
#     """
#     model = Application
#     fields = ('user', 'opportunity_description', 'applied_at')
#     readonly_fields = ('user', 'opportunity_description', 'applied_at')
#     extra = 0  # No extra empty forms for adding new applications
#     can_delete = False  # Prevent deletion
#     can_add = False  # Prevent adding new applications
#
#     def has_add_permission(self, request, obj=None):
#         return False
#
#     def has_delete_permission(self, request, obj=None):
#         return False
#
#     def has_change_permission(self, request, obj=None):
#         return False
#
# # Custom admin class for Job model
# class JobAdmin(admin.ModelAdmin):
#     """
#     Admin configuration for the Job model, customizing the display and filtering options.
#     """
#     list_display = ('job_title', 'company_name', 'user_id', 'project_type', 'created_at', 'applicant_count')
#     list_filter = ('project_type', 'organization_type', 'country', 'created_at')
#     search_fields = ('job_title', 'company_name', 'talents', 'project_title')
#     date_hierarchy = 'created_at'
#     readonly_fields = ('created_at', 'user_id')
#     inlines = [ApplicationInline]  # Add the inline to display applicants
#
#     def applicant_count(self, obj):
#         """
#         Display the number of applicants for a job in the admin list.
#         """
#         return obj.application_set.count()
#     applicant_count.short_description = 'Applicants'
#
#     def get_queryset(self, request):
#         """
#         Annotate the queryset with applicant count for efficient display.
#         """
#         queryset = super().get_queryset(request)
#         return queryset.annotate(applicant_count=Count('application'))
#
#     def save_model(self, request, obj, form, change):
#         """
#         Ensure the user_id is set to the current user on creation.
#         """
#         if not change:  # Only set user_id on creation, not update
#             obj.user_id = request.user
#         super().save_model(request, obj, form, change)
#
# # Custom admin class for Application model
# class ApplicationAdmin(admin.ModelAdmin):
#     """
#     Admin configuration for the Application model, customizing the display and filtering options.
#     """
#     list_display = ('user', 'job', 'applied_at', 'opportunity_description_short')
#     list_filter = ('applied_at',)
#     search_fields = ('user__email', 'job__job_title', 'opportunity_description')
#     readonly_fields = ('applied_at',)
#     fields = ('user', 'job', 'opportunity_description', 'applied_at')
#
#     def opportunity_description_short(self, obj):
#         """
#         Display a truncated version of the opportunity description in the admin list.
#         """
#         return obj.opportunity_description[:50] + '...' if len(obj.opportunity_description) > 50 else obj.opportunity_description
#     opportunity_description_short.short_description = 'Opportunity Description'
#
#     def get_queryset(self, request):
#         """
#         Prefetch related data for efficient display.
#         """
#         queryset = super().get_queryset(request)
#         return queryset.select_related('user', 'job')
#
#     def save_model(self, request, obj, form, change):
#         """
#         Set the user to the current admin user on creation if not provided.
#         """
#         if not change and not obj.user_id:  # Only set user_id on creation if not already set
#             obj.user = request.user
#         super().save_model(request, obj, form, change)
#
#     def has_change_permission(self, request, obj=None):
#         """
#         Restrict changes to Application instances in admin.
#         """
#         return False
#
#     def has_delete_permission(self, request, obj=None):
#         """
#         Restrict deletion of Application instances in admin.
#         """
#         return False
#
# # Register the models with their admin classes
# admin.site.register(Job, JobAdmin)
# admin.site.register(Application, ApplicationAdmin)


from django.contrib import admin
from .models import Job, Application
from django.db.models import Count

# Inline admin for displaying Applications related to a Job
class ApplicationInline(admin.TabularInline):
    """
    Inline admin to display read-only applicant information for a specific job.
    """
    model = Application
    fields = ('profile_id', 'opportunity_description', 'applied_at')
    readonly_fields = ('profile_id', 'opportunity_description', 'applied_at')
    extra = 0
    can_delete = False
    can_add = False

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def profile_id(self, obj):
        """Display the profile name instead of the raw ID, or 'No Profile' if null."""
        return obj.profile_id.name if obj.profile_id else "No Profile"
    profile_id.short_description = 'Applicant Profile'

# Custom admin class for Job model
class JobAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Job model, customizing the display and filtering options.
    """
    list_display = ('job_title', 'company_name', 'profile_id', 'project_type', 'created_at', 'applicant_count')
    list_filter = ('project_type', 'organization_type', 'country', 'created_at')
    search_fields = ('job_title', 'company_name', 'talents', 'project_title', 'profile_id__user__email')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'profile_id')
    inlines = [ApplicationInline]

    def applicant_count(self, obj):
        """
        Display the number of applicants for a job in the admin list.
        """
        return obj.application_set.count()
    applicant_count.short_description = 'Applicants'

    def get_queryset(self, request):
        """
        Annotate the queryset with applicant count for efficient display.
        """
        queryset = super().get_queryset(request)
        return queryset.annotate(applicant_count=Count('application'))

    def profile_id(self, obj):
        """Display the profile name instead of the raw ID, or 'No Profile' if null."""
        return obj.profile_id.name if obj.profile_id else "No Profile"
    profile_id.short_description = 'Profile'

    def save_model(self, request, obj, form, change):
        """
        Ensure the profile_id is set to the current user's profile on creation if it exists.
        """
        if not change and not obj.profile_id and hasattr(request.user, 'profile'):
            obj.profile_id = request.user.profile
        super().save_model(request, obj, form, change)

# Custom admin class for Application model
class ApplicationAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Application model, customizing the display and filtering options.
    """
    list_display = ('profile_id', 'job', 'applied_at', 'opportunity_description_short')
    list_filter = ('applied_at',)
    search_fields = ('profile_id__user__email', 'job__job_title', 'opportunity_description')
    readonly_fields = ('applied_at',)
    fields = ('profile_id', 'job', 'opportunity_description', 'applied_at')

    def opportunity_description_short(self, obj):
        """
        Display a truncated version of the opportunity description in the admin list.
        """
        return obj.opportunity_description[:50] + '...' if len(obj.opportunity_description) > 50 else obj.opportunity_description
    opportunity_description_short.short_description = 'Opportunity Description'

    def get_queryset(self, request):
        """
        Prefetch related data for efficient display.
        """
        queryset = super().get_queryset(request)
        return queryset.select_related('profile_id', 'job')

    def profile_id(self, obj):
        """Display the profile name instead of the raw ID, or 'No Profile' if null."""
        return obj.profile_id.name if obj.profile_id else "No Profile"
    profile_id.short_description = 'Applicant Profile'

    def save_model(self, request, obj, form, change):
        """
        Set the profile_id to the current admin user's profile on creation if it exists.
        """
        if not change and not obj.profile_id and hasattr(request.user, 'profile'):
            obj.profile_id = request.user.profile
        super().save_model(request, obj, form, change)

    def has_change_permission(self, request, obj=None):
        """
        Restrict changes to Application instances in admin.
        """
        return False

    def has_delete_permission(self, request, obj=None):
        """
        Restrict deletion of Application instances in admin.
        """
        return False

# Register the models with their admin classes
admin.site.register(Job, JobAdmin)
admin.site.register(Application, ApplicationAdmin)