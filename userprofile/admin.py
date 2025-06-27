from django.contrib import admin
from django import forms
from django.core.files.storage import default_storage
from django.contrib import messages
from .models import (
    Profile, BasicInformation, LocationInformation, IdentityVerification, ProfessionsAndSkills, PhysicalAttributes,
    MedicalInfo, PersonalInfo, SocialMedia, Headshot, NaturalPhotos
)
import os
from django.core.exceptions import ValidationError

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['user', 'birthdate', 'profession', 'location', 'availability_status', 'verified', 'flagged', 'status']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only make fields other than 'birthdate', 'profession', and 'user' optional
        for field in self.fields:
            if field not in ['birthdate', 'profession', 'user']:
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

class ProfessionalQualificationsForm(forms.ModelForm):
    class Meta:
        model = ProfessionsAndSkills
        fields = [
            'is_actor', 'is_model', 'is_performer', 'is_host', 'is_influencer', 'is_voice_over', 'is_cameraman', 'is_presenter', 'is_stuntman',
            'professions', 'actor_category', 'model_categories', 'performer_categories', 'influencer_categories',
            'skills', 'main_skill', 'skill_description', 'video_url'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].required = False

class PhysicalAttributesForm(forms.ModelForm):
    class Meta:
        model = PhysicalAttributes
        fields = [
            'facial_hair', 'physical_condition'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].required = False

class MedicalInfoForm(forms.ModelForm):
    class Meta:
        model = MedicalInfo
        fields = ['disability_status', 'disability_type']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].required = False

class PersonalInfoForm(forms.ModelForm):
    class Meta:
        model = PersonalInfo
        fields = [
            'first_name',
            'last_name',
            'language_proficiency',
            'custom_language'
        ]
        widgets = {
            'language_proficiency': forms.CheckboxSelectMultiple(),
        }

    def clean(self):
        cleaned_data = super().clean()
        # Add any custom validation here if needed
        return cleaned_data

class SocialMediaForm(forms.ModelForm):
    class Meta:
        model = SocialMedia
        fields = [
            'instagram_username', 'instagram_followers', 'facebook_username', 
            'facebook_followers', 'youtube_username', 'youtube_followers', 
            'tiktok_username', 'tiktok_followers'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].required = False

class HeadshotForm(forms.ModelForm):
    class Meta:
        model = Headshot
        fields = ['professional_headshot']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].required = False

    def clean(self):
        cleaned_data = super().clean()
        clear_field = "professional_headshot-clear"
        if clear_field in self.data and self.data[clear_field] == 'on':
            cleaned_data['professional_headshot'] = None
        else:
            file = cleaned_data.get('professional_headshot')
            if file:
                valid_extensions = ['.jpg', '.jpeg', '.png']
                ext = os.path.splitext(file.name)[1].lower()
                if ext not in valid_extensions:
                    raise ValidationError("Professional headshot must be an image file (.jpg, .jpeg, .png).")
                max_size = 5 * 1024 * 1024  # 5MB
                if file.size > max_size:
                    raise ValidationError("Professional headshot file size must not exceed 5MB.")
        return cleaned_data

class BasicInformationForm(forms.ModelForm):
    class Meta:
        model = BasicInformation
        fields = [
            'nationality', 'gender', 'languages', 'hair_color', 'eye_color', 'skin_tone',
            'body_type', 'medical_condition', 'medicine_type', 'marital_status', 'hobbies',
            'date_of_birth', 'height', 'weight', 'emergency_contact_name', 'emergency_contact_phone',
            'custom_hobby', 'driving_license', 'visible_piercings', 'visible_tattoos', 'willing_to_travel'
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'languages': forms.CheckboxSelectMultiple(),
            'medical_condition': forms.CheckboxSelectMultiple(),
            'medicine_type': forms.CheckboxSelectMultiple(),
            'hobbies': forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].required = False

