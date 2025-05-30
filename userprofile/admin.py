from django.contrib import admin
from django import forms
from django.core.files.storage import default_storage
from django.contrib import messages
from .models import (
    Profile, IdentityVerification, ProfessionalQualifications, PhysicalAttributes,
    MedicalInfo, Education, WorkExperience, ContactInfo, PersonalInfo, Media
)
import os
from django.core.exceptions import ValidationError

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['user', 'name', 'birthdate', 'profession', 'nationality', 'location', 'availability_status', 'verified', 'flagged', 'status']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only make fields other than 'name', 'birthdate', 'profession', and 'nationality' optional
        for field in self.fields:
            if field not in ['name', 'birthdate', 'profession', 'nationality', 'user']:
                self.fields[field].required = False

class IdentityVerificationForm(forms.ModelForm):
    class Meta:
        model = IdentityVerification
        fields = ['id_type', 'id_number', 'id_expiry_date', 'id_front', 'id_back', 'id_verified']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].required = False

    def clean(self):
        cleaned_data = super().clean()
        for field in ['id_front', 'id_back']:
            clear_field = f"{field}-clear"
            if clear_field in self.data and self.data[clear_field] == 'on':
                cleaned_data[field] = None
            else:
                file = cleaned_data.get(field)
                if file:
                    valid_extensions = ['.jpg', '.jpeg', '.png', '.gif']
                    ext = os.path.splitext(file.name)[1].lower()
                    if ext not in valid_extensions:
                        raise ValidationError(f"{field} must be an image file (.jpg, .jpeg, .png, .gif).")
                    max_size = 5 * 1024 * 1024  # 5MB
                    if file.size > max_size:
                        raise ValidationError(f"{field} file size must not exceed 5MB.")
        return cleaned_data

class MediaForm(forms.ModelForm):
    class Meta:
        model = Media
        fields = ['video', 'photo']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].required = False

    def clean(self):
        cleaned_data = super().clean()
        for field in ['photo', 'video']:
            clear_field = f"{field}-clear"
            if clear_field in self.data and self.data[clear_field] == 'on':
                cleaned_data[field] = None
            else:
                file = cleaned_data.get(field)
                if file:
                    if field == 'photo':
                        valid_extensions = ['.jpg', '.jpeg', '.png', '.gif']
                        max_size = 5 * 1024 * 1024  # 5MB
                    else:  # video
                        valid_extensions = ['.mp4', '.avi', '.mov', '.mkv']
                        max_size = 50 * 1024 * 1024  # 50MB
                    ext = os.path.splitext(file.name)[1].lower()
                    if ext not in valid_extensions:
                        raise ValidationError(f"{field} must be a {'image' if field == 'photo' else 'video'} file ({', '.join(valid_extensions)}).")
                    if file.size > max_size:
                        raise ValidationError(f"{field} file size must not exceed {'5MB' if field == 'photo' else '50MB'}.")
        return cleaned_data

class ProfessionalQualificationsForm(forms.ModelForm):
    class Meta:
        model = ProfessionalQualifications
        fields = [
            'experience_level', 'skills', 'work_authorization', 'industry_experience',
            'min_salary', 'max_salary', 'availability', 'preferred_work_location', 'shift_preference',
            'willingness_to_relocate', 'overtime_availability', 'travel_willingness', 'software_proficiency',
            'typing_speed', 'driving_skills', 'equipment_experience', 'role_title', 'portfolio_url',
            'union_membership', 'reference', 'available_start_date', 'preferred_company_size',
            'preferred_industry', 'leadership_style', 'communication_style', 'motivation', 'has_driving_license'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].required = False

class PhysicalAttributesForm(forms.ModelForm):
    class Meta:
        model = PhysicalAttributes
        fields = [
            'weight', 'height', 'gender', 'hair_color', 'eye_color', 'body_type',
            'skin_tone', 'facial_hair', 'tattoos_visible', 'piercings_visible', 'physical_condition'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].required = False

class MedicalInfoForm(forms.ModelForm):
    class Meta:
        model = MedicalInfo
        fields = ['health_conditions', 'medications', 'disability_status', 'disability_type']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].required = False

class EducationForm(forms.ModelForm):
    class Meta:
        model = Education
        fields = [
            'education_level', 'degree_type', 'field_of_study', 'graduation_year',
            'gpa', 'institution_name', 'scholarships', 'academic_achievements',
            'certifications', 'online_courses'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].required = False

class WorkExperienceForm(forms.ModelForm):
    class Meta:
        model = WorkExperience
        fields = [
            'years_of_experience', 'employment_status', 'previous_employers',
            'projects', 'training', 'internship_experience'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].required = False

class ContactInfoForm(forms.ModelForm):
    class Meta:
        model = ContactInfo
        fields = [
            'address', 'specific_area', 'city', 'region', 'country',
            'housing_status', 'residence_duration', 'emergency_contact', 'emergency_phone'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].required = False

class PersonalInfoForm(forms.ModelForm):
    class Meta:
        model = PersonalInfo
        fields = [
            'marital_status', 'ethnicity', 'personality_type', 'work_preference',
            'hobbies', 'volunteer_experience', 'company_culture_preference', 'social_media_links',
            'social_media_handles', 'language_proficiency', 'special_skills', 'tools_experience',
            'award_recognitions'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].required = False

class IdentityVerificationInline(admin.StackedInline):
    model = IdentityVerification
    form = IdentityVerificationForm
    can_delete = True
    extra = 0
    fields = ['id_type', 'id_number', 'id_expiry_date', 'id_front', 'id_back', 'id_verified']
    readonly_fields = ['id_verified']

