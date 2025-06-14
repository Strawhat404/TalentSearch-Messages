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
        tags=['Profile'],
        operation_summary="Create Profile",
        operation_description="Create a new user profile with all required information",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['name', 'birthdate', 'profession', 'nationality', 'location', 'physical_attributes'],
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING, example="John Doe"),
                'birthdate': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE, example="1990-01-01"),
                'profession': openapi.Schema(type=openapi.TYPE_STRING, example="actor"),
                'nationality': openapi.Schema(type=openapi.TYPE_STRING, example="ethiopian"),
                'location': openapi.Schema(type=openapi.TYPE_STRING, example="Addis Ababa"),
                'physical_attributes': openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    required=['weight', 'height', 'gender', 'hair_color', 'eye_color', 'body_type', 'skin_tone'],
                    properties={
                        'weight': openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT, minimum=30, example=70.5),
                        'height': openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT, minimum=100, example=175.0),
                        'gender': openapi.Schema(type=openapi.TYPE_STRING, example="male"),
                        'hair_color': openapi.Schema(type=openapi.TYPE_STRING, example="black"),
                        'eye_color': openapi.Schema(type=openapi.TYPE_STRING, example="brown"),
                        'body_type': openapi.Schema(type=openapi.TYPE_STRING, example="athletic"),
                        'skin_tone': openapi.Schema(type=openapi.TYPE_STRING, example="medium"),
                        'facial_hair': openapi.Schema(type=openapi.TYPE_STRING, example="clean shaven"),
                        'tattoos_visible': openapi.Schema(type=openapi.TYPE_BOOLEAN, default=False),
                        'piercings_visible': openapi.Schema(type=openapi.TYPE_BOOLEAN, default=False),
                        'physical_condition': openapi.Schema(type=openapi.TYPE_STRING, example="excellent")
                    }
                ),
                'education': openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'education_level': openapi.Schema(type=openapi.TYPE_STRING, example="bachelor"),
                        'degree_type': openapi.Schema(type=openapi.TYPE_STRING, example="BA"),
                        'field_of_study': openapi.Schema(type=openapi.TYPE_STRING, example="Performing Arts"),
                        'graduation_year': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE, example="2020"),
                        'gpa': openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT, example=3.8),
                        'institution_name': openapi.Schema(type=openapi.TYPE_STRING, example="University of Arts"),
                        'scholarships': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
                        'academic_achievements': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
                        'certifications': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
                        'online_courses': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING))
                    }
                ),
                'work_experience': openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'years_of_experience': openapi.Schema(type=openapi.TYPE_INTEGER, minimum=0, example=5),
                        'employment_status': openapi.Schema(type=openapi.TYPE_STRING, example="full-time"),
                        'previous_employers': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
                        'projects': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
                        'training': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
                        'internship_experience': openapi.Schema(type=openapi.TYPE_STRING, example="6 months at XYZ Studio")
                    }
                ),
                'personal_info': openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'marital_status': openapi.Schema(type=openapi.TYPE_STRING, example="single"),
                        'ethnicity': openapi.Schema(type=openapi.TYPE_STRING, example="african"),
                        'personality_type': openapi.Schema(type=openapi.TYPE_STRING, example="extrovert"),
                        'work_preference': openapi.Schema(type=openapi.TYPE_STRING, example="flexible"),
                        'hobbies': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
                        'volunteer_experience': openapi.Schema(type=openapi.TYPE_STRING, example="Community theater"),
                        'company_culture_preference': openapi.Schema(type=openapi.TYPE_STRING, example="collaborative"),
                        'social_media': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
                        'other_social_media': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
                        'language_proficiency': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
                        'special_skills': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
                        'tools_experience': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
                        'award_recognitions': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING))
                    }
                ),
                'contact_info': openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'address': openapi.Schema(type=openapi.TYPE_STRING, example="123 Main St"),
                        'city': openapi.Schema(type=openapi.TYPE_STRING, example="Addis Ababa"),
                        'region': openapi.Schema(type=openapi.TYPE_STRING, example="Addis Ababa"),
                        'postal_code': openapi.Schema(type=openapi.TYPE_STRING, example="1000"),
                        'residence_type': openapi.Schema(type=openapi.TYPE_STRING, example="apartment"),
                        'residence_duration': openapi.Schema(type=openapi.TYPE_STRING, example="2 years"),
                        'housing_status': openapi.Schema(type=openapi.TYPE_STRING, example="renting"),
                        'emergency_contact': openapi.Schema(type=openapi.TYPE_STRING, example="Jane Doe"),
                        'emergency_phone': openapi.Schema(type=openapi.TYPE_STRING, example="+251911234567")
                    }
                )
            }
        ),
        responses={
            201: openapi.Response(
                description="Profile created successfully",
                schema=ProfileSerializer,
                examples={
                    'application/json': {
                        "id": 1,
                        "name": "John Doe",
                        "email": "john@example.com",
                        "birthdate": "1990-01-01",
                        "profession": "actor",
                        "nationality": "ethiopian",
                        "age": 34,
                        "location": "Addis Ababa",
                        "created_at": "2024-02-20T10:00:00Z",
                        "availability_status": True,
                        "verified": False,
                        "flagged": False,
                        "status": "active",
                        "physical_attributes": {
                            "weight": 70.5,
                            "height": 175.0,
                            "gender": "male",
                            "hair_color": "black",
                            "eye_color": "brown",
                            "body_type": "athletic",
                            "skin_tone": "medium",
                            "facial_hair": "clean shaven",
                            "tattoos_visible": False,
                            "piercings_visible": False,
                            "physical_condition": "excellent"
                        },
                        "education": {
                            "education_level": "bachelor",
                            "degree_type": "BA",
                            "field_of_study": "Performing Arts",
                            "graduation_year": "2020",
                            "gpa": 3.8,
                            "institution_name": "University of Arts",
                            "scholarships": ["Merit Scholarship"],
                            "academic_achievements": ["Dean's List"],
                            "certifications": ["Acting Certification"],
                            "online_courses": ["Advanced Acting Techniques"]
                        },
                        "work_experience": {
                            "years_of_experience": 5,
                            "employment_status": "full-time",
                            "previous_employers": ["ABC Studios"],
                            "projects": ["Movie X", "TV Show Y"],
                            "training": ["Method Acting"],
                            "internship_experience": "6 months at XYZ Studio"
                        },
                        "personal_info": {
                            "marital_status": "single",
                            "ethnicity": "african",
                            "personality_type": "extrovert",
                            "work_preference": "flexible",
                            "hobbies": ["dancing", "singing"],
                            "volunteer_experience": "Community theater",
                            "company_culture_preference": "collaborative",
                            "social_media": ["instagram.com/johndoe"],
                            "other_social_media": [],
                            "language_proficiency": ["English", "Amharic"],
                            "special_skills": ["Stage Combat"],
                            "tools_experience": ["Final Cut Pro"],
                            "award_recognitions": ["Best Actor 2023"]
                        },
                        "contact_info": {
                            "address": "123 Main St",
                            "city": "Addis Ababa",
                            "region": "Addis Ababa",
                            "postal_code": "1000",
                            "residence_type": "apartment",
                            "residence_duration": "2 years",
                            "housing_status": "renting",
                            "emergency_contact": "Jane Doe",
                            "emergency_phone": "+251911234567"
                        }
                    }
                }
            ),
            400: openapi.Response(
                description="Bad Request",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(type=openapi.TYPE_STRING),
                        'details': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            additionalProperties=openapi.Schema(
                                type=openapi.TYPE_ARRAY,
                                items=openapi.Schema(type=openapi.TYPE_STRING)
                            )
                        )
                    }
                ),
                examples={
                    'application/json': {
                        "error": "Validation Error",
                        "details": {
                            "birthdate": ["User must be at least 18 years old"],
                            "physical_attributes.weight": ["Weight must be at least 30 kg"]
                        }
                    }
                }
            ),
            401: openapi.Response(description="Unauthorized"),
            403: openapi.Response(description="Forbidden"),
            500: openapi.Response(description="Internal Server Error")
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
        tags=['Profile'],
        operation_summary="Update Profile",
        operation_description="Update an existing user profile. All fields are optional for update.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING, example="John Doe"),
                'birthdate': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE, example="1990-01-01"),
                'profession': openapi.Schema(type=openapi.TYPE_STRING, example="actor"),
                'nationality': openapi.Schema(type=openapi.TYPE_STRING, example="ethiopian"),
                'location': openapi.Schema(type=openapi.TYPE_STRING, example="Addis Ababa"),
                'physical_attributes': openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'weight': openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT, minimum=30, example=70.5),
                        'height': openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT, minimum=100, example=175.0),
                        'gender': openapi.Schema(type=openapi.TYPE_STRING, example="male"),
                        'hair_color': openapi.Schema(type=openapi.TYPE_STRING, example="black"),
                        'eye_color': openapi.Schema(type=openapi.TYPE_STRING, example="brown"),
                        'body_type': openapi.Schema(type=openapi.TYPE_STRING, example="athletic"),
                        'skin_tone': openapi.Schema(type=openapi.TYPE_STRING, example="medium"),
                        'facial_hair': openapi.Schema(type=openapi.TYPE_STRING, example="clean shaven"),
                        'tattoos_visible': openapi.Schema(type=openapi.TYPE_BOOLEAN, default=False),
                        'piercings_visible': openapi.Schema(type=openapi.TYPE_BOOLEAN, default=False),
                        'physical_condition': openapi.Schema(type=openapi.TYPE_STRING, example="excellent")
                    }
                ),
                'education': openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'education_level': openapi.Schema(type=openapi.TYPE_STRING, example="bachelor"),
                        'degree_type': openapi.Schema(type=openapi.TYPE_STRING, example="BA"),
                        'field_of_study': openapi.Schema(type=openapi.TYPE_STRING, example="Performing Arts"),
                        'graduation_year': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE, example="2020"),
                        'gpa': openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT, example=3.8),
                        'institution_name': openapi.Schema(type=openapi.TYPE_STRING, example="University of Arts"),
                        'scholarships': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
                        'academic_achievements': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
                        'certifications': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
                        'online_courses': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING))
                    }
                ),
                'work_experience': openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'years_of_experience': openapi.Schema(type=openapi.TYPE_INTEGER, minimum=0, example=5),
                        'employment_status': openapi.Schema(type=openapi.TYPE_STRING, example="full-time"),
                        'previous_employers': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
                        'projects': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
                        'training': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
                        'internship_experience': openapi.Schema(type=openapi.TYPE_STRING, example="6 months at XYZ Studio")
                    }
                ),
                'personal_info': openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'marital_status': openapi.Schema(type=openapi.TYPE_STRING, example="single"),
                        'ethnicity': openapi.Schema(type=openapi.TYPE_STRING, example="african"),
                        'personality_type': openapi.Schema(type=openapi.TYPE_STRING, example="extrovert"),
                        'work_preference': openapi.Schema(type=openapi.TYPE_STRING, example="flexible"),
                        'hobbies': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
                        'volunteer_experience': openapi.Schema(type=openapi.TYPE_STRING, example="Community theater"),
                        'company_culture_preference': openapi.Schema(type=openapi.TYPE_STRING, example="collaborative"),
                        'social_media': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
                        'other_social_media': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
                        'language_proficiency': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
                        'special_skills': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
                        'tools_experience': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
                        'award_recognitions': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING))
                    }
                ),
                'contact_info': openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'address': openapi.Schema(type=openapi.TYPE_STRING, example="123 Main St"),
                        'city': openapi.Schema(type=openapi.TYPE_STRING, example="Addis Ababa"),
                        'region': openapi.Schema(type=openapi.TYPE_STRING, example="Addis Ababa"),
                        'postal_code': openapi.Schema(type=openapi.TYPE_STRING, example="1000"),
                        'residence_type': openapi.Schema(type=openapi.TYPE_STRING, example="apartment"),
                        'residence_duration': openapi.Schema(type=openapi.TYPE_STRING, example="2 years"),
                        'housing_status': openapi.Schema(type=openapi.TYPE_STRING, example="renting"),
                        'emergency_contact': openapi.Schema(type=openapi.TYPE_STRING, example="Jane Doe"),
                        'emergency_phone': openapi.Schema(type=openapi.TYPE_STRING, example="+251911234567")
                    }
                )
            }
        ),
        responses={
            200: openapi.Response(
                description="Profile updated successfully",
                schema=ProfileSerializer
            ),
            400: openapi.Response(
                description="Bad Request",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(type=openapi.TYPE_STRING),
                        'details': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            additionalProperties=openapi.Schema(
                                type=openapi.TYPE_ARRAY,
                                items=openapi.Schema(type=openapi.TYPE_STRING)
                            )
                        )
                    }
                )
            ),
            401: openapi.Response(description="Unauthorized"),
            403: openapi.Response(description="Forbidden"),
            404: openapi.Response(description="Profile not found"),
            500: openapi.Response(description="Internal Server Error")
        }
    )
    def put(self, request):
        try:
            profile = Profile.objects.get(user=request.user)
            # Create a copy of the data to avoid modifying the original
            data = request.data.copy()
            
            # Remove fields that shouldn't be updated
            for field in ['user', 'id', 'email', 'age', 'created_at', 'verified', 'flagged']:
                if field in data:
                    del data[field]
            
            # Handle nested data
            for nested_field in ['identity_verification', 'professional_qualifications', 'physical_attributes',
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
        tags=['Profile'],
        operation_summary="Get Profile",
        operation_description="Retrieve the current user's profile",
        responses={
            200: openapi.Response(
                description="Profile retrieved successfully",
                schema=ProfileSerializer
            ),
            401: openapi.Response(description="Unauthorized"),
            404: openapi.Response(description="Profile not found"),
            500: openapi.Response(description="Internal Server Error")
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
        tags=['Profile'],
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
    @swagger_auto_schema(
        tags=['Profile'],
        operation_summary="Get Profile Choices",
        operation_description="Retrieve available choices for profile fields (countries, languages, physical attributes, etc.)",
        responses={
            200: openapi.Response(
                description="Choices retrieved successfully",
                schema=openapi.Schema(type=openapi.TYPE_OBJECT)
            )
        }
    )
    def get(self, request):
        data_dir = os.path.join(settings.BASE_DIR, 'userprofile', 'data')
        response_data = {}
        
        # Load countries
        with open(os.path.join(data_dir, 'countries.json'), 'r') as f:
            response_data['countries'] = json.load(f)['countries']
        
        # Load languages
        with open(os.path.join(data_dir, 'languages.json'), 'r') as f:
            response_data['languages'] = json.load(f)['languages']
        
        # Load physical attributes
        with open(os.path.join(data_dir, 'physical_attributes.json'), 'r') as f:
            physical_data = json.load(f)
            response_data.update({
                'hair_colors': physical_data['hair_colors'],
                'eye_colors': physical_data['eye_colors'],
                'skin_tones': physical_data['skin_tones'],
                'body_types': physical_data['body_types'],
                'genders': physical_data['genders']
            })
        
        # Load personal info
        with open(os.path.join(data_dir, 'personal_info.json'), 'r') as f:
            personal_data = json.load(f)
            response_data.update({
                'marital_statuses': personal_data['marital_statuses'],
                'hobbies': personal_data['hobbies'],
                'medical_conditions': personal_data['medical_conditions'],
                'medicine_types': personal_data['medicine_types']
            })

        # Load nationalities
        with open(os.path.join(data_dir, 'nationalities.json'), 'r') as f:
            response_data['nationalities'] = json.load(f)['nationalities']

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

        # Load medical info
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

        # Load locations
        with open(os.path.join(data_dir, 'locations.json'), 'r') as f:
            location_data = json.load(f)
            response_data.update({
                'regions': location_data['regions'],
                'cities': location_data['cities']
            })
        
        return Response(response_data)
