from rest_framework import serializers
from .models import News

class NewsSerializer(serializers.ModelSerializer):
    class Meta:
        model = News
        fields = ['id', 'title', 'content', 'created_by', 'created_at', 'updated_at', 'status', 'image_gallery', 'tags']