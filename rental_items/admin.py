from django.contrib import admin
from .models import RentalItem, RentalItemImage, RentalItemRating, Wishlist
from django.utils.html import format_html

class RentalItemImageInline(admin.TabularInline):
    model = RentalItemImage
    extra = 1
    readonly_fields = ('image_preview', 'created_at')
    fields = ('image', 'image_preview')
    show_change_link = True
    can_delete = True

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="100" height="100" style="object-fit: cover;" />', obj.image.url)
        return "No image"
    image_preview.short_description = 'Preview'

@admin.register(RentalItem)
class RentalItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'category', 'daily_rate', 'available', 'featured_item', 'approved', 'created_at', 'main_image_preview')
    list_filter = ('type', 'category', 'available', 'featured_item', 'approved', 'created_at')
    search_fields = ('name', 'description', 'specs')
    readonly_fields = ('main_image_preview', 'created_at')
    inlines = [RentalItemImageInline]
    
    def get_fieldsets(self, request, obj=None):
        fieldsets = [
            (None, {
                'fields': ('name', 'type', 'category', 'description', 'daily_rate', 'image', 'main_image_preview', 'specs', 'available', 'featured_item', 'approved', 'user')
            })
        ]
        if obj:  # Only show created_at in change view
            fieldsets.append(('Dates', {
                'fields': ('created_at',),
                'classes': ('collapse',)
            }))
        return fieldsets

    def main_image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="150" height="150" style="object-fit: cover;" />', obj.image.url)
        return "No image"
    main_image_preview.short_description = 'Main Image Preview'

@admin.register(RentalItemImage)
class RentalItemImageAdmin(admin.ModelAdmin):
    list_display = ('rental_item', 'image_preview', 'created_at')
    readonly_fields = ('image_preview',)

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="100" height="100" style="object-fit: cover;" />', obj.image.url)
        return "No image"
    image_preview.short_description = 'Preview'

@admin.register(RentalItemRating)
class RentalItemRatingAdmin(admin.ModelAdmin):
    list_display = ('rental_item', 'user', 'rating', 'comment', 'created_at')
    search_fields = ('rental_item__name', 'user__email', 'comment')
    list_filter = ('rating', 'created_at')

@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'rental_item', 'created_at')
    search_fields = ('user__email', 'rental_item__name')
    list_filter = ('created_at',)
    readonly_fields = ('created_at',)
