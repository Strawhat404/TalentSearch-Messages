from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample, OpenApiTypes
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from .models import Profile
from .serializers import ProfileSerializer

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
