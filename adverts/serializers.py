from rest_framework import serializers
from .models import Adver

class AdvertSerializer(serializers.ModelSerializer):
    class Meta:
        model = Advert
        fields = ['id', 'image', 'title', 'video', 'created_at']