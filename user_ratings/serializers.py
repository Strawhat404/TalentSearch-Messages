from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import UserRating
from userprofile.models import Profile, ProfessionsAndSkills
from django.core.files.storage import default_storage

User = get_user_model()

class RaterProfileSerializer(serializers.ModelSerializer):
    photo_url = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = ['name', 'photo_url', 'profession']

    def get_photo_url(self, obj):
        """
        Get the URL of the profile's photo from the related Headshot object.
        """
        try:
            if hasattr(obj, 'headshot') and obj.headshot and obj.headshot.professional_headshot:
                return obj.headshot.professional_headshot.url
        except:
            pass
        return None

    def get_profession(self, obj):
        """
        Get the list of professions from the related ProfessionsAndSkills object.
        Returns an empty list if no professions are available.
        """
        try:
            professions_and_skills = obj.professions_and_skills
            if professions_and_skills and professions_and_skills.professions:
                return professions_and_skills.professions  # Returns the full list
        except ProfessionsAndSkills.DoesNotExist:
            pass
        return []

class UserRatingSerializer(serializers.ModelSerializer):
    rater_profile = RaterProfileSerializer(source='rater_profile_id', read_only=True)
    rater_username = serializers.CharField(source='rating_user_id.username', read_only=True)
    rated_username = serializers.CharField(source='rated_user_id.username', read_only=True)

    class Meta:
        model = UserRating
        fields = [
            'id', 'rating_user_id', 'rated_user_id', 'rating', 'feedback',
            'created_at', 'updated_at', 'rater_profile_id', 'rated_profile_id',
            'rater_profile', 'rater_username', 'rated_username'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'rater_profile', 'rater_username', 'rated_username']

    def validate_rating_user_id(self, value):
        """
        Ensure rating_user_id is not blank and exists.
        """
        if not value:
            raise serializers.ValidationError("rating_user_id cannot be blank.")
        if not User.objects.filter(id=value.id).exists():
            raise serializers.ValidationError("rating_user_id does not exist.")
        return value

    def validate_rated_user_id(self, value):
        """
        Ensure rated_user_id is not blank and exists.
        """
        if not value:
            raise serializers.ValidationError("rated_user_id cannot be blank.")
        if not User.objects.filter(id=value.id).exists():
            raise serializers.ValidationError("rated_user_id does not exist.")
        return value

    def validate_rater_profile_id(self, value):
        """
        Ensure rater_profile_id is not blank and exists.
        """
        if not value:
            raise serializers.ValidationError("rater_profile_id cannot be blank.")
        if not Profile.objects.filter(id=value.id).exists():
            raise serializers.ValidationError("rater_profile_id does not exist.")
        return value

    def validate_rated_profile_id(self, value):
        """
        Ensure rated_profile_id is not blank and exists.
        """
        if not value:
            raise serializers.ValidationError("rated_profile_id cannot be blank.")
        if not Profile.objects.filter(id=value.id).exists():
            raise serializers.ValidationError("rated_profile_id does not exist.")
        return value

    def validate_rating(self, value):
        """
        Ensure rating is between 1 and 5.
        """
        if value is None:
            raise serializers.ValidationError("rating cannot be blank.")
        if not isinstance(value, int) or value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be an integer between 1 and 5.")
        return value

    def validate(self, data):
        """
        Ensure rating_user_id matches rater_profile_id's user and
        rated_user_id matches rated_profile_id's user.
        Also check if a rating already exists for this user pair during creation.
        """
        rating_user_id = data.get('rating_user_id')
        rater_profile_id = data.get('rater_profile_id')
        rated_user_id = data.get('rated_user_id')
        rated_profile_id = data.get('rated_profile_id')

        if rating_user_id and rater_profile_id and rating_user_id != rater_profile_id.user:
            raise serializers.ValidationError({
                'rating_user_id': 'rating_user_id must match the user of rater_profile_id.'
            })
        if rated_user_id and rated_profile_id and rated_user_id != rated_profile_id.user:
            raise serializers.ValidationError({
                'rated_user_id': 'rated_user_id must match the user of rated_profile_id.'
            })
        if rating_user_id and rated_user_id and rating_user_id == rated_user_id:
            raise serializers.ValidationError({
                'rating_user_id': 'Users cannot rate themselves.'
            })

        # Check for existing rating only during creation (not update)
        if self.instance is None:  # Creation mode
            if UserRating.objects.filter(
                rating_user_id=rating_user_id,
                rated_user_id=rated_user_id
            ).exists():
                raise serializers.ValidationError({
                    'non_field_errors': 'You have already rated this user. Please update the existing rating.'
                })

        return data

class UserRatingUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserRating
        fields = ['rating', 'feedback']

    def validate_rating(self, value):
        """
        Ensure rating is between 1 and 5.
        """
        if value is None:
            raise serializers.ValidationError("rating cannot be blank.")
        if not isinstance(value, int) or value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be an integer between 1 and 5.")
        return value