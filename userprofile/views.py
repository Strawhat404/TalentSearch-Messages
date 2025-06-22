from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from .models import Profile, VerificationStatus, VerificationAuditLog
from .serializers import ProfileSerializer, VerificationStatusSerializer, VerificationAuditLogSerializer
import os
import json
from django.conf import settings
from django.db import IntegrityError

class ProfileView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    @swagger_auto_schema(
        tags=['profile'],
        summary="Get user profile",
        description="Retrieve the authenticated user's profile.",
        responses={
            200: openapi.Response(
                description="Profile retrieved successfully",
                schema=ProfileSerializer,
                examples={
                    'application/json': {
                        "id": 3,
                        "name": "mak",
                        "email": "makdatse@gmail.com",
                        "birthdate": "2001-05-16",
                        "profession": "actor",
                        "nationality": "ethiopian",
                        "age": 24,
                        "location": "",
                        "created_at": "2025-05-27T05:37:38.297856Z",
                        "availability_status": True,
                        "verified": False,
                        "flagged": False,
                        "status": "",
                        "identity_verification": {
                            "id_type": None,
                            "id_number": None,
                            "id_expiry_date": None,
                            "id_front": None,
                            "id_back": None
                        },
                        "experience": {
                            "experience_level": None,
                            "skills": [],
                            "work_authorization": None,
                            "industry_experience": None,
                            "min_salary": None,
                            "max_salary": None,
                            "availability": None,
                            "preferred_work_location": None,
                            "shift_preference": None,
                            "willingness_to_relocate": None,
                            "overtime_availability": None,
                            "travel_willingness": None,
                            "software_proficiency": [],
                            "typing_speed": None,
                            "driving_skills": None,
                            "equipment_experience": [],
                            "role_title": None,
                            "portfolio_url": None,
                            "union_membership": None,
                            "reference": [],
                            "available_start_date": None,
                            "preferred_company_size": None,
                            "preferred_industry": [],
                            "leadership_style": None,
                            "communication_style": None,
                            "motivation": None,
                            "has_driving_license": False
                        },
                        "physical_attributes": {
                            "weight": None,
                            "height": None,
                            "gender": None,
                            "hair_color": None,
                            "eye_color": None,
                            "body_type": None,
                            "skin_tone": None,
                            "facial_hair": None,
                            "tattoos_visible": False,
                            "piercings_visible": False,
                            "physical_condition": None
                        },
                        "medical_info": {
                            "health_conditions": [],
                            "medications": [],
                            "disability_status": None,
                            "disability_type": None
                        },
                        "education": {
                            "education_level": None,
                            "degree_type": None,
                            "field_of_study": None,
                            "graduation_year": None,
                            "gpa": None,
                            "institution_name": None,
                            "scholarships": [],
                            "academic_achievements": [],
                            "certifications": [],
                            "online_courses": []
                        },
                        "work_experience": {
                            "years_of_experience": None,
                            "employment_status": None,
                            "previous_employers": [],
                            "projects": [],
                            "training": [],
                            "internship_experience": None
                        },
                        "contact_info": {
                            "address": None,
                            "city": None,
                            "region": None,
                            "postal_code": None,
                            "residence_type": None,
                            "residence_duration": None,
                            "housing_status": None,
                            "emergency_contact": None,
                            "emergency_phone": None
                        },
                        "personal_info": {
                            "marital_status": None,
                            "ethnicity": None,
                            "personality_type": None,
                            "work_preference": None,
                            "hobbies": [],
                            "volunteer_experience": None,
                            "company_culture_preference": None,
                            "social_media_links": {},
                            "social_media_handles": [],
                            "language_proficiency": [],
                            "special_skills": [],
                            "tools_experience": [],
                            "award_recognitions": []
                        },
                        "media": {
                            "video": None,
                            "photo": None
                        }
                    }
                }
            ),
            404: openapi.Response(description="Profile not found"),
            401: openapi.Response(description="Unauthorized"),
        }
    )
    def get(self, request):
        try:
            profile = Profile.objects.get(user=request.user)
            serializer = ProfileSerializer(profile)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Profile.DoesNotExist:
            return Response({"message": "Profile not found."}, status=status.HTTP_404_NOT_FOUND)

    @swagger_auto_schema(
        tags=['profile'],
        summary="Create user profile",
        description="Create a new user profile with required and optional fields.",
        request_body=ProfileSerializer,
        responses={
            201: openapi.Response(
                description="Profile created successfully",
                schema=ProfileSerializer,
                examples={
                    'application/json': {
                        "id": 3,
                        "name": "mak",
                        "email": "makdatse@gmail.com",
                        "birthdate": "2001-05-16",
                        "profession": "actor",
                        "nationality": "ethiopian",
                        "age": 24,
                        "location": "",
                        "created_at": "2025-05-27T05:37:38.297856Z",
                        "availability_status": True,
                        "verified": False,
                        "flagged": False,
                        "status": "",
                        "identity_verification": {
                            "id_type": None,
                            "id_number": None,
                            "id_expiry_date": None,
                            "id_front": None,
                            "id_back": None
                        },
                        "experience": {
                            "experience_level": None,
                            "skills": [],
                            "work_authorization": None,
                            "industry_experience": None,
                            "min_salary": None,
                            "max_salary": None,
                            "availability": None,
                            "preferred_work_location": None,
                            "shift_preference": None,
                            "willingness_to_relocate": None,
                            "overtime_availability": None,
                            "travel_willingness": None,
                            "software_proficiency": [],
                            "typing_speed": None,
                            "driving_skills": None,
                            "equipment_experience": [],
                            "role_title": None,
                            "portfolio_url": None,
                            "union_membership": None,
                            "reference": [],
                            "available_start_date": None,
                            "preferred_company_size": None,
                            "preferred_industry": [],
                            "leadership_style": None,
                            "communication_style": None,
                            "motivation": None,
                            "has_driving_license": False
                        },
                        "physical_attributes": {
                            "weight": None,
                            "height": None,
                            "gender": None,
                            "hair_color": None,
                            "eye_color": None,
                            "body_type": None,
                            "skin_tone": None,
                            "facial_hair": None,
                            "tattoos_visible": False,
                            "piercings_visible": False,
                            "physical_condition": None
                        },
                        "medical_info": {
                            "health_conditions": [],
                            "medications": [],
                            "disability_status": None,
                            "disability_type": None
                        },
                        "education": {
                            "education_level": None,
                            "degree_type": None,
                            "field_of_study": None,
                            "graduation_year": None,
                            "gpa": None,
                            "institution_name": None,
                            "scholarships": [],
                            "academic_achievements": [],
                            "certifications": [],
                            "online_courses": []
                        },
                        "work_experience": {
                            "years_of_experience": None,
                            "employment_status": None,
                            "previous_employers": [],
                            "projects": [],
                            "training": [],
                            "internship_experience": None
                        },
                        "contact_info": {
                            "address": None,
                            "city": None,
                            "region": None,
                            "postal_code": None,
                            "residence_type": None,
                            "residence_duration": None,
                            "housing_status": None,
                            "emergency_contact": None,
                            "emergency_phone": None
                        },
                        "personal_info": {
                            "marital_status": None,
                            "ethnicity": None,
                            "personality_type": None,
                            "work_preference": None,
                            "hobbies": [],
                            "volunteer_experience": None,
                            "company_culture_preference": None,
                            "social_media_links": {},
                            "social_media_handles": [],
                            "language_proficiency": [],
                            "special_skills": [],
                            "tools_experience": [],
                            "award_recognitions": []
                        },
                        "media": {
                            "video": None,
                            "photo": None
                        }
                    }
                }
            ),
            400: openapi.Response(description="Validation error"),
            401: openapi.Response(description="Unauthorized"),
        }
    )
    def post(self, request):
        try:
            if Profile.objects.filter(user=request.user).exists():
                return Response(
                    {"message": "Profile already exists for this user."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer = ProfileSerializer(data=request.data, context={'request': request})
            if serializer.is_valid():
                profile = serializer.save()
                response_data = {
                    "id": profile.id,
                    "message": "Profile created successfully."
                }
                return Response(response_data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"message": f"An error occurred while creating the profile: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        tags=['profile'],
        summary="Update user profile",
        description="Update an existing user profile with partial data.",
        request_body=ProfileSerializer,
        responses={
            200: openapi.Response(
                description="Profile updated successfully",
                schema=ProfileSerializer
            ),
            400: openapi.Response(description="Validation error"),
            401: openapi.Response(description="Unauthorized"),
            404: openapi.Response(description="Profile not found"),
        }
    )
    def patch(self, request):
        try:
            profile = Profile.objects.get(user=request.user)
            # Create a copy of the data to avoid modifying the original
            data = request.data.copy()
            
            # Remove fields that shouldn't be updated
            for field in ['user', 'id', 'email', 'age', 'created_at', 'verified', 'flagged']:
                if field in data:
                    del data[field]
            
            # Handle nested data
            for nested_field in ['identity_verification', 'experience', 'physical_attributes',
                               'medical_info', 'education', 'work_experience', 'contact_info',
                               'personal_info', 'media']:
                if nested_field in data:
                    try:
                        nested_data = data[nested_field]
                        if isinstance(nested_data, dict):
                            # Get the existing nested instance
                            nested_instance = getattr(profile, nested_field, None)
                            if nested_instance:
                                # Update the existing instance
                                for key, value in nested_data.items():
                                    setattr(nested_instance, key, value)
                                nested_instance.save()
                            else:
                                # Create a new instance
                                nested_model = getattr(profile, f'{nested_field}_set').model
                                nested_model.objects.create(profile=profile, **nested_data)
                            # Remove the nested data from the main data
                            del data[nested_field]
                    except Exception as e:
                        print(f"Error processing {nested_field}: {str(e)}")
                        raise Exception(f"Error processing {nested_field}: {str(e)}")
            
            # Update the main profile fields
            for attr, value in data.items():
                setattr(profile, attr, value)
            profile.save()

            response_data = {
                "id": profile.id,
                "message": "Profile updated successfully."
            }
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Profile.DoesNotExist:
            return Response({"message": "Profile not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            import traceback
            print(f"Full error: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            return Response(
                {"message": f"An error occurred while updating the profile: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        tags=['profile'],
        summary="Delete user profile",
        description="Delete the authenticated user's profile.",
        responses={
            200: openapi.Response(
                description="Profile deleted successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "message": openapi.Schema(type=openapi.TYPE_STRING, example="Profile deleted successfully.")
                    }
                ),
                examples={
                    'application/json': {
                        "message": "Profile deleted successfully."
                    }
                }
            ),
            404: openapi.Response(description="Profile not found"),
            401: openapi.Response(description="Unauthorized"),
        }
    )
    def delete(self, request):
        try:
            profile = Profile.objects.get(user=request.user)
            user = request.user
            profile.delete()
            user.delete()
            return Response({"message": "Profile deleted successfully."}, status=status.HTTP_200_OK)
        except Profile.DoesNotExist:
            return Response({"message": "Profile not found."}, status=status.HTTP_404_NOT_FOUND)

class VerificationView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    @swagger_auto_schema(
        tags=['verification'],
        summary="Verify a profile",
        description="Verify a user profile with proper documentation and notes.",
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'verification_type': {'type': 'string', 'enum': ['id', 'address', 'phone']},
                    'verification_method': {'type': 'string', 'enum': ['document', 'phone_call', 'email']},
                    'verification_notes': {'type': 'string'},
                },
                'required': ['verification_type', 'verification_method']
            }
        },
        responses={
            200: openapi.Response(
                description="Profile verified successfully",
                schema=VerificationStatusSerializer
            ),
            400: openapi.Response(description="Validation error"),
            401: openapi.Response(description="Unauthorized"),
            403: openapi.Response(description="Permission denied"),
            404: openapi.Response(description="Profile not found"),
        }
    )
    def post(self, request, profile_id):
        try:
            profile = Profile.objects.get(id=profile_id)
            
            # Check if user has permission to verify
            if not request.user.has_perm('userprofile.verify_profiles'):
                return Response(
                    {"message": "You don't have permission to verify profiles."},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Create or update verification status
            verification, created = VerificationStatus.objects.get_or_create(
                profile=profile,
                defaults={
                    'is_verified': True,
                    'verification_type': request.data.get('verification_type'),
                    'verified_by': request.user,
                    'verification_method': request.data.get('verification_method'),
                    'verification_notes': request.data.get('verification_notes', '')
                }
            )

            if not created:
                verification.is_verified = True
                verification.verification_type = request.data.get('verification_type')
                verification.verified_by = request.user
                verification.verification_method = request.data.get('verification_method')
                verification.verification_notes = request.data.get('verification_notes', '')
                verification.save()

            # Create audit log
            VerificationAuditLog.objects.create(
                profile=profile,
                previous_status=False,
                new_status=True,
                changed_by=request.user,
                verification_type=verification.verification_type,
                verification_method=verification.verification_method,
                notes=verification.verification_notes,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT')
            )

            return Response({
                "message": "Profile verified successfully",
                "verification": VerificationStatusSerializer(verification).data
            }, status=status.HTTP_200_OK)

        except Profile.DoesNotExist:
            return Response(
                {"message": "Profile not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"message": f"An error occurred: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

class VerificationAuditLogView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=['verification'],
        summary="Get verification audit logs",
        description="Get the audit logs for profile verifications.",
        responses={
            200: openapi.Response(
                description="Audit logs retrieved successfully",
                schema=VerificationAuditLogSerializer(many=True)
            ),
            401: openapi.Response(description="Unauthorized"),
            403: openapi.Response(description="Permission denied"),
        }
    )
    def get(self, request, profile_id):
        try:
            profile = Profile.objects.get(id=profile_id)
            
            # Check if user has permission to view audit logs
            if not request.user.has_perm('userprofile.view_verification_logs'):
                return Response(
                    {"message": "You don't have permission to view verification logs."},
                    status=status.HTTP_403_FORBIDDEN
                )

            logs = VerificationAuditLog.objects.filter(profile=profile)
            serializer = VerificationAuditLogSerializer(logs, many=True)
            
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Profile.DoesNotExist:
            return Response(
                {"message": "Profile not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"message": f"An error occurred: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

class ChoiceDataView(APIView):
    """
    View to serve choice data for various fields
    """
    def get(self, request):
        data_dir = os.path.join(settings.BASE_DIR, 'userprofile', 'data')
        response_data = {}
        
        # Load basic information bundle
        with open(os.path.join(data_dir, 'basic_information.json'), 'r') as f:
            basic_info_data = json.load(f)
            basic_info = basic_info_data.get('basic_information', {})
            
            # Extract all basic information fields
            response_data.update({
                'nationalities': basic_info.get('nationality', []),
                'languages': basic_info.get('languages', []),
                'genders': basic_info.get('gender', []),
                'hair_colors': basic_info.get('hair_color', []),
                'eye_colors': basic_info.get('eye_color', []),
                'skin_tones': basic_info.get('skin_tone', []),
                'body_types': basic_info.get('body_type', []),
                'medical_conditions': basic_info.get('medical_condition', []),
                'medicine_types': basic_info.get('medicine_type', []),
                'marital_statuses': basic_info.get('marital_status', []),
                'hobbies': basic_info.get('hobbies', [])
            })
        
        # Load location information bundle
        with open(os.path.join(data_dir, 'location_information.json'), 'r') as f:
            location_info_data = json.load(f)
            location_info = location_info_data.get('location_information', {})
            
            # Extract all location information fields
            response_data.update({
                'housing_status': location_info.get('housing_status', []),
                'regions': location_info.get('regions', []),
                'duration': location_info.get('duration', []),
                'cities': location_info.get('cities', {}),
                'countries': location_info.get('countries', [])
            })

        # Load professions
        with open(os.path.join(data_dir, 'professions.json'), 'r') as f:
            response_data['professions'] = json.load(f)['professions']

        # Load skills
        with open(os.path.join(data_dir, 'skills.json'), 'r') as f:
            response_data['skills'] = json.load(f)['skills']

        # Load professional choices
        with open(os.path.join(data_dir, 'professional_choices.json'), 'r') as f:
            professional_data = json.load(f)
            response_data.update({
                'experience_levels': professional_data['experience_levels'],
                'work_authorizations': professional_data['work_authorizations'],
                'industry_experiences': professional_data['industry_experiences'],
                'availabilities': professional_data['availabilities'],
                'work_locations': professional_data['work_locations'],
                'shift_preferences': professional_data['shift_preferences'],
                'company_sizes': professional_data['company_sizes'],
                'leadership_styles': professional_data['leadership_styles'],
                'communication_styles': professional_data['communication_styles'],
                'motivations': professional_data['motivations']
            })

        # Load medical info for disability statuses (backward compatibility)
        with open(os.path.join(data_dir, 'medical_info.json'), 'r') as f:
            medical_data = json.load(f)
            response_data.update({
                'disability_statuses': medical_data['disability_statuses'],
                'disability_types': medical_data['disability_types']
            })

        # Load influencer categories
        with open(os.path.join(data_dir, 'influencer_categories.json'), 'r') as f:
            response_data['influencer_categories'] = json.load(f)['categories']

        # Load performer categories
        with open(os.path.join(data_dir, 'performer_categories.json'), 'r') as f:
            response_data['performer_categories'] = json.load(f)['categories']

        # Load model categories
        with open(os.path.join(data_dir, 'model_categories.json'), 'r') as f:
            response_data['model_categories'] = json.load(f)['categories']
        
        return Response(response_data)
