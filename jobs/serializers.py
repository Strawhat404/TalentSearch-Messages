from rest_framework import serializers
from .models import Job, Application
import re
from urllib.parse import urlparse
from datetime import date
from django.utils.html import strip_tags
import bleach
from userprofile.models import Profile

def sanitize_text(value):
    """
    Sanitize text using bleach to remove HTML tags, JS, and XSS, with additional character cleaning.
    """
    if not value or not isinstance(value, str):
        return ""
    # Use bleach to aggressively sanitize, removing all tags, attributes, and scripts
    value = bleach.clean(value, tags=[], attributes={}, strip=True, protocols=['http', 'https'])
    # Additional regex to catch any remaining XSS patterns
    value = re.sub(r'alert\s*\(.*?\)', '', value, flags=re.IGNORECASE)
    value = re.sub(r'<script.*?>.*?</script>', '', value, flags=re.IGNORECASE | re.DOTALL)
    value = re.sub(r'on\w+\s*=\s*["\'].*?["\']', '', value, flags=re.IGNORECASE)
    value = re.sub(r'javascript\s*:', '', value, flags=re.IGNORECASE)
    value = re.sub(r'eval\s*\(.*?\)', '', value, flags=re.IGNORECASE)  # Added eval() removal
    value = re.sub(r'expression\s*\(.*?\)', '', value, flags=re.IGNORECASE)  # Added CSS expression removal
    # Remove remaining special characters
    value = re.sub(r'[<>%&*{}[\]|\\^`~]', '', value)
    return value.strip()

class JobSerializer(serializers.ModelSerializer):
    profile_id = serializers.PrimaryKeyRelatedField(read_only=True)
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
            'id', 'profile_id', 'talents', 'project_type', 'organization_type',
            'first_name', 'last_name', 'company_name', 'company_website',
            'job_title', 'country', 'postal_code', 'project_title',
            'project_start_date', 'project_end_date', 'compensation_type',
            'compensation_amount', 'project_details', 'created_at', 'applicant_count'
        ]
        read_only_fields = ['id', 'profile_id', 'created_at']

    def validate_talents(self, value):
        return sanitize_text(value)

    def validate_project_type(self, value):
        return sanitize_text(value)

    def validate_organization_type(self, value):
        return sanitize_text(value)

    def validate_first_name(self, value):
        return sanitize_text(value)

    def validate_last_name(self, value):
        return sanitize_text(value)

    def validate_job_title(self, value):
        return sanitize_text(value)

    def validate_country(self, value):
        return sanitize_text(value)

    def validate_company_name(self, value):
        return sanitize_text(value) if value else value

    def validate_project_title(self, value):
        return sanitize_text(value) if value else value

    def validate_project_details(self, value):
        return sanitize_text(value) if value else value

    def validate_compensation_type(self, value):
        return sanitize_text(value) if value else value

    def validate_compensation_amount(self, value):
        return sanitize_text(value) if value else value

    def validate(self, data):
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

        if 'project_start_date' in data and 'project_end_date' in data:
            start_date = data.get('project_start_date')
            end_date = data.get('project_end_date')
            if start_date and end_date and end_date < start_date:
                errors['project_end_date'] = "Project end date cannot be before project start date."

        if 'postal_code' in data and data.get('postal_code'):
            postal_code = data.get('postal_code')
            sanitized_postal = re.sub(r'[^0-9]', '', postal_code.strip())
            data['postal_code'] = sanitized_postal
            if not re.match(r'^\d{4}$', sanitized_postal):
                errors['postal_code'] = "Postal code must be a 4-digit number (e.g., 1000 for Addis Ababa)."

        if 'company_website' in data and data.get('company_website'):
            website = data.get('company_website')
            try:
                parsed = urlparse(website)
                if not all([parsed.scheme in ['http', 'https'], parsed.netloc]):
                    errors['company_website'] = "Company website must be a valid URL with http or https scheme."
            except ValueError:
                errors['company_website'] = "Invalid URL format for company website."

        if 'compensation_type' in data and 'compensation_amount' in data:
            comp_type = data.get('compensation_type')
            comp_amount = data.get('compensation_amount')
            if comp_type and not comp_amount:
                errors['compensation_amount'] = "Compensation amount is required when compensation type is provided."
            elif comp_amount and not comp_type:
                errors['compensation_type'] = "Compensation type is required when compensation amount is provided."

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
        return Application.objects.filter(job_id=obj.id).count()