class ProfessionalQualificationsInline(admin.StackedInline):
    model = ProfessionalQualifications
    form = ProfessionalQualificationsForm
    can_delete = True
    extra = 0
    fields = [
        'experience_level', 'skills', 'work_authorization', 'industry_experience',
        'min_salary', 'max_salary', 'availability', 'preferred_work_location', 'shift_preference',
        'willingness_to_relocate', 'overtime_availability', 'travel_willingness', 'software_proficiency',
        'typing_speed', 'driving_skills', 'equipment_experience', 'role_title', 'portfolio_url',
        'union_membership', 'reference', 'available_start_date', 'preferred_company_size',
        'preferred_industry', 'leadership_style', 'communication_style', 'motivation', 'has_driving_license'
    ]

class PhysicalAttributesInline(admin.StackedInline):
    model = PhysicalAttributes
    form = PhysicalAttributesForm
    can_delete = True
    extra = 0
    fields = [
        'weight', 'height', 'gender', 'hair_color', 'eye_color', 'body_type',
        'skin_tone', 'facial_hair', 'tattoos_visible', 'piercings_visible', 'physical_condition'
    ]

class MedicalInfoInline(admin.StackedInline):
    model = MedicalInfo
    form = MedicalInfoForm
    can_delete = True
    extra = 0
    fields = ['health_conditions', 'medications', 'disability_status', 'disability_type']

class EducationInline(admin.StackedInline):
    model = Education
    form = EducationForm
    can_delete = True
    extra = 0
    fields = [
        'education_level', 'degree_type', 'field_of_study', 'graduation_year',
        'gpa', 'institution_name', 'scholarships', 'academic_achievements',
        'certifications', 'online_courses'
    ]

class WorkExperienceInline(admin.StackedInline):
    model = WorkExperience
    form = WorkExperienceForm
    can_delete = True
    extra = 0
    fields = [
        'years_of_experience', 'employment_status', 'previous_employers',
        'projects', 'training', 'internship_experience'
    ]

class ContactInfoInline(admin.StackedInline):
    model = ContactInfo
    form = ContactInfoForm
    can_delete = True
    extra = 0
    fields = [
        'address', 'specific_area', 'city', 'region', 'country',
        'housing_status', 'residence_duration', 'emergency_contact', 'emergency_phone'
    ]

class PersonalInfoInline(admin.StackedInline):
    model = PersonalInfo
    form = PersonalInfoForm
    can_delete = True
    extra = 0
    fields = [
        'marital_status', 'ethnicity', 'personality_type', 'work_preference',
        'hobbies', 'volunteer_experience', 'company_culture_preference', 'social_media_links',
        'social_media_handles', 'language_proficiency', 'special_skills', 'tools_experience',
        'award_recognitions'
    ]

class MediaInline(admin.StackedInline):
    model = Media
    form = MediaForm
    can_delete = True
    extra = 0
    fields = ['video', 'photo']

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    form = ProfileForm
    list_display = ['name', 'user', 'profession', 'nationality', 'location', 'created_at', 'availability_status', 'verified', 'flagged', 'status']
    list_filter = ['availability_status', 'verified', 'flagged', 'status']
    search_fields = ['name', 'user__username', 'user__email', 'profession', 'nationality', 'location']
    readonly_fields = ['created_at', 'age']
    inlines = [
        IdentityVerificationInline,
        ProfessionalQualificationsInline,
        PhysicalAttributesInline,
        MedicalInfoInline,
        EducationInline,
        WorkExperienceInline,
        ContactInfoInline,
        PersonalInfoInline,
        MediaInline
    ]
    fieldsets = (
        (None, {
            'fields': ('user', 'name', 'birthdate', 'age', 'profession', 'nationality', 'location')
        }),
        ('Status', {
            'fields': ('availability_status', 'verified', 'flagged', 'status')
        }),
        ('Metadata', {
            'fields': ('created_at',)
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        if obj:  # If editing an existing object
            return self.readonly_fields + ['user']
        return self.readonly_fields

    def save_formset(self, request, form, formset, change):
        if formset.model in [IdentityVerification, Media]:
            file_fields = ['id_front', 'id_back'] if formset.model == IdentityVerification else ['photo', 'video']
            for form in formset.forms:
                if not form.has_changed():
                    continue
                obj = form.instance
                try:
                    old_obj = formset.model.objects.get(pk=obj.pk) if obj.pk else None
                except formset.model.DoesNotExist:
                    old_obj = None

                old_file_paths = {}
                if old_obj:
                    for field in file_fields:
                        old_file_paths[field] = getattr(old_obj, field).path if getattr(old_obj, field) else None

                form.save()

                for field in file_fields:
                    new_file = getattr(obj, field)
                    old_file_path = old_file_paths.get(field)
                    if old_file_path and (not new_file or (new_file and new_file.path != old_file_path)):
                        if os.path.isfile(old_file_path):
                            try:
                                os.remove(old_file_path)
                                messages.info(request, f"Deleted old file: {old_file_path}")
                            except OSError as e:
                                messages.error(request, f"Error deleting old file {old_file_path}: {e}")

                    if new_file and (not old_file_path or new_file.path != old_file_path):
                        upload_to = obj.__class__._meta.get_field(field).upload_to
                        os.makedirs(os.path.join(default_storage.location, upload_to), exist_ok=True)

        super().save_formset(request, form, formset, change)

    def delete_model(self, request, obj):
        user = obj.user
        obj.delete()
        if user:
            user.delete()
        messages.info(request, f"Profile and associated user {user.username} deleted successfully.")