from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django import forms
from .models import Profile
import os
from django.core.exceptions import ValidationError
from pathlib import Path
from django.contrib.admin.sites import NotRegistered
from django.contrib.auth import get_user_model
User = get_user_model()
# Custom form with file size and extension validation
class ProfileAdminForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make all fields optional except name and profession
        for field_name, field in self.fields.items():
            if field_name not in ['name', 'profession']:
                field.required = False
                if isinstance(field, forms.JSONField):
                    field.empty_value = field.widget.attrs.get('empty_value', {})
                    field.widget.attrs['empty_value'] = field.empty_value
                if isinstance(field, (forms.CharField, forms.URLField)):
                    field.empty_value = ''
                    field.widget.attrs['empty_value'] = ''
                if isinstance(field, (forms.DateField, forms.IntegerField, forms.FloatField)):
                    field.empty_value = None
                    field.widget.attrs['empty_value'] = None

    def clean(self):
        cleaned_data = super().clean()
        json_fields = [
            'skills', 'languages', 'social_media_links', 'health_conditions', 'medications',
            'social_media_handles', 'previous_employers', 'projects', 'training', 'certifications',
            'online_courses', 'software_proficiency', 'equipment_experience', 'hobbies',
            'preferred_industry', 'scholarships', 'academic_achievements', 'language_proficiency',
            'special_skills', 'tools_experience', 'award_recognitions', 'reference'
        ]
        for field_name in json_fields:
            if field_name in cleaned_data and cleaned_data[field_name] in (None, '', '{}', '[]'):
                cleaned_data[field_name] = {} if self.fields[field_name].widget.attrs.get('empty_value') == {} else []
        return cleaned_data

    # File size and extension validation
    def validate_file(self, file, allowed_extensions, max_size_mb):
        if not file:
            return
        # Validate file size
        max_size_bytes = max_size_mb * 1024 * 1024  # Convert MB to bytes
        if file.size > max_size_bytes:
            raise ValidationError(f"File size exceeds the maximum limit of {max_size_mb} MB.")
        if file.size == 0:
            raise ValidationError("The submitted file is empty.")
        # Validate file extension
        extension = Path(file.name).suffix.lower()
        if extension not in allowed_extensions:
            raise ValidationError(f"Unsupported file extension. Allowed extensions are: {', '.join(allowed_extensions)}.")

    def clean_photo(self):
        photo = self.cleaned_data.get('photo')
        self.validate_file(photo, allowed_extensions=['.jpg', '.jpeg', '.png'], max_size_mb=5)  # 5 MB limit for images
        return photo

    def clean_video(self):
        video = self.cleaned_data.get('video')
        self.validate_file(video, allowed_extensions=['.mp4', '.mov'], max_size_mb=50)  # 50 MB limit for videos
        return video

    def clean_id_front(self):
        id_front = self.cleaned_data.get('id_front')
        self.validate_file(id_front, allowed_extensions=['.jpg', '.jpeg', '.png'], max_size_mb=5)  # 5 MB limit for images
        return id_front

    def clean_id_back(self):
        id_back = self.cleaned_data.get('id_back')
        self.validate_file(id_back, allowed_extensions=['.jpg', '.jpeg', '.png'], max_size_mb=5)  # 5 MB limit for images
        return id_back

# Inline for Profile to allow editing within the User admin page
class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'
    form = ProfileAdminForm
    fields = (
        ('name', 'profession'),
        ('user',),
        ('birthdate', 'weight', 'height'),
        ('location', 'gender', 'hair_color', 'eye_color', 'body_type'),
        'has_driving_license',
        ('photo', 'video', 'id_front', 'id_back'),
        ('skills', 'languages', 'social_media_links'),
        ('nationality', 'education_level', 'experience_level'),
        ('min_salary', 'max_salary', 'work_authorization'),
        ('industry_experience', 'years_of_experience', 'employment_status'),
        ('previous_employers', 'projects', 'training', 'internship_experience'),
        ('degree_type', 'field_of_study', 'certifications', 'online_courses'),
        ('preferred_work_location', 'shift_preference', 'willingness_to_relocate'),
        ('overtime_availability', 'travel_willingness', 'software_proficiency'),
        ('typing_speed', 'driving_skills', 'equipment_experience'),
        ('personality_type', 'work_preference', 'hobbies', 'volunteer_experience'),
        ('company_culture_preference', 'id_type', 'id_number', 'id_expiry_date'),
        ('id_verified', 'residence_type', 'address', 'city', 'region', 'postal_code'),
        ('residence_duration', 'housing_status', 'emergency_contact', 'emergency_phone'),
        ('skin_tone', 'facial_hair', 'tattoos_visible', 'piercings_visible'),
        ('physical_condition', 'role_title', 'portfolio_url', 'social_media_handles'),
        ('union_membership', 'reference', 'available_start_date', 'graduation_year'),
        ('gpa', 'institution_name', 'scholarships', 'academic_achievements'),
        ('language_proficiency', 'special_skills', 'tools_experience', 'award_recognitions'),
        ('preferred_company_size', 'preferred_industry', 'leadership_style'),
        ('communication_style', 'motivation', 'verified', 'flagged', 'status'),
    )