class LocationInformationForm(forms.ModelForm):
    class Meta:
        model = LocationInformation
        fields = [
            'housing_status', 'region', 'duration', 'city', 'country',
            'address', 'specific_area'
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

class BasicInformationInline(admin.StackedInline):
    model = BasicInformation
    form = BasicInformationForm
    can_delete = True
    extra = 0
    fields = [
        'nationality', 'gender', 'languages', 'hair_color', 'eye_color', 'skin_tone',
        'body_type', 'medical_condition', 'medicine_type', 'marital_status', 'hobbies',
        'date_of_birth', 'height', 'weight', 'emergency_contact_name', 'emergency_contact_phone',
        'custom_hobby', 'driving_license', 'visible_piercings', 'visible_tattoos', 'willing_to_travel'
    ]

class LocationInformationInline(admin.StackedInline):
    model = LocationInformation
    form = LocationInformationForm
    can_delete = True
    extra = 0
    fields = [
        'housing_status', 'region', 'duration', 'city', 'country',
        'address', 'specific_area'
    ]

class ProfessionalQualificationsInline(admin.StackedInline):
    model = ProfessionsAndSkills
    form = ProfessionalQualificationsForm
    can_delete = True
    extra = 0
    fields = [
        'is_actor', 'is_model', 'is_performer', 'is_host', 'is_influencer', 'is_voice_over', 'is_cameraman', 'is_presenter', 'is_stuntman',
        'professions', 'actor_category', 'model_categories', 'performer_categories', 'influencer_categories',
        'skills', 'main_skill', 'skill_description', 'video_url'
    ]

class PhysicalAttributesInline(admin.StackedInline):
    model = PhysicalAttributes
    form = PhysicalAttributesForm
    can_delete = True
    extra = 0
    fields = [
        'facial_hair', 'physical_condition'
    ]

class MedicalInfoInline(admin.StackedInline):
    model = MedicalInfo
    form = MedicalInfoForm
    can_delete = True
    extra = 0
    fields = ['disability_status', 'disability_type']

class PersonalInfoInline(admin.StackedInline):
    model = PersonalInfo
    form = PersonalInfoForm
    can_delete = True
    extra = 0
    fields = [
        'first_name', 'last_name', 'language_proficiency', 'custom_language'
    ]

class SocialMediaInline(admin.StackedInline):
    model = SocialMedia
    form = SocialMediaForm
    can_delete = True
    extra = 0
    fields = [
        'instagram_username', 'instagram_followers', 'facebook_username', 
        'facebook_followers', 'youtube_username', 'youtube_followers', 
        'tiktok_username', 'tiktok_followers'
    ]

class HeadshotInline(admin.StackedInline):
    model = Headshot
    form = HeadshotForm
    can_delete = True
    extra = 0
    fields = ['professional_headshot']

class NaturalPhotosForm(forms.ModelForm):
    class Meta:
        model = NaturalPhotos
        fields = ['natural_photo_1', 'natural_photo_2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].required = False

    def clean(self):
        cleaned_data = super().clean()
        for field in ['natural_photo_1', 'natural_photo_2']:
            clear_field = f"{field}-clear"
            if clear_field in self.data and self.data[clear_field] == 'on':
                cleaned_data[field] = None
            else:
                file = cleaned_data.get(field)
                if file:
                    valid_extensions = ['.jpg', '.jpeg', '.png']
                    ext = os.path.splitext(file.name)[1].lower()
                    if ext not in valid_extensions:
                        raise ValidationError(f"{field} must be an image file (.jpg, .jpeg, .png).")
                    max_size = 5 * 1024 * 1024  # 5MB
                    if file.size > max_size:
                        raise ValidationError(f"{field} file size must not exceed 5MB.")
        return cleaned_data

class NaturalPhotosInline(admin.StackedInline):
    model = NaturalPhotos
    form = NaturalPhotosForm
    can_delete = True
    extra = 0
    fields = ['natural_photo_1', 'natural_photo_2']

class ProfileAdmin(admin.ModelAdmin):
    form = ProfileForm
    list_display = ['get_user_name', 'user', 'profession', 'location', 'created_at', 'availability_status', 'verified', 'flagged', 'status']
    list_filter = ['availability_status', 'verified', 'flagged', 'status']
    search_fields = ['user__name', 'user__username', 'user__email', 'profession', 'location']
    readonly_fields = ['created_at', 'age', 'get_user_name']
    inlines = [
        IdentityVerificationInline,
        BasicInformationInline,
        LocationInformationInline,
        ProfessionalQualificationsInline,
        PhysicalAttributesInline,
        MedicalInfoInline,
        PersonalInfoInline,
        SocialMediaInline,
        HeadshotInline,
        NaturalPhotosInline
    ]
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'birthdate', 'profession', 'location', 'status')
        }),
        ('Status', {
            'fields': ('availability_status', 'verified', 'flagged')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    def get_user_name(self, obj):
        return obj.name
    get_user_name.short_description = 'Name'

    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing an existing object
            return self.readonly_fields + ('user',)
        return self.readonly_fields

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        
        for instance in instances:
            if formset.model in [IdentityVerification, NaturalPhotos]:
                # Handle file uploads for these models
                if hasattr(instance, 'id_front') and instance.id_front:
                    # Process ID front image
                    pass
                elif hasattr(instance, 'id_back') and instance.id_back:
                    # Process ID back image
                    pass
            elif hasattr(instance, 'professional_headshot') and instance.professional_headshot:
                # Process headshot image
                pass
            elif hasattr(instance, 'natural_photo_1') and instance.natural_photo_1:
                # Process natural photo 1
                pass
            elif hasattr(instance, 'natural_photo_2') and instance.natural_photo_2:
                # Process natural photo 2
                pass
            
            instance.save()
        
        formset.save_m2m()

    def delete_model(self, request, obj):
        # Delete associated files before deleting the model
        try:
            # Delete identity verification files
            if hasattr(obj, 'identity_verification'):
                if obj.identity_verification.id_front:
                    if os.path.isfile(obj.identity_verification.id_front.path):
                        os.remove(obj.identity_verification.id_front.path)
                if obj.identity_verification.id_back:
                    if os.path.isfile(obj.identity_verification.id_back.path):
                        os.remove(obj.identity_verification.id_back.path)
            
            # Delete headshot files
            if hasattr(obj, 'headshot') and obj.headshot.professional_headshot:
                if os.path.isfile(obj.headshot.professional_headshot.path):
                    os.remove(obj.headshot.professional_headshot.path)
            
            # Delete natural photos files
            if hasattr(obj, 'natural_photos'):
                if obj.natural_photos.natural_photo_1:
                    if os.path.isfile(obj.natural_photos.natural_photo_1.path):
                        os.remove(obj.natural_photos.natural_photo_1.path)
                if obj.natural_photos.natural_photo_2:
                    if os.path.isfile(obj.natural_photos.natural_photo_2.path):
                        os.remove(obj.natural_photos.natural_photo_2.path)
            
        except Exception as e:
            messages.error(request, f"Error deleting files: {str(e)}")
        
        super().delete_model(request, obj)

admin.site.register(Profile, ProfileAdmin) 