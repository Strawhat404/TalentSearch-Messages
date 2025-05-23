from django.contrib import admin
from .models import Rating

@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ('item_id', 'user', 'rating', 'comment', 'created_at')
    search_fields = ('item_id', 'user__email', 'comment')
    list_filter = ('rating', 'created_at')
