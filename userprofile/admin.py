from django.contrib import admin
from django import forms
from django.core.files.storage import default_storage
from django.contrib import messages
from .models import (
    Profile, BasicInformation, LocationInformation, ProfessionsAndSkills, IdentityVerification, PhysicalAttributes,
    MedicalInfo, Education, WorkExperience, ContactInfo, PersonalInfo, Media, SocialMedia, Headshot, NaturalPhotos, Experience
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

class BasicInformationForm(forms.ModelForm):
    class Meta:
        model = BasicInformation
        fields = [
            # Dropdown Values
            'nationality', 'gender', 'languages', 'hair_color', 'eye_color', 
            'skin_tone', 'body_type', 'medical_conditions', 'medicine_types', 
            'marital_status', 'hobbies',
            # Input Fields  
            'date_of_birth', 'height', 'weight', 'emergency_contact_name', 
            'emergency_contact_phone', 'custom_hobby',
            # Toggle Fields
            'has_driving_license', 'has_visible_piercings', 'has_visible_tattoos', 
            'willing_to_travel'
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'languages': forms.Textarea(attrs={'rows': 3}),
            'medical_conditions': forms.Textarea(attrs={'rows': 3}),
            'medicine_types': forms.Textarea(attrs={'rows': 3}),
            'hobbies': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # All fields are required except custom_hobby
        for field in self.fields:
            if field != 'custom_hobby':
                self.fields[field].required = True

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

class ExperienceForm(forms.ModelForm):
    class Meta:
        model = Experience
        fields = [
            'experience_level', 'skills', 'availability', 'preferred_work_location', 'shift_preference',
            'willingness_to_relocate', 'overtime_availability', 'travel_willingness',
            'equipment_experience', 'role_title', 'portfolio_url',
            'union_membership', 'reference', 'available_start_date', 'preferred_company_size',
            'preferred_industry', 'leadership_style', 'communication_style', 'motivation', 'has_driving_license',
            'work_authorization'
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
            'education_level', 'degree_type', 'field_of_study',
            'institution_name', 'scholarships', 'academic_achievements',
            'certifications', 'online_courses'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].required = False

class WorkExperienceForm(forms.ModelForm):
    class Meta:
        model = WorkExperience
        fields = ['years_of_experience', 'employment_status']

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
            self.fields[field].required = True

class PersonalInfoForm(forms.ModelForm):
    class Meta:
        model = PersonalInfo
        fields = [
            'first_name',
            'last_name',
            'date_of_birth',
            'gender',
            'marital_status',
            'nationality',
            'id_type',
            'id_number',
            'hobbies',
            'language_proficiency',
            'social_media',
            'custom_hobby',
            'custom_language',
            'custom_social_media'
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'hobbies': forms.CheckboxSelectMultiple(),
            'language_proficiency': forms.CheckboxSelectMultiple(),
            'social_media': forms.JSONField(),
        }

    def clean(self):
        cleaned_data = super().clean()
        # Add any custom validation here if needed
        return cleaned_data

class IdentityVerificationInline(admin.StackedInline):
    model = IdentityVerification
    form = IdentityVerificationForm
    can_delete = True
    extra = 0
    fields = ['id_type', 'id_number', 'id_expiry_date', 'id_front', 'id_back', 'id_verified']
    readonly_fields = ['id_verified']

class ExperienceInline(admin.StackedInline):
    model = Experience
    form = ExperienceForm
    can_delete = True
    extra = 0
    fields = [
        'experience_level', 'skills', 'availability', 'preferred_work_location', 'shift_preference',
        'willingness_to_relocate', 'overtime_availability', 'travel_willingness',
        'equipment_experience', 'role_title', 'portfolio_url',
        'union_membership', 'reference', 'available_start_date', 'preferred_company_size',
        'preferred_industry', 'leadership_style', 'communication_style', 'motivation', 'has_driving_license',
        'work_authorization'
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
        'education_level', 'degree_type', 'field_of_study',
        'institution_name', 'scholarships', 'academic_achievements',
        'certifications', 'online_courses'
    ]

class WorkExperienceInline(admin.StackedInline):
    model = WorkExperience
    form = WorkExperienceForm
    can_delete = True
    extra = 0
    fields = ['years_of_experience', 'employment_status']

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
        'first_name',
        'last_name',
        'date_of_birth',
        'gender',
        'marital_status',
        'nationality',
        'id_type',
        'id_number',
        'hobbies',
        'language_proficiency',
        'social_media',
        'custom_hobby',
        'custom_language',
        'custom_social_media'
    ]

class MediaInline(admin.StackedInline):
    model = Media
    form = MediaForm
    can_delete = True
    extra = 0
    fields = ['video', 'photo']

class BasicInformationInline(admin.StackedInline):
    model = BasicInformation
    form = BasicInformationForm
    can_delete = True
    extra = 0
    fields = [
        ('nationality', 'gender'),
        ('date_of_birth', 'marital_status'),
        ('height', 'weight'),
        ('hair_color', 'eye_color'),
        ('skin_tone', 'body_type'),
        ('emergency_contact_name', 'emergency_contact_phone'),
        'languages',
        'medical_conditions',
        'medicine_types',
        'hobbies',
        'custom_hobby',
        ('has_driving_license', 'has_visible_piercings'),
        ('has_visible_tattoos', 'willing_to_travel'),
    ]

class LocationInformationForm(forms.ModelForm):
    class Meta:
        model = LocationInformation
        fields = [
            # Dropdown Values
            'housing_status', 'region', 'duration', 'city', 'country',
            # Input Fields  
            'address', 'specific_area'
        ]
        widgets = {
            'housing_status': forms.Select(),
            'duration': forms.Select(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # All fields are required
        for field in self.fields:
            self.fields[field].required = True

class LocationInformationInline(admin.StackedInline):
    model = LocationInformation
    form = LocationInformationForm
    can_delete = True
    extra = 0
    fields = [
        ('housing_status', 'duration'),
        ('region', 'city'),
        'country',
        'address',
        'specific_area',
    ]

class ProfessionsAndSkillsForm(forms.ModelForm):
    class Meta:
        model = ProfessionsAndSkills
        fields = [
            # Dropdown Values
            'actor_category',
            # Multi-Select Values
            'model_categories', 'performer_categories', 'influencer_categories',
            'skills', 'main_skill'
        ]
        widgets = {
            'model_categories': forms.Textarea(attrs={'rows': 3}),
            'performer_categories': forms.Textarea(attrs={'rows': 3}),
            'influencer_categories': forms.Textarea(attrs={'rows': 3}),
            'skills': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make fields optional
        for field in self.fields:
            self.fields[field].required = False

class SocialMediaForm(forms.ModelForm):
    class Meta:
        model = SocialMedia
        fields = [
            # Social Media Platform URLs/Usernames
            'instagram', 'facebook', 'youtube', 'tiktok'
        ]
        widgets = {
            'instagram': forms.URLInput(attrs={'placeholder': 'https://instagram.com/username or @username'}),
            'facebook': forms.URLInput(attrs={'placeholder': 'https://facebook.com/username'}),
            'youtube': forms.URLInput(attrs={'placeholder': 'https://youtube.com/@channel'}),
            'tiktok': forms.URLInput(attrs={'placeholder': 'https://tiktok.com/@username'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # All fields are optional, but at least one social media platform is required (validated in clean)
        for field in self.fields:
            self.fields[field].required = False

    def clean(self):
        cleaned_data = super().clean()
        # Validate that at least one social media platform is provided
        social_platforms = [cleaned_data.get('instagram'), cleaned_data.get('facebook'), 
                          cleaned_data.get('youtube'), cleaned_data.get('tiktok')]
        if not any(platform for platform in social_platforms):
            raise ValidationError("At least one social media platform is required.")
        return cleaned_data

class HeadshotForm(forms.ModelForm):
    class Meta:
        model = Headshot
        fields = ['professional_headshot']
        widgets = {
            'professional_headshot': forms.ClearableFileInput(attrs={'accept': 'image/jpeg,image/png'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Professional headshot is required
        self.fields['professional_headshot'].required = True

    def clean_professional_headshot(self):
        headshot = self.cleaned_data.get('professional_headshot')
        if headshot:
            # Validate file extension
            valid_extensions = ['.jpg', '.jpeg', '.png']
            ext = os.path.splitext(headshot.name)[1].lower()
            if ext not in valid_extensions:
                raise ValidationError("Professional headshot must be a JPG or PNG image file.")
            
            # Validate file size (5MB limit)
            if headshot.size > 5 * 1024 * 1024:
                raise ValidationError("Professional headshot file size must not exceed 5MB.")
        
        return headshot

class NaturalPhotosForm(forms.ModelForm):
    class Meta:
        model = NaturalPhotos
        fields = ['natural_photo_1', 'natural_photo_2']
        widgets = {
            'natural_photo_1': forms.ClearableFileInput(attrs={'accept': 'image/jpeg,image/png'}),
            'natural_photo_2': forms.ClearableFileInput(attrs={'accept': 'image/jpeg,image/png'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Both natural photos are required
        self.fields['natural_photo_1'].required = True
        self.fields['natural_photo_2'].required = True

    def clean_natural_photo_1(self):
        photo = self.cleaned_data.get('natural_photo_1')
        if photo:
            # Validate file extension
            valid_extensions = ['.jpg', '.jpeg', '.png']
            ext = os.path.splitext(photo.name)[1].lower()
            if ext not in valid_extensions:
                raise ValidationError("First natural photo must be a JPG or PNG image file.")
            
            # Validate file size (5MB limit)
            if photo.size > 5 * 1024 * 1024:
                raise ValidationError("First natural photo file size must not exceed 5MB.")
        
        return photo

    def clean_natural_photo_2(self):
        photo = self.cleaned_data.get('natural_photo_2')
        if photo:
            # Validate file extension
            valid_extensions = ['.jpg', '.jpeg', '.png']
            ext = os.path.splitext(photo.name)[1].lower()
            if ext not in valid_extensions:
                raise ValidationError("Second natural photo must be a JPG or PNG image file.")
            
            # Validate file size (5MB limit)
            if photo.size > 5 * 1024 * 1024:
                raise ValidationError("Second natural photo file size must not exceed 5MB.")
        
        return photo

class ProfessionsAndSkillsInline(admin.StackedInline):
    model = ProfessionsAndSkills
    form = ProfessionsAndSkillsForm
    can_delete = True
    extra = 0
    fields = [
        'actor_category',
        'model_categories',
        'performer_categories',
        'influencer_categories',
        'skills',
        'main_skill',
    ]

class SocialMediaInline(admin.StackedInline):
    model = SocialMedia
    form = SocialMediaForm
    can_delete = True
    extra = 0
    fieldsets = (
        ('Social Media Platforms', {
            'fields': (
                ('instagram', 'facebook'),
                ('youtube', 'tiktok')
            ),
            'description': 'Enter URLs or usernames for your social media accounts. At least one platform is required.'
        }),
    )

class HeadshotInline(admin.StackedInline):
    model = Headshot
    form = HeadshotForm
    can_delete = True
    extra = 0
    fieldsets = (
        ('Professional Headshot', {
            'fields': ('professional_headshot',),
            'description': 'Upload a professional headshot photo in JPG or PNG format.'
        }),
    )

class NaturalPhotosInline(admin.StackedInline):
    model = NaturalPhotos
    form = NaturalPhotosForm
    can_delete = True
    extra = 0
    fieldsets = (
        ('Natural Photos', {
            'fields': (
                'natural_photo_1',
                'natural_photo_2'
            ),
            'description': 'Upload two natural photos in JPG or PNG format. Both photos are required.'
        }),
    )

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    form = ProfileForm
    list_display = ['name', 'user', 'profession', 'nationality', 'location', 'created_at', 'availability_status', 'verified', 'flagged', 'status']
    list_filter = ['availability_status', 'verified', 'flagged', 'status']
    search_fields = ['name', 'user__username', 'user__email', 'profession', 'nationality', 'location']
    readonly_fields = ['created_at', 'age']
    inlines = [
        BasicInformationInline,
        LocationInformationInline,
        ProfessionsAndSkillsInline,
        IdentityVerificationInline,
        ExperienceInline,
        PhysicalAttributesInline,
        MedicalInfoInline,
        EducationInline,
        WorkExperienceInline,
        ContactInfoInline,
        PersonalInfoInline,
        MediaInline,
        SocialMediaInline,
        HeadshotInline,
        NaturalPhotosInline
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