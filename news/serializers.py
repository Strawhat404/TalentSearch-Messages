from rest_framework import serializers
from .models import News

class NewsSerializer(serializers.ModelSerializer):
    class Meta:
        model = News
        fields = ['id','title','date','category','image','created_at','content']
        read_only_fields = ['id','created_at','content']
        