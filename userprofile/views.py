from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample, OpenApiTypes
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from .models import Profile, VerificationStatus, VerificationAuditLog
from .serializers import ProfileSerializer, VerificationStatusSerializer, VerificationAuditLogSerializer
import os
import json
from django.conf import settings

class ProfileView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    @extend_schema(
        tags=['profile'],
        summary="Create user profile",
        description="Create a new user profile with required and optional fields.",
        request={
            'multipart/form-data': {
                'type': 'object',
                'properties': {
                    'name': {'type': 'string', 'description': 'User\'s full name', 'example': 'John Doe'},
                    'profession': {'type': 'string', 'description': 'User\'s profession',
                                   'example': 'Software Engineer'},
                    'photo': {'type': 'string', 'format': 'binary',
                              'description': 'Profile photo (jpg, jpeg, png, gif, max 5MB)'},
                    'video': {'type': 'string', 'format': 'binary',
                              'description': 'Profile video (mp4, avi, mov, mkv, max 50MB)'},
                    'birthdate': {'type': 'string', 'format': 'date', 'description': 'Date of birth (YYYY-MM-DD)',
                                  'example': '1990-01-01'},
                    'location': {'type': 'string', 'description': 'Current location', 'example': 'Addis Ababa'},
                    'gender': {'type': 'string', 'description': 'Gender', 'example': 'Male'},
                    'nationality': {'type': 'string', 'description': 'Nationality', 'example': 'Ethiopian'},
                    'education_level': {'type': 'string', 'description': 'Highest education level',
                                        'example': "Bachelor's"},
                    'experience_level': {'type': 'string', 'description': 'Professional experience level',
                                         'example': 'Senior'},
                    'skills': {'type': 'array', 'items': {'type': 'string'}, 'description': 'List of skills',
                               'example': ['Python', 'Django']},
                    'languages': {'type': 'array', 'items': {'type': 'string'}, 'description': 'List of languages',
                                  'example': ['English', 'Amharic']},
                    'min_salary': {'type': 'integer', 'description': 'Minimum expected salary', 'example': 50000},
                    'max_salary': {'type': 'integer', 'description': 'Maximum expected salary', 'example': 100000},
                    'identity_verification[id_type]': {'type': 'string',
                                                       'enum': ['national_id', 'passport', 'drivers_license',
                                                                'kebele_id'], 'description': 'Type of ID',
                                                       'example': 'national_id'},
                    'identity_verification[id_number]': {'type': 'string', 'description': 'ID number',
                                                         'example': '123456789012'},
                    'identity_verification[id_expiry_date]': {'type': 'string', 'format': 'date',
                                                              'description': 'ID expiration date',
                                                              'example': '2030-01-01'},
                    'identity_verification[id_front]': {'type': 'string', 'format': 'binary',
                                                        'description': 'Front side of ID (max 5MB)'},
                    'identity_verification[id_back]': {'type': 'string', 'format': 'binary',
                                                       'description': 'Back side of ID (max 5MB)'},
                    'emergency_contact': {'type': 'string', 'description': 'Emergency contact name',
                                          'example': 'Jane Doe'},
                    'emergency_phone': {'type': 'string', 'description': 'Emergency contact phone',
                                        'example': '+251911223344'},
                    'social_media_links': {'type': 'object', 'description': 'Social media URLs',
                                           'example': {'twitter': 'https://twitter.com/johndoe'}},
                    'preferred_work_location': {'type': 'string', 'description': 'Preferred work location',
                                                'example': 'Remote'},
                    'shift_preference': {'type': 'string', 'description': 'Preferred work shift', 'example': 'Day'},
                    'willingness_to_relocate': {'type': 'string', 'description': 'Willingness to relocate',
                                                'example': 'Yes'},
                    'overtime_availability': {'type': 'string', 'description': 'Overtime availability',
                                              'example': 'Yes'},
                    'travel_willingness': {'type': 'string', 'description': 'Willingness to travel', 'example': 'Yes'},
                },
                'required': ['name', 'profession']
            }
        },
        responses={
            201: ProfileSerializer,
            400: OpenApiTypes.OBJECT,
            401: OpenApiTypes.OBJECT,
        },
        examples=[
            OpenApiExample(
                'Success Response',
                value={
                    'id': 1,
                    'name': 'John Doe',
                    'email': 'john@example.com',
                    'profession': 'Software Engineer',
                    'location': 'Addis Ababa',
                    'photo': 'http://example.com/media/profile_photos/john.jpg',
                    'created_at': '2024-03-20T10:00:00Z',
                    'verified': False
                },
                status_codes=['201']
            ),
            OpenApiExample(
                'Validation Error',
                value={
                    'name': ['This field is required.'],
                    'profession': ['This field is required.'],
                    'photo': ['File size must not exceed 5MB.'],
                    'identity_verification[id_number]': ['Invalid ID number format for the selected ID type.']
                },
                status_codes=['400']
            ),
            OpenApiExample(
                'Unauthorized',
                value={'detail': 'Authentication credentials were not provided.'},
                status_codes=['401']
            )
        ]
    )
    def get(self, request):
        try:
            profile = Profile.objects.get(user=request.user)
            serializer = ProfileSerializer(profile)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Profile.DoesNotExist:
            return Response({"message": "Profile not found."}, status=status.HTTP_404_NOT_FOUND)

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

class ChoiceDataView(APIView):
    """
    View to serve choice data for various fields
    """
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
        
        return Response(response_data)
