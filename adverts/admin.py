from django.contrib import admin
from .models import Advert

@admin.register(Advert)
class AdvertAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_by', 'status', 'location', 'run_from', 'run_to', 'created_at')
    list_filter = ('status', 'created_by', 'run_from', 'run_to', 'created_at')
    search_fields = ('title', 'description', 'location')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    readonly_fields = ('id', 'created_at', 'updated_at')