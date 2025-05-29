from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from .models import Profile, VerificationStatus, VerificationAuditLog
from .serializers import ProfileSerializer, VerificationStatusSerializer, VerificationAuditLogSerializer

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
                        "professional_qualifications": {
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
                        "professional_qualifications": {
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
        description="Update the authenticated user's profile.",
        request_body=ProfileSerializer,
        responses={
            200: openapi.Response(
                description="Profile updated successfully",
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
                        "professional_qualifications": {
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
            404: openapi.Response(description="Profile not found"),
        }
    )
    def put(self, request):
        try:
            profile = Profile.objects.get(user=request.user)
            serializer = ProfileSerializer(profile, data=request.data, partial=True)
            if serializer.is_valid():
                updated_profile = serializer.save()
                response_data = {
                    "id": updated_profile.id,
                    "message": "Profile updated successfully."
                }
                return Response(response_data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Profile.DoesNotExist:
            return Response({"message": "Profile not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
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

    @extend_schema(
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
            200: OpenApiTypes.OBJECT,
            400: OpenApiTypes.OBJECT,
            401: OpenApiTypes.OBJECT,
            403: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
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

    @extend_schema(
        tags=['verification'],
        summary="Get verification audit logs",
        description="Get the audit logs for profile verifications.",
        responses={
            200: OpenApiTypes.OBJECT,
            401: OpenApiTypes.OBJECT,
            403: OpenApiTypes.OBJECT,
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
