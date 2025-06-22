"""
Django model for jobs, storing job-related information linked to a user.
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from datetime import date

User = get_user_model()

class Job(models.Model):
    """
    Represents a job posting or project associated with a user.
    """
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    talents = models.CharField(max_length=255, blank=False)
    project_type = models.CharField(max_length=100, blank=False)
    organization_type = models.CharField(max_length=100, blank=False)
    first_name = models.CharField(max_length=100, blank=False)
    last_name = models.CharField(max_length=100, blank=False)
    company_name = models.CharField(max_length=255, blank=False)
    company_website = models.URLField(blank=True, null=True)
    job_title = models.CharField(max_length=255, blank=False)
    country = models.CharField(max_length=100, blank=False)
    postal_code = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        validators=[
            RegexValidator(
                regex=r'^\d{4}$',
                message="Postal code must be a 4-digit number (e.g., 1000 for Addis Ababa)."
            )
        ]
    )
    project_title = models.CharField(max_length=255, blank=True)
    project_start_date = models.DateField(blank=True, null=True)
    project_end_date = models.DateField(blank=True, null=True)
    compensation_type = models.TextField(blank=True)  # As updated previously
    compensation_amount = models.CharField(max_length=100, blank=True)
    project_details = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        """
        Model-level validation for date range and future dates.
        """
        if self.project_start_date and self.project_end_date:
            if self.project_end_date < self.project_start_date:
                raise ValidationError({
                    'project_end_date': "Project end date cannot be before project start date."
                })
        current_date = date.today()
        if self.project_start_date and self.project_start_date < current_date:
            raise ValidationError({
                'project_start_date': "Project start date must be today or in the future."
            })
        if self.project_end_date and self.project_end_date < current_date:
            raise ValidationError({
                'project_end_date': "Project end date must be today or in the future."
            })

    def __str__(self):
        """
        String representation of the Job instance.
        Returns the job title and company name.
        """
        return f"{self.job_title} at {self.company_name}"

class Application(models.Model):
    """
    Represents a job application submitted by a user.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    opportunity_description = models.TextField()
    applied_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        """
        String representation of the Application instance.
        Returns the user and job title.
        """
        return f"{self.user.email} applied for {self.job.job_title}"