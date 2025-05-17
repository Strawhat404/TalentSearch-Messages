from django.contrib import admin
from .models import Job

@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'user_id', 'job_title', 'company_name', 'country',
        'project_type', 'organization_type', 'project_start_date',
        'project_end_date', 'compensation_type', 'created_at'
    )
    list_filter = ('country', 'project_type', 'organization_type', 'compensation_type')
    search_fields = ('job_title', 'company_name', 'user_id__username', 'project_title', 'talents')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at',)

    fieldsets = (
        ('Basic Info', {
            'fields': ('user_id', 'job_title', 'company_name', 'company_website', 'country', 'postal_code')
        }),
        ('Talent & Project Details', {
            'fields': ('talents', 'project_type', 'organization_type', 'project_title', 'project_details')
        }),
        ('Dates & Compensation', {
            'fields': ('project_start_date', 'project_end_date', 'compensation_type', 'compensation_amount')
        }),
        ('Contact Info', {
            'fields': ('first_name', 'last_name')
        }),
        ('Meta', {
            'fields': ('created_at',)
        }),
    )
