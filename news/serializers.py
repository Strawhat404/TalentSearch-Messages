from rest_framework import serializers
from .models import News, NewsImage
from django.utils import timezone

class NewsImageSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(allow_null=True, required=False)
    class Meta:
        model = NewsImage
        fields = ['id', 'image', 'caption']

class NewsSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField(read_only=True)
    image_gallery = NewsImageSerializer(many=True, read_only=True)
    tags = serializers.SerializerMethodField()

    title = serializers.CharField(
        max_length=255,
        help_text="Enter a concise news title (max 255 characters)",
        error_messages={
            'blank': 'Title cannot be empty',
            'max_length': 'Title cannot be longer than 255 characters'
        }
    )

    content = serializers.CharField(
        help_text="Provide the full news content",
        error_messages={
            'blank': 'Content cannot be empty'
        }
    )

    status = serializers.ChoiceField(
        choices=News.STATUS_CHOICES,
        default='draft',
        help_text="Current status of the news article"
    )

    def get_tags(self, obj):
        return [tag.name for tag in obj.tags.all()]

    def get_created_by(self, obj):
        return {
            'id': obj.created_by.id if obj.created_by else None,
            'username': obj.created_by.username if obj.created_by else None
        }

    def validate(self, data):
        """
        Validate the news data
        """
        # Add any custom validation here
        if data.get('status') == 'published' and not data.get('content'):
            raise serializers.ValidationError({
                'content': 'Content is required for published news'
            })
        return data

    class Meta:
        model = News
        fields = ['id', 'title', 'content', 'created_by', 'created_at', 
                 'updated_at', 'status', 'image_gallery', 'tags']
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']