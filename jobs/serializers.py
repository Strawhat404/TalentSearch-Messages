"""
Serializer for the Job model, handling data validation and serialization.
Ensures required fields are provided and not blank.
"""

from rest_framework import serializers
from .models import Job


class JobSerializer(serializers.ModelSerializer):
    """
    Serializer for the Job model, mapping job fields and validating required fields.
    """
    user_id = serializers.PrimaryKeyRelatedField(read_only=True)
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
            'id', 'user_id', 'talents', 'project_type', 'organization_type',
            'first_name', 'last_name', 'company_name', 'company_website',
            'job_title', 'country', 'postal_code', 'project_title',
            'project_start_date', 'project_end_date', 'compensation_type',
            'compensation_amount', 'project_details', 'created_at'
        ]
        read_only_fields = ['id', 'user_id', 'created_at']

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