# Custom UserAdmin to include Profile inline and enforce email
class CustomUserAdmin(UserAdmin):
    inlines = (ProfileInline,)
    list_display = ('email', 'first_name', 'last_name', 'is_staff', 'get_profile_name')
    list_select_related = ('profile',)
    ordering = ('email',)

    # Add these fieldsets to match your custom user model (no username)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password1', 'password2', 'is_staff', 'is_active'),
        }),
    )

    def get_profile_name(self, obj):
        return obj.profile.name if hasattr(obj, 'profile') else '-'

    get_profile_name.short_description = 'Profile Name'

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['email'].required = True
        return form

    def save_formset(self, request, form, formset, change):
        # Handle file deletion for ProfileInline
        if formset.model == Profile:
            file_fields = ['photo', 'video', 'id_front', 'id_back']
            for form in formset.forms:
                if not form.has_changed():
                    continue
                obj = form.instance
                try:
                    old_obj = Profile.objects.get(pk=obj.pk) if obj.pk else None
                except Profile.DoesNotExist:
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
                                self.message_user(request, f"Deleted old file: {old_file_path}")
                            except OSError as e:
                                self.message_user(request, f"Error deleting old file {old_file_path}: {e}")
        # Always call super to keep Django admin happy!
        super().save_formset(request, form, formset, change)

# Register Profile model
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    form = ProfileAdminForm
    list_display = ('name', 'user', 'profession', 'email', 'created_at', 'verified', 'flagged')
    list_filter = ('profession', 'has_driving_license', 'verified', 'flagged', 'availability_status')
    search_fields = ('name', 'user__email', 'profession', 'location')
    list_select_related = ('user',)

    fieldsets = (
        ('Required Information', {
            'fields': ('name', 'profession')
        }),
        ('User Information', {
            'fields': ('user',)
        }),
        ('Personal Information', {
            'fields': ('birthdate', 'weight', 'height', 'gender', 'hair_color', 'eye_color', 'body_type', 'skin_tone',
                       'facial_hair', 'tattoos_visible', 'piercings_visible', 'physical_condition')
        }),
        ('Contact Information', {
            'fields': ('location', 'address', 'city', 'region', 'postal_code', 'emergency_contact', 'emergency_phone')
        }),
        ('Professional Information', {
            'fields': ('experience_level', 'years_of_experience', 'employment_status', 'previous_employers', 'projects',
                       'training', 'internship_experience', 'role_title')
        }),
        ('Education', {
            'fields': ('education_level', 'degree_type', 'field_of_study', 'graduation_year', 'gpa', 'institution_name',
                       'scholarships', 'academic_achievements', 'certifications', 'online_courses')
        }),
        ('Skills and Preferences', {
            'fields': (
            'skills', 'languages', 'language_proficiency', 'special_skills', 'software_proficiency', 'tools_experience',
            'typing_speed', 'driving_skills', 'equipment_experience', 'work_preference', 'preferred_work_location',
            'shift_preference', 'willingness_to_relocate', 'overtime_availability', 'travel_willingness',
            'preferred_company_size', 'preferred_industry')
        }),
        ('Media and Documents', {
            'fields': ('photo', 'video', 'id_front', 'id_back', 'id_type', 'id_number', 'id_expiry_date', 'id_verified',
                       'portfolio_url', 'social_media_links', 'social_media_handles')
        }),
        ('Additional Information', {
            'fields': (
            'has_driving_license', 'nationality', 'work_authorization', 'industry_experience', 'marital_status',
            'ethnicity', 'disability_status', 'disability_type', 'health_conditions', 'medications', 'residence_type',
            'residence_duration', 'housing_status', 'landmark', 'availability', 'availability_status', 'min_salary',
            'max_salary', 'union_membership', 'reference', 'available_start_date', 'hobbies', 'volunteer_experience',
            'company_culture_preference', 'personality_type', 'leadership_style', 'communication_style', 'motivation',
            'award_recognitions')
        }),
        ('Admin Status', {
            'fields': ('created_at', 'verified', 'flagged', 'status')
        }),
    )

    readonly_fields = ('created_at',)

    def email(self, obj):
        return obj.user.email

    email.short_description = 'Email'

    def save_model(self, request, obj, form, change):
        # If this is an update (not a new object), check for file changes
        if change:
            try:
                # Fetch the original object from the database
                old_obj = Profile.objects.get(pk=obj.pk)
                file_fields = ['photo', 'video', 'id_front', 'id_back']
                old_file_paths = {}
                for field in file_fields:
                    old_file_paths[field] = getattr(old_obj, field).path if getattr(old_obj, field) else None

                # Save the new object (this uploads the new file)
                super().save_model(request, obj, form, change)

                # Check each file field and delete the old file if replaced
                for field in file_fields:
                    new_file = getattr(obj, field)
                    old_file_path = old_file_paths[field]
                    # If there's a new file and it's different from the old file, delete the old file
                    # Also delete if the field is cleared (new_file is None)
                    if old_file_path and (not new_file or (new_file and new_file.path != old_file_path)):
                        if os.path.isfile(old_file_path):
                            try:
                                os.remove(old_file_path)
                                self.message_user(request, f"Deleted old file: {old_file_path}")
                            except OSError as e:
                                self.message_user(request, f"Error deleting old file {old_file_path}: {e}")
            except Profile.DoesNotExist:
                # Shouldn't happen, but handle just in case
                super().save_model(request, obj, form, change)
        else:
            # For new objects, just save normally
            super().save_model(request, obj, form, change)

# Unregister the default User admin and register the custom one
try:
    admin.site.unregister(User)
except NotRegistered:
    pass
admin.site.register(User, CustomUserAdmin)