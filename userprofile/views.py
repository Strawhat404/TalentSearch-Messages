from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .models import Profile, VerificationStatus, VerificationAuditLog, Headshot
from .serializers import ProfileSerializer, VerificationStatusSerializer, VerificationAuditLogSerializer, PublicProfileSerializer
import os
from django.conf import settings
from django.db import IntegrityError
from django.shortcuts import get_object_or_404

@method_decorator(csrf_exempt, name='dispatch')
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
                        "professions_and_skills": {
                            "professions": [],
                            "actor_category": [],
                            "model_categories": [],
                            "performer_categories": [],
                            "influencer_categories": [],
                            "skills": [],
                            "main_skill": [],
                            "skill_description": None,
                            "video_url": None
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
                        "personal_info": {
                            "marital_status": None,
                            "ethnicity": None,
                            "personality_type": None,
                            "work_preference": None,
                            "hobbies": [],
                            "volunteer_experience": None,
                            "company_culture_preference": None,
                            "language_proficiency": [],
                            "special_skills": [],
                            "tools_experience": [],
                            "award_recognitions": []
                        },
                        "natural_photos": {
                            "natural_photo_1": None,
                            "natural_photo_2": None
                        },
                        "headshot": {
                            "professional_headshot": None
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
                        "professions_and_skills": {
                            "professions": [],
                            "actor_category": [],
                            "model_categories": [],
                            "performer_categories": [],
                            "influencer_categories": [],
                            "skills": [],
                            "main_skill": [],
                            "skill_description": None,
                            "video_url": None
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
                        "personal_info": {
                            "marital_status": None,
                            "ethnicity": None,
                            "personality_type": None,
                            "work_preference": None,
                            "hobbies": [],
                            "volunteer_experience": None,
                            "company_culture_preference": None,
                            "language_proficiency": [],
                            "special_skills": [],
                            "tools_experience": [],
                            "award_recognitions": []
                        },
                        "natural_photos": {
                            "natural_photo_1": None,
                            "natural_photo_2": None
                        },
                        "headshot": {
                            "professional_headshot": None
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
            for nested_field in ['identity_verification', 'professions_and_skills', 'physical_attributes',
                               'medical_info', 'personal_info', 'social_media', 'headshot', 'natural_photos']:
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
                                # Create a new instance - import the model dynamically
                                from userprofile.models import (
                                    IdentityVerification, ProfessionsAndSkills, PhysicalAttributes,
                                    MedicalInfo, PersonalInfo, SocialMedia, Headshot, NaturalPhotos
                                )
                                
                                model_mapping = {
                                    'identity_verification': IdentityVerification,
                                    'professions_and_skills': ProfessionsAndSkills,
                                    'physical_attributes': PhysicalAttributes,
                                    'medical_info': MedicalInfo,
                                    'personal_info': PersonalInfo,
                                    'social_media': SocialMedia,
                                    'headshot': Headshot,
                                    'natural_photos': NaturalPhotos
                                }
                                
                                model_class = model_mapping.get(nested_field)
                                if model_class:
                                    model_class.objects.create(profile=profile, **nested_data)
                                else:
                                    raise Exception(f"Unknown nested field: {nested_field}")
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

@method_decorator(csrf_exempt, name='dispatch')
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

@method_decorator(csrf_exempt, name='dispatch')
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

@method_decorator(csrf_exempt, name='dispatch')
class PublicProfilesView(APIView):
    """
    Public endpoint to fetch all profiles with limited data
    """
    def get_permissions(self):
        """
        Allow public access for GET requests only
        """
        if self.request.method == 'GET':
            return []  # No authentication required for GET
        return [IsAuthenticated()]  # Require authentication for other methods

    @swagger_auto_schema(
        tags=['public-profiles'],
        summary="Get all public profiles",
        description="Retrieve all public profiles with limited information (no sensitive data). Anyone can access this endpoint without authentication.",
        parameters=[
            openapi.Parameter(
                'profession',
                openapi.IN_QUERY,
                description="Filter profiles by profession",
                type=openapi.TYPE_STRING,
                required=False
            ),
            openapi.Parameter(
                'location',
                openapi.IN_QUERY,
                description="Filter profiles by location",
                type=openapi.TYPE_STRING,
                required=False
            ),
            openapi.Parameter(
                'verified',
                openapi.IN_QUERY,
                description="Filter by verification status (true/false)",
                type=openapi.TYPE_BOOLEAN,
                required=False
            ),
            openapi.Parameter(
                'available',
                openapi.IN_QUERY,
                description="Filter by availability status (true/false)",
                type=openapi.TYPE_BOOLEAN,
                required=False
            ),
        ],
        responses={
            200: openapi.Response(
                description="Public profiles retrieved successfully",
                schema=PublicProfileSerializer(many=True),
                examples={
                    'application/json': [
                        {
                            "id": 1,
                            "name": "John Doe",
                            "profession": "actor",
                            "age": 28,
                            "location": "Los Angeles",
                            "created_at": "2025-01-15T10:30:00Z",
                            "availability_status": True,
                            "verified": True,
                            "status": "active",
                            "professions_and_skills": {
                                "professions": ["actor", "model"],
                                "actor_category": [],
                                "model_categories": [],
                                "performer_categories": [],
                                "influencer_categories": [],
                                "skills": ["acting", "dancing", "singing"],
                                "main_skill": [],
                                "skill_description": "Professional actor with 3-5 years experience",
                                "video_url": "https://example.com/portfolio"
                            },
                            "physical_attributes": {
                                "gender": "male",
                                "hair_color": "brown",
                                "eye_color": "blue",
                                "body_type": "athletic",
                                "skin_tone": "fair"
                            },
                            "medical_info": {
                                "health_conditions": [],
                                "medications": [],
                                "disability_status": None,
                                "disability_type": None
                            },
                            "personal_info": {
                                "marital_status": None,
                                "ethnicity": None,
                                "personality_type": None,
                                "work_preference": None,
                                "hobbies": [],
                                "volunteer_experience": None,
                                "company_culture_preference": None,
                                "language_proficiency": [],
                                "special_skills": [],
                                "tools_experience": [],
                                "award_recognitions": []
                            },
                            "natural_photos": {
                                "natural_photo_1": None,
                                "natural_photo_2": None
                            },
                            "headshot": {
                                "professional_headshot": None
                            }
                        }
                    ]
                }
            ),
        }
    )
    def get(self, request):
        try:
            # Get all profiles that are available and not flagged
            profiles = Profile.objects.filter(
                availability_status=True,
                flagged=False
            ).select_related(
                'professions_and_skills',
                'physical_attributes',
                'medical_info',
                'personal_info',
                'headshot',
                'natural_photos'
            ).order_by('-created_at')

            # Apply filters if provided
            profession = request.query_params.get('profession')
            if profession:
                profiles = profiles.filter(profession__icontains=profession)

            location = request.query_params.get('location')
            if location:
                profiles = profiles.filter(location__icontains=location)

            verified = request.query_params.get('verified')
            if verified is not None:
                verified_bool = verified.lower() == 'true'
                profiles = profiles.filter(verified=verified_bool)

            available = request.query_params.get('available')
            if available is not None:
                available_bool = available.lower() == 'true'
                profiles = profiles.filter(availability_status=available_bool)

            serializer = PublicProfileSerializer(profiles, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
