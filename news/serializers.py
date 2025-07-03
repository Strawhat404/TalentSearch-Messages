# from rest_framework import serializers
# from .models import News, NewsImage
# from django.utils import timezone
#
#
# class NewsImageSerializer(serializers.ModelSerializer):
#     image = serializers.ImageField(allow_null=True, required=False)
#
#     class Meta:
#         model = NewsImage
#         fields = ['id', 'image', 'caption']
#
#
# class NewsSerializer(serializers.ModelSerializer):
#     created_by = serializers.StringRelatedField(read_only=True)
#     image_gallery = NewsImageSerializer(many=True, read_only=True)
#     tags = serializers.SerializerMethodField()
#
#     # New fields for direct image upload
#     images = serializers.ListField(
#         child=serializers.ImageField(allow_empty_file=False, use_url=False),
#         write_only=True,
#         required=False,
#         help_text="Upload multiple images for the news article"
#     )
#     image_captions = serializers.ListField(
#         child=serializers.CharField(max_length=255, allow_blank=True),
#         write_only=True,
#         required=False,
#         help_text="Optional captions for the images (must match the number of images)"
#     )
#
#     title = serializers.CharField(
#         max_length=255,
#         help_text="Enter a concise news title (max 255 characters)",
#         error_messages={
#             'blank': 'Title cannot be empty',
#             'max_length': 'Title cannot be longer than 255 characters'
#         }
#     )
#
#     content = serializers.CharField(
#         help_text="Provide the full news content",
#         error_messages={
#             'blank': 'Content cannot be empty'
#         }
#     )
#
#     status = serializers.ChoiceField(
#         choices=News.STATUS_CHOICES,
#         default='draft',
#         help_text="Current status of the news article"
#     )
#
#     def get_tags(self, obj):
#         return [tag.name for tag in obj.tags.all()]
#
#     def get_created_by(self, obj):
#         return {
#             'id': obj.created_by.id if obj.created_by else None,
#             'username': obj.created_by.username if obj.created_by else None
#         }
#
#     def validate(self, data):
#         """
#         Validate the news data including images
#         """
#         # Existing validation
#         if data.get('status') == 'published' and not data.get('content'):
#             raise serializers.ValidationError({
#                 'content': 'Content is required for published news'
#             })
#
#         # Validate images and captions
#         images = data.get('images', [])
#         captions = data.get('image_captions', [])
#
#         if images and captions and len(images) != len(captions):
#             raise serializers.ValidationError({
#                 'image_captions': 'Number of captions must match the number of images'
#             })
#
#         # Validate maximum number of images (optional limit)
#         if len(images) > 10:
#             raise serializers.ValidationError({
#                 'images': 'Maximum of 10 images allowed per news article'
#             })
#
#         return data
#
#     def create(self, validated_data):
#         """
#         Create news with associated images
#         """
#         images_data = validated_data.pop('images', [])
#         captions_data = validated_data.pop('image_captions', [])
#
#         # Create the news article
#         news = News.objects.create(**validated_data)
#
#         # Create and associate images with error handling for size
#         for i, image_data in enumerate(images_data):
#             try:
#                 caption = captions_data[i] if i < len(captions_data) else ""
#                 news_image = NewsImage.objects.create(
#                     image=image_data,
#                     caption=caption
#                 )
#                 news.image_gallery.add(news_image)
#             except ValidationError as e:
#                 if 'image' in e.message_dict and 'Image size must be no more than 5MB' in str(e):
#                     raise serializers.ValidationError({
#                         'images': [f'Image {i + 1} exceeds the 5MB size limit.']
#                     })
#                 raise  # Re-raise other validation errors
#
#         return news
#
#     def update(self, instance, validated_data):
#         """
#         Update news and handle image updates
#         """
#         images_data = validated_data.pop('images', None)
#         captions_data = validated_data.pop('image_captions', [])
#
#         # Update news fields
#         for attr, value in validated_data.items():
#             setattr(instance, attr, value)
#         instance.save()
#
#         # Handle image updates if provided
#         if images_data is not None:
#             # Note: This replaces all images. For append functionality,
#             # you might want to modify this logic
#             for i, image_data in enumerate(images_data):
#                 try:
#                     caption = captions_data[i] if i < len(captions_data) else ""
#                     news_image = NewsImage.objects.create(
#                         image=image_data,
#                         caption=caption
#                     )
#                     instance.image_gallery.add(news_image)
#                 except ValidationError as e:
#                     if 'image' in e.message_dict and 'Image size must be no more than 5MB' in str(e):
#                         raise serializers.ValidationError({
#                             'images': [f'Image {i + 1} exceeds the 5MB size limit.']
#                         })
#                     raise  # Re-raise other validation errors
#
#         return instance
#
#     class Meta:
#         model = News
#         fields = ['id', 'title', 'content', 'created_by', 'created_at',
#                   'updated_at', 'status', 'image_gallery', 'tags', 'images', 'image_captions']
#         read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']


from rest_framework import serializers
from rest_framework.exceptions import ValidationError  # Added import
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

    # New fields for direct image upload
    images = serializers.ListField(
        child=serializers.ImageField(allow_empty_file=False, use_url=False),
        write_only=True,
        required=False,
        help_text="Upload multiple images for the news article"
    )
    image_captions = serializers.ListField(
        child=serializers.CharField(max_length=255, allow_blank=True),
        write_only=True,
        required=False,
        help_text="Optional captions for the images (must match the number of images)"
    )

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
        Validate the news data including images
        """
        if data.get('status') == 'published' and not data.get('content'):
            raise serializers.ValidationError({
                'content': 'Content is required for published news'
            })

        images = data.get('images', [])
        captions = data.get('image_captions', [])

        if images and captions and len(images) != len(captions):
            raise serializers.ValidationError({
                'image_captions': 'Number of captions must match the number of images'
            })

        if len(images) > 10:
            raise serializers.ValidationError({
                'images': 'Maximum of 10 images allowed per news article'
            })

        return data

    def create(self, validated_data):
        """
        Create news with associated images
        """
        images_data = validated_data.pop('images', [])
        captions_data = validated_data.pop('image_captions', [])

        news = News.objects.create(**validated_data)

        for i, image_data in enumerate(images_data):
            try:
                caption = captions_data[i] if i < len(captions_data) else ""
                news_image = NewsImage.objects.create(
                    image=image_data,
                    caption=caption
                )
                news.image_gallery.add(news_image)
            except ValidationError as e:
                if 'image' in e.message_dict and 'Image size must be no more than 5MB' in str(e):
                    raise serializers.ValidationError({
                        'images': [f'Image {i + 1} exceeds the 5MB size limit.']
                    })
                raise

        return news

    def update(self, instance, validated_data):
        """
        Update news and handle image updates
        """
        images_data = validated_data.pop('images', None)
        captions_data = validated_data.pop('image_captions', [])

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if images_data is not None:
            for i, image_data in enumerate(images_data):
                try:
                    caption = captions_data[i] if i < len(captions_data) else ""
                    news_image = NewsImage.objects.create(
                        image=image_data,
                        caption=caption
                    )
                    instance.image_gallery.add(news_image)
                except ValidationError as e:
                    if 'image' in e.message_dict and 'Image size must be no more than 5MB' in str(e):
                        raise serializers.ValidationError({
                            'images': [f'Image {i + 1} exceeds the 5MB size limit.']
                        })
                    raise

        return instance

    class Meta:
        model = News
        fields = ['id', 'title', 'content', 'created_by', 'created_at',
                  'updated_at', 'status', 'image_gallery', 'tags', 'images', 'image_captions']
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']