from django.contrib import admin
from .models import Job, Application
from django.contrib.auth.models import User

# Custom admin class for Job model
class JobAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Job model, customizing the display and filtering options.
    """
    list_display = ('job_title', 'company_name', 'user_id', 'project_type', 'created_at', 'applicant_count')
    list_filter = ('project_type', 'organization_type', 'country', 'created_at')
    search_fields = ('job_title', 'company_name', 'talents', 'project_title')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'user_id')

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

    def save_model(self, request, obj, form, change):
        """
        Ensure the user_id is set to the current user on creation.
        """
        if not change:  # Only set user_id on creation, not update
            obj.user_id = request.user
        super().save_model(request, obj, form, change)

# Custom admin class for Application model
class ApplicationAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Application model, customizing the display and filtering options.
    """
    list_display = ('user', 'job', 'applied_at', 'opportunity_description_short')
    list_filter = ('applied_at',)
    search_fields = ('user__email', 'job__job_title', 'opportunity_description')
    readonly_fields = ('applied_at', 'user', 'job')

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
        return queryset.select_related('user', 'job')

# Register the models with their admin classes
admin.site.register(Job, JobAdmin)
admin.site.register(Application, ApplicationAdmin)