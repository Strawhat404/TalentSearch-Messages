from django.contrib import admin
from .models import Profile

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('name', 'profession', 'location', 'created_at')
    list_filter = ('profession', 'gender', 'created_at')
    search_fields = ('name', 'profession', 'bio', 'location')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'name', 'birthdate', 'gender', 'nationality')
        }),
        ('Physical Attributes', {
            'fields': ('weight', 'height')
        }),
        ('Professional Information', {
            'fields': ('profession', 'skills', 'languages')
        }),
        ('Personal Details', {
            'fields': ('bio', 'interests', 'location', 'timezone')
        }),
        ('Media', {
            'fields': ('profile_picture', 'cover_photo')
        }),
        ('Social & Preferences', {
            'fields': ('social_links', 'preferences')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    ) 