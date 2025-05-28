from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from userprofile.models import Profile  # Import Profile from userprofile app

User = get_user_model()

class UserRating(models.Model):
    id = models.AutoField(primary_key=True)
    rating_user_id = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='ratings_given'
    )
    rated_user_id = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='ratings_received'
    )
    rating = models.IntegerField(
        validators=[
            MinValueValidator(1, message="Rating must be at least 1."),
            MaxValueValidator(5, message="Rating must be at most 5.")
        ]
    )
    feedback = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    rater_profile_id = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name='ratings_given'
    )
    rated_profile_id = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name='ratings_received'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['rating_user_id', 'rated_user_id'],
                name='unique_user_rating'
            )
        ]

    def clean(self):
        """
        Validate that rating_user_id matches rater_profile_id's user and
        rated_user_id matches rated_profile_id's user.
        """
        if self.rating_user_id != self.rater_profile_id.user:
            raise ValidationError({
                'rating_user_id': 'rating_user_id must match the user of rater_profile_id.'
            })
        if self.rated_user_id != self.rated_profile_id.user:
            raise ValidationError({
                'rated_user_id': 'rated_user_id must match the user of rated_profile_id.'
            })
        if self.rating_user_id == self.rated_user_id:
            raise ValidationError({
                'rating_user_id': 'Users cannot rate themselves.'
            })

    def save(self, *args, **kwargs):
        """
        Ensure required fields are not blank and validate before saving.
        """
        if not self.rating_user_id:
            raise ValueError("rating_user_id cannot be blank.")
        if not self.rated_user_id:
            raise ValueError("rated_user_id cannot be blank.")
        if not self.rater_profile_id:
            raise ValueError("rater_profile_id cannot be blank.")
        if not self.rated_profile_id:
            raise ValueError("rated_profile_id cannot be blank.")
        if self.rating is None:
            raise ValueError("rating cannot be blank.")
        self.full_clean()  # Run model validation
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Rating {self.rating} by {self.rater_profile_id.name} for {self.rated_profile_id.name}"