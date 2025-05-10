"""
Serializer for the Job model, handling data validation and serialization.
Ensures required fields are provided and not blank.
"""

from rest_framework import serializers
from .models import Job
from django.utils import timezone


class JobSerializer(serializers.ModelSerializer):
    """
    Serializer for the Job model, mapping job fields and validating required fields.
    """
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    talents = serializers.CharField(required=True)
    project_type = serializers.CharField(required=True)
    organization_type = serializers.CharField(required=True)
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    job_title = serializers.CharField(required=True)
    country = serializers.CharField(required=True)

    class Meta:
        model = Job
        fields = [
            'id', 'user', 'job_title', 'company_name', 'company_website', 'location',
            'country', 'remote_work', 'first_name', 'last_name', 'email',
            'phone', 'description', 'requirements', 'responsibilities',
            'benefits', 'compensation_type', 'compensation_amount',
            'compensation_currency', 'employment_type', 'experience_level',
            'education_level', 'skills_required', 'languages_required',
            'project_type', 'project_duration', 'start_date',
            'organization_type', 'industry', 'company_size', 'status',
            'application_deadline', 'tags', 'talents', 'is_featured',
            'views_count', 'applications_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at', 'views_count', 'applications_count']

    def validate(self, data):
        """
        Validate required fields to ensure they are not blank.
        Checks all required fields for POST and provided fields for PUT.
        """
        required_fields = [
            'talents', 'project_type', 'organization_type', 'first_name',
            'last_name', 'company_name', 'job_title', 'country'
        ]
        errors = {}
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
        if errors:
            raise serializers.ValidationError(errors)
        return data

    def validate_compensation_amount(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Compensation amount cannot be negative")
        return value

    def validate_application_deadline(self, value):
        if value and value < timezone.now().date():
            raise serializers.ValidationError("Application deadline cannot be in the past")
        return value