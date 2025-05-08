from django.contrib import admin
from .models import Job

@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ('job_title', 'company_name', 'location', 'status', 'created_at', 'application_deadline')
    list_filter = ('status', 'employment_type', 'experience_level', 'remote_work', 'created_at')
    search_fields = ('job_title', 'company_name', 'description', 'requirements', 'location')
    readonly_fields = ('created_at', 'updated_at', 'views_count', 'applications_count')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('job_title', 'company_name', 'company_website', 'location', 'country', 'remote_work')
        }),
        ('Contact Information', {
            'fields': ('first_name', 'last_name', 'email', 'phone')
        }),
        ('Job Details', {
            'fields': ('description', 'requirements', 'responsibilities', 'benefits')
        }),
        ('Compensation', {
            'fields': ('compensation_type', 'compensation_amount', 'compensation_currency')
        }),
        ('Requirements', {
            'fields': ('employment_type', 'experience_level', 'education_level', 'skills_required', 'languages_required')
        }),
        ('Project Information', {
            'fields': ('project_type', 'project_duration', 'start_date')
        }),
        ('Organization', {
            'fields': ('organization_type', 'industry', 'company_size')
        }),
        ('Status and Dates', {
            'fields': ('status', 'application_deadline', 'created_at', 'updated_at')
        }),
        ('Statistics', {
            'fields': ('views_count', 'applications_count', 'is_featured')
        }),
    )
