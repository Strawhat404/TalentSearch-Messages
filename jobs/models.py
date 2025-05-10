"""
Django model for jobs, storing job-related information linked to a user.
"""

from django.db import models
from django.conf import settings
from django.utils import timezone
from taggit.managers import TaggableManager


class Job(models.Model):
    """
    Represents a job posting or project associated with a user.
    """
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
        ('expired', 'Expired'),
    )

    COMPENSATION_TYPE_CHOICES = (
        ('hourly', 'Hourly'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
        ('project', 'Project-based'),
    )

    # Basic Information
    job_title = models.CharField(max_length=200, help_text="Title of the job position")
    company_name = models.CharField(max_length=200, help_text="Name of the company offering the job")
    company_website = models.URLField(blank=True, null=True, help_text="Company's website URL")
    location = models.CharField(max_length=200, blank=True, null=True, help_text="Job location")
    country = models.CharField(max_length=100, help_text="Country where the job is located")
    remote_work = models.BooleanField(default=False, help_text="Whether the job can be done remotely")
    
    # Contact Information
    first_name = models.CharField(max_length=100, help_text="Contact person's first name")
    last_name = models.CharField(max_length=100, help_text="Contact person's last name")
    email = models.EmailField(blank=True, null=True, help_text="Contact email address")
    phone = models.CharField(max_length=20, blank=True, null=True, help_text="Contact phone number")
    
    # Job Details
    description = models.TextField(blank=True, null=True, help_text="Detailed job description")
    requirements = models.TextField(blank=True, null=True, help_text="Job requirements and qualifications")
    responsibilities = models.TextField(blank=True, null=True, help_text="Job responsibilities")
    benefits = models.TextField(blank=True, null=True, help_text="Job benefits and perks")
    
    # Compensation
    compensation_type = models.CharField(
        max_length=20,
        choices=COMPENSATION_TYPE_CHOICES,
        default='monthly',
        help_text="Type of compensation"
    )
    compensation_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Compensation amount"
    )
    compensation_currency = models.CharField(
        max_length=3,
        default='USD',
        help_text="Currency for compensation"
    )
    
    # Additional Information
    employment_type = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Type of employment (e.g., Full-time, Part-time, Contract)"
    )
    experience_level = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Required experience level"
    )
    education_level = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Required education level"
    )
    skills_required = models.JSONField(
        default=list,
        help_text="List of required skills"
    )
    languages_required = models.JSONField(
        default=list,
        help_text="List of required languages"
    )
    
    # Project Information
    project_type = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Type of project (if applicable)"
    )
    project_duration = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Expected duration of the project"
    )
    start_date = models.DateField(
        null=True,
        blank=True,
        help_text="Expected start date"
    )
    
    # Organization Information
    organization_type = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Type of organization"
    )
    industry = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Industry sector"
    )
    company_size = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Size of the company"
    )
    
    # Metadata
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='jobs',
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        help_text="Current status of the job posting"
    )
    application_deadline = models.DateField(
        null=True,
        blank=True,
        help_text="Deadline for job applications"
    )
    
    # Additional Fields
    tags = TaggableManager(blank=True, help_text="Tags for job categorization")
    talents = models.JSONField(
        default=list,
        help_text="List of required talents or specializations"
    )
    is_featured = models.BooleanField(
        default=False,
        help_text="Whether this job is featured"
    )
    views_count = models.IntegerField(
        default=0,
        help_text="Number of times the job has been viewed"
    )
    applications_count = models.IntegerField(
        default=0,
        help_text="Number of applications received"
    )

    def __str__(self):
        """
        String representation of the Job instance.
        Returns the job title and company name.
        """
        return f"{self.job_title} at {self.company_name}"

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['company_name']),
            models.Index(fields=['job_title']),
            models.Index(fields=['location']),
        ]
        