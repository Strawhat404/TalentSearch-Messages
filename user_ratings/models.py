from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from userprofile.models import Profile  # Import Profile from userprofile app

User = get_user_model()

class UserRating(models.Model):
    id = models.AutoField(primary_key=True)
    # Removed rating_user_id and rated_user_id
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
                fields=['rater_profile_id', 'rated_profile_id'],  # Updated to use profile_id
                name='unique_user_rating'
            )
        ]

    def clean(self):
        """
        Validate that rater_profile_id and rated_profile_id are consistent with their users.
        """
        if self.rater_profile_id.user == self.rated_profile_id.user:
            raise ValidationError({
                'rater_profile_id': 'Profiles cannot rate themselves.'
            })

    def save(self, *args, **kwargs):
        """
        Ensure required fields are not blank and validate before saving.
        """
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