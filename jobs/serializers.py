"""
Serializer for the Job model, handling data validation and serialization.
Ensures required fields are provided and not blank.
"""

from rest_framework import serializers
from .models import Job, Application
import re
from urllib.parse import urlparse
from datetime import date
from django.utils.html import strip_tags
from userprofile.models import Profile

class JobSerializer(serializers.ModelSerializer):
    """
    Serializer for the Job model, mapping job fields and validating required fields.
    Includes applicant_count as a calculated field.
    """
    user_id = serializers.PrimaryKeyRelatedField(read_only=True)
    talents = serializers.CharField(required=True)
    project_type = serializers.CharField(required=True)
    organization_type = serializers.CharField(required=True)
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    job_title = serializers.CharField(required=True)
    country = serializers.CharField(required=True)
    applicant_count = serializers.SerializerMethodField()

    class Meta:
        model = Job
        fields = [
            'id', 'user_id', 'talents', 'project_type', 'organization_type',
            'first_name', 'last_name', 'company_name', 'company_website',
            'job_title', 'country', 'postal_code', 'project_title',
            'project_start_date', 'project_end_date', 'compensation_type',
            'compensation_amount', 'project_details', 'created_at', 'applicant_count'
        ]
        read_only_fields = ['id', 'user_id', 'created_at']

    def validate(self, data):
        """
        Validate required fields to ensure they are not blank.
        Checks all required fields for POST and provided fields for PUT.
        Adds validations for date range, Ethiopia-specific postal code, company website,
        Ethiopia-specific compensation, and future dates.
        """
        required_fields = [
            'talents', 'project_type', 'organization_type', 'first_name',
            'last_name', 'company_name', 'job_title', 'country'
        ]
        errors = {}

        # Existing validation for required fields
        if not self.partial:
            for field in required_fields:
                if field not in data:
                    errors[field] = f"{field.replace('_', ' ').title()} cannot be blank."
                elif data.get(field) is None or str(data.get(field)).strip() == "":
                    errors[field] = f"{field.replace('_', ' ').title()} cannot be blank."
        else:
            for field, value in data.items():
                if field in required_fields and (value is None or str(value).strip() == ""):
                    errors[field] = f"{field.replace('_', ' ').title()} cannot be blank."

        # Date range validation: Ensure project_end_date is not before project_start_date
        if 'project_start_date' in data and 'project_end_date' in data:
            start_date = data.get('project_start_date')
            end_date = data.get('project_end_date')
            if start_date and end_date and end_date < start_date:
                errors['project_end_date'] = "Project end date cannot be before project start date."

        # Ethiopia-specific postal code validation: Must be a 4-digit number
        if 'postal_code' in data and data.get('postal_code'):
            postal_code = data.get('postal_code')
            if not re.match(r'^\d{4}$', postal_code):
                errors['postal_code'] = "Postal code must be a 4-digit number (e.g., 1000 for Addis Ababa)."

        # Company website validation: Ensure it has a valid scheme and domain
        if 'company_website' in data and data.get('company_website'):
            website = data.get('company_website')
            try:
                parsed = urlparse(website)
                if not all([parsed.scheme in ['http', 'https'], parsed.netloc]):
                    errors['company_website'] = "Company website must be a valid URL with http or https scheme."
            except ValueError:
                errors['company_website'] = "Invalid URL format for company website."

        # Ethiopia-specific compensation validation: Ensure compensation_amount is valid for ETB
        if 'compensation_type' in data and 'compensation_amount' in data:
            comp_type = data.get('compensation_type')
            comp_amount = data.get('compensation_amount')
            if comp_type and comp_amount:
                # Allow "ETB" prefix/suffix or plain number (e.g., "ETB 50000", "50000 ETB", "50000")
                cleaned_amount = comp_amount.strip().replace('ETB', '').replace(',', '').strip()
                try:
                    amount = float(cleaned_amount)
                    if amount <= 0:
                        errors['compensation_amount'] = "Compensation amount must be a positive number in ETB."
                except (ValueError, TypeError):
                    errors['compensation_amount'] = "Compensation amount must be a valid number (e.g., 50000 or ETB 50000)."
            elif comp_type and not comp_amount:
                errors['compensation_amount'] = "Compensation amount is required when compensation type is provided."
            elif comp_amount and not comp_type:
                errors['compensation_type'] = "Compensation type is required when compensation amount is provided."

        # Future date validation: Ensure project dates are in the future
        current_date = date.today()
        if 'project_start_date' in data and data.get('project_start_date'):
            if data.get('project_start_date') < current_date:
                errors['project_start_date'] = "Project start date must be today or in the future."
        if 'project_end_date' in data and data.get('project_end_date'):
            if data.get('project_end_date') < current_date:
                errors['project_end_date'] = "Project end date must be today or in the future."

        if errors:
            raise serializers.ValidationError(errors)
        return data

    def get_applicant_count(self, obj):
        """
        Calculate the number of applicants for the job.
        """
        return Application.objects.filter(job_id=obj.id).count()

class ApplicationSerializer(serializers.ModelSerializer):
    """
    Serializer for the Application model, handling job application data.
    Includes the applicant's name and email from User with a fallback to User.name.
    """
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    job = serializers.PrimaryKeyRelatedField(read_only=True)
    opportunity_description = serializers.CharField(required=True)
    applicant_name = serializers.SerializerMethodField()
    applicant_email = serializers.SerializerMethodField()

    class Meta:
        model = Application
        fields = ['user', 'job', 'opportunity_description', 'applied_at', 'applicant_name', 'applicant_email']  # Added 'applicant_email'
        read_only_fields = ['user', 'job', 'applied_at', 'applicant_name', 'applicant_email']  # Added 'applicant_email'

    def validate_opportunity_description(self, value):
        """
        Validate and sanitize the opportunity description.
        Ensures 50-1000 characters, removes special characters, and strips HTML tags.
        """
        # Strip HTML tags
        sanitized_value = strip_tags(value)
        # Remove special characters (e.g., <, >, &, etc.) beyond basic text
        cleaned_value = re.sub(r'[<>%&]', '', sanitized_value)
        length = len(cleaned_value)

        if length < 50:
            raise serializers.ValidationError("Opportunity description must be at least 50 characters long.")
        if length > 1000:
            raise serializers.ValidationError("Opportunity description must not exceed 1000 characters.")

        return cleaned_value

    def get_applicant_name(self, obj):
        """
        Get the applicant's name from Profile, falling back to User.name if Profile is missing.
        """
        profile = getattr(obj.user.profile, 'all', [None])[0] if hasattr(obj.user, 'profile') else None
        return profile.name if profile else obj.user.name

    def get_applicant_email(self, obj):
        """
        Get the applicant's email from User.
        """
        return obj.user.email
