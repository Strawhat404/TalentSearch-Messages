"""
Django model for jobs, storing job-related information linked to a user.
"""

from django.db import models
from django.contrib.auth import get_user_model
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
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    project_title = models.CharField(max_length=255, blank=True)
    project_start_date = models.DateField(blank=True, null=True)
    project_end_date = models.DateField(blank=True, null=True)
    compensation_type = models.CharField(max_length=50, blank=True)
    compensation_amount = models.CharField(max_length=100, blank=True)
    project_details = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """
        String representation of the Job instance.
        Returns the job title and company name.
        """
        return f"{self.job_title} at {self.company_name}"