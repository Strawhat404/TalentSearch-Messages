from django.contrib import admin
from .models import Advert
from django.utils.html import format_html

@admin.register(Advert)
class AdvertAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_by', 'status', 'location', 'run_from', 'run_to', 'created_at', 'display_image', 'display_video')
    list_filter = ('status', 'created_by', 'run_from', 'run_to', 'created_at')
    search_fields = ('title', 'description', 'location')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    readonly_fields = ('id', 'created_at', 'updated_at', 'display_image', 'display_video')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'status', 'location')
        }),
        ('Media', {
            'fields': ('image', 'video', 'display_image', 'display_video'),
            'classes': ('collapse',)
        }),
        ('Campaign Details', {
            'fields': ('run_from', 'run_to'),
            'classes': ('collapse',)
        }),
        ('System Information', {
            'fields': ('id', 'created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def display_image(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" style="object-fit: cover;" />', obj.image.url)
        return "No image"
    display_image.short_description = 'Image Preview'

    def display_video(self, obj):
        if obj.video:
            return format_html('<a href="{}" target="_blank">View Video</a>', obj.video.url)
        return "No video"
    display_video.short_description = 'Video'

    def save_model(self, request, obj, form, change):
        if not change:  # If creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)