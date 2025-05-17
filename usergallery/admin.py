from django.contrib import admin
from .models import GalleryItem
from django.utils.html import format_html
from django.urls import reverse
from django.contrib.admin import SimpleListFilter
import os
from django import forms
from django.core.exceptions import ValidationError

# Custom filter to show items by profile name
class ProfileNameFilter(SimpleListFilter):
    title = 'Profile Name'
    parameter_name = 'profile_name'

    def lookups(self, request, model_admin):
        profiles = set(item.profile_id for item in GalleryItem.objects.all())
        return [(profile.id, profile.name) for profile in profiles]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(profile_id=self.value())
        return queryset

# Custom form for GalleryItem with validation
class GalleryItemForm(forms.ModelForm):
    class Meta:
        model = GalleryItem
        fields = '__all__'

    def clean_item_url(self):
        item_url = self.cleaned_data.get('item_url')
        if item_url:
            valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.mp4', '.avi', '.mov', '.mkv']
            ext = os.path.splitext(item_url.name)[1].lower()
            if ext not in valid_extensions:
                raise ValidationError('File must be an image (.jpg, .jpeg, .png, .gif) or video (.mp4, .avi, .mov, .mkv).')
            if item_url.size > 50 * 1024 * 1024:  # 50MB limit
                raise ValidationError('File size must not exceed 50MB.')
        return item_url

# Custom admin class for GalleryItem
@admin.register(GalleryItem)
class GalleryItemAdmin(admin.ModelAdmin):
    """
    Admin configuration for the GalleryItem model, providing a detailed and user-friendly interface.
    """
    list_display = ('id', 'profile_link', 'item_url_preview', 'item_type', 'description', 'created_at', 'updated_at')
    list_filter = ('item_type', 'created_at', ProfileNameFilter)
    search_fields = ('description', 'profile_id__name', 'profile_id__user__email')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')
    form = GalleryItemForm  # Use the custom form

    # Custom fields for display
    def profile_link(self, obj):
        """
        Display a clickable link to the associated profile in the admin.
        """
        url = reverse('admin:userprofile_profile_change', args=[obj.profile_id.id])
        return format_html('<a href="{}">{}</a>', url, obj.profile_id.name)
    profile_link.short_description = 'Profile'

    def item_url_preview(self, obj):
        """
        Display a preview of the item_url (image thumbnail or video icon) with a link.
        """
        if obj.item_url:
            if obj.item_type == 'image':
                return format_html(
                    '<a href="{}" target="_blank"><img src="{}" style="max-height: 100px; max-width: 100px;" /></a>',
                    obj.item_url.url, obj.item_url.url
                )
            else:
                return format_html(
                    '<a href="{}" target="_blank">Video</a>',
                    obj.item_url.url
                )
        return "No file"
    item_url_preview.short_description = 'Item Preview'

    # Customize the change form
    fieldsets = (
        (None, {
            'fields': ('profile_id', 'item_url', 'item_type', 'description')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    # Allow adding/editing multiple items at once
    list_editable = ('description',)

    # Prepopulate fields on add
    prepopulated_fields = {'description': ('item_type',)}

    # Custom actions
    actions = ['delete_selected']

    def get_queryset(self, request):
        """
        Optimize queryset with select_related for profile data.
        """
        qs = super().get_queryset(request)
        return qs.select_related('profile_id', 'profile_id__user')

    def save_model(self, request, obj, form, change):
        """
        Ensure item_type is updated based on file extension if changed, and delete old file if updated.
        """
        # Fetch the old file path if this is an update
        old_item = GalleryItem.objects.get(id=obj.id) if change else None
        old_file_path = old_item.item_url.path if old_item and old_item.item_url else None

        if obj.item_url:
            ext = os.path.splitext(obj.item_url.name)[1].lower()
            if ext in ['.jpg', '.jpeg', '.png', '.gif']:
                obj.item_type = 'image'
            elif ext in ['.mp4', '.avi', '.mov', '.mkv']:
                obj.item_type = 'video'

        # Save the new file to get the new file path
        super().save_model(request, obj, form, change)

        # After saving, delete the old file if a new file was uploaded and paths differ
        if change and old_file_path and obj.item_url and old_file_path != obj.item_url.path and os.path.isfile(old_file_path):
            os.remove(old_file_path)

    def delete_model(self, request, obj):
        """
        Delete the associated file from the filesystem before deleting the model.
        """
        if obj.item_url and os.path.isfile(obj.item_url.path):
            os.remove(obj.item_url.path)
        super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        """
        Handle bulk deletion of items and their files.
        """
        for obj in queryset:
            if obj.item_url and os.path.isfile(obj.item_url.path):
                os.remove(obj.item_url.path)
        queryset.delete()