from rest_framework import serializers
from .models import Advert

class AdvertSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Advert
        fields = [
            'id', 'image', 'title', 'video', 'created_at', 'description',
            'created_by', 'updated_at', 'status', 'location', 'run_from', 'run_to'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']