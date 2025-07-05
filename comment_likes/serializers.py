from rest_framework import serializers
from .models import CommentReaction
from userprofile.serializers import ProfileSerializer

class CommentReactionSerializer(serializers.ModelSerializer):
    user_profile = ProfileSerializer(source='user.profile', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    user = serializers.UUIDField(source='user.id', read_only=True)

    class Meta:
        model = CommentReaction
        fields = ['id', 'comment', 'user', 'is_dislike', 'created_at', 'user_profile', 'username']
        read_only_fields = ['id', 'created_at', 'user_profile', 'username', 'user']

class CommentReactionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommentReaction
        fields = ['comment', 'is_dislike']

    def validate(self, data):
        if 'comment' in data:
            user = self.context['request'].user
            comment = data['comment']
            is_dislike = data.get('is_dislike', self.instance.is_dislike if self.instance else False)

            existing_reaction = CommentReaction.objects.filter(
                comment=comment,
                user=user
            ).exclude(pk=getattr(self.instance, 'pk', None)).first()

            if existing_reaction:
                if existing_reaction.is_dislike == is_dislike:
                    raise serializers.ValidationError(
                        f"You have already {'disliked' if is_dislike else 'liked'} this comment"
                    )
                existing_reaction.delete()

        return data

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
