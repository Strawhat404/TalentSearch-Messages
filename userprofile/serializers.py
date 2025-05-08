from rest_framework import serializers
from .models import Profile
from django.contrib.auth import get_user_model

User = get_user_model()

class ProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)
    age = serializers.IntegerField(read_only=True)

    class Meta:
        model = Profile
        fields = [
            'id', 'user', 'email', 'name', 'birthdate', 'age', 'weight',
            'height', 'gender', 'nationality', 'languages', 'profession',
            'skills', 'interests', 'bio', 'profile_picture', 'cover_photo',
            'social_links', 'location', 'timezone', 'preferences',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at']

    def validate_birthdate(self, value):
        if value and value.year < 1900:
            raise serializers.ValidationError("Birthdate cannot be before 1900")
        return value

    def validate_weight(self, value):
        if value is not None and value <= 0:
            raise serializers.ValidationError("Weight must be positive")
        return value

    def validate_height(self, value):
        if value is not None and value <= 0:
            raise serializers.ValidationError("Height must be positive")
        return value 