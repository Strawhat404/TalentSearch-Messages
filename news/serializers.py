from rest_framework import serializers
form .models import News

class NewsSerializers(serializers.ModelSerializer):
    class Meta:
        model = News
        fields = ['id','title','date','category','image','created_at']
        read_only_fields = ['id','created_at']
        