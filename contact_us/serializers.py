from rest_framework import serializers
from .models import ContactMessage
import re
from django.utils.html import strip_tags
import bleach

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
    value = re.sub(r'eval\s*\(.*?\)', '', value, flags=re.IGNORECASE)
    value = re.sub(r'expression\s*\(.*?\)', '', value, flags=re.IGNORECASE)
    # Remove remaining special characters
    value = re.sub(r'[<>%&*{}[\]|\\^`~]', '', value)
    return value.strip()

class ContactMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactMessage
        fields = ['id', 'name', 'email', 'subject', 'message', 'created_at']
        read_only_fields = ['id', 'created_at']

    def validate_email(self, value):
        if not value.strip():
            raise serializers.ValidationError("Email cannot be blank.")
        return sanitize_text(value)

    def validate_name(self, value):
        if not value.strip():
            raise serializers.ValidationError("Name cannot be blank.")
        return sanitize_text(value)

    def validate_subject(self, value):
        if not value.strip():
            raise serializers.ValidationError("Subject cannot be blank.")
        return sanitize_text(value)

    def validate_message(self, value):
        if not value.strip():
            raise serializers.ValidationError("Message cannot be blank.")
        return sanitize_text(value)

    def create(self, validated_data):
        """
        Create a contact message instance with the validated data.
        """
        contact_message = ContactMessage.objects.create(
            name=validated_data['name'],
            email=validated_data['email'],
            subject=validated_data['subject'],
            message=validated_data['message']
        )
        return contact_message

    def update(self, instance, validated_data):
        """
        Update a contact message instance with the validated data.
        """
        instance.name = validated_data.get('name', instance.name)
        instance.email = validated_data.get('email', instance.email)
        instance.subject = validated_data.get('subject', instance.subject)
        instance.message = validated_data.get('message', instance.message)
        instance.save()
        return instance

    def to_representation(self, instance):
        """
        Ensure the serialized output reflects the sanitized value.
        """
        ret = super().to_representation(instance)
        if 'name' in ret:
            ret['name'] = sanitize_text(ret['name'])
        if 'email' in ret:
            ret['email'] = sanitize_text(ret['email'])
        if 'subject' in ret:
            ret['subject'] = sanitize_text(ret['subject'])
        if 'message' in ret:
            ret['message'] = sanitize_text(ret['message'])
        return ret