from django.contrib import admin
from .models import News, NewsImage
from django.utils.html import format_html
from django.utils.safestring import mark_safe

class NewsImageInline(admin.TabularInline):
    model = News.image_gallery.through
    extra = 1
    verbose_name = "News Image"
    verbose_name_plural = "News Images"

@admin.register(NewsImage)
class NewsImageAdmin(admin.ModelAdmin):
    list_display = ('caption', 'display_image')
    search_fields = ('caption',)
    readonly_fields = ('display_image',)

    def display_image(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="100" height="100" style="object-fit: cover;" />', obj.image.url)
        return "No image"
    display_image.short_description = 'Image Preview'

@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'created_by', 'created_at', 'display_gallery', 'display_tags')
    list_filter = ('status', 'created_by', 'created_at')
    search_fields = ('title', 'content', 'tags__name')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at', 'display_gallery')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'content', 'status')
        }),
        ('Media', {
            'fields': ('image_gallery', 'display_gallery'),
            'classes': ('collapse',)
        }),
        ('Categorization', {
            'fields': ('tags',),
            'classes': ('collapse',)
        }),
        ('System Information', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def display_gallery(self, obj):
        images = obj.image_gallery.all()
        if not images:
            return "No images"
        
        html = '<div style="display: flex; flex-wrap: wrap; gap: 10px;">'
        for image in images:
            html += f'''
                <div style="text-align: center;">
                    <img src="{image.image.url}" width="150" height="150" style="object-fit: cover;" />
                    <p>{image.caption or "No caption"}</p>
                </div>
            '''
        html += '</div>'
        return mark_safe(html)
    display_gallery.short_description = 'Image Gallery Preview'

    def display_tags(self, obj):
        return ", ".join([tag.name for tag in obj.tags.all()])
    display_tags.short_description = 'Tags'

    def save_model(self, request, obj, form, change):
        if not change:  # If creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

# Register your models here.