class ApplicationSerializer(serializers.ModelSerializer):
    profile_id = serializers.PrimaryKeyRelatedField(read_only=True)
    job = serializers.PrimaryKeyRelatedField(read_only=True)
    opportunity_description = serializers.CharField(required=True)
    applicant_name = serializers.SerializerMethodField()
    applicant_email = serializers.SerializerMethodField()

    class Meta:
        model = Application
        fields = ['profile_id', 'job', 'opportunity_description', 'applied_at', 'applicant_name', 'applicant_email']
        read_only_fields = ['profile_id', 'job', 'applied_at', 'applicant_name', 'applicant_email']

    def validate_opportunity_description(self, value):
        """
        Validate and sanitize the opportunity description.
        Ensures 50-1000 characters, removes special characters, and strips HTML tags and JS.
        """
        original_value = value
        sanitized_value = sanitize_text(value)
        cleaned_value = re.sub(r'[<>%&*{}[\]|\\^`~]', '', sanitized_value)
        length = len(cleaned_value)

        if length < 50:
            raise serializers.ValidationError("Opportunity description must be at least 50 characters long.")
        if length > 1000:
            raise serializers.ValidationError("Opportunity description must not exceed 1000 characters.")

        return cleaned_value

    def create(self, validated_data):
        """
        Create an application instance with the validated opportunity_description.
        """
        application = Application.objects.create(
            profile_id=validated_data['profile_id'],
            job=validated_data['job'],
            opportunity_description=validated_data['opportunity_description']
        )
        return application

    def update(self, instance, validated_data):
        """
        Update an application instance with the validated opportunity_description.
        """
        instance.opportunity_description = validated_data.get('opportunity_description', instance.opportunity_description)
        instance.save()
        return instance

    def get_applicant_name(self, obj):
        return obj.profile_id.name

    def get_applicant_email(self, obj):
        return obj.profile_id.user.email

    def to_representation(self, instance):
        """
        Ensure the serialized output reflects the sanitized value.
        """
        ret = super().to_representation(instance)
        if 'opportunity_description' in ret:
            ret['opportunity_description'] = sanitize_text(ret['opportunity_description'])
        return ret

def sanitize_text(value):
    """
    Sanitize text using bleach to remove HTML tags, JS, and XSS, with additional character cleaning.
    """
    if not value or not isinstance(value, str):
        return ""
    # Use bleach to aggressively sanitize, removing all tags, attributes, and scripts
    value = bleach.clean(value, tags=[], attributes={}, strip=True, protocols=['http', 'https'])
    # Additional regex to catch any remaining XSS patterns
    value = re.sub(r'alert\s*\(.*?\)', '', value, flags=re.IGNORECASE)
    value = re.sub(r'<script.*?>.*?</script>', '', value, flags=re.IGNORECASE | re.DOTALL)
    value = re.sub(r'on\w+\s*=\s*["\'].*?["\']', '', value, flags=re.IGNORECASE)
    value = re.sub(r'javascript\s*:', '', value, flags=re.IGNORECASE)
    value = re.sub(r'eval\s*\(.*?\)', '', value, flags=re.IGNORECASE)  # Added eval() removal
    value = re.sub(r'expression\s*\(.*?\)', '', value, flags=re.IGNORECASE)  # Added CSS expression removal
    # Remove remaining special characters
    value = re.sub(r'[<>%&*{}[\]|\\^`~]', '', value)
    return value.strip()