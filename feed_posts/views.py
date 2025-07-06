from rest_framework import generics, status, serializers
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from .models import FeedPost, UserFollow
from .serializers import FeedPostSerializer, UserFollowSerializer
from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import os
import logging
from authapp.services import notify_new_feed_posted
from userprofile.models import Profile

logger = logging.getLogger(__name__)

class FeedPostListView(generics.ListCreateAPIView):
    serializer_class = FeedPostSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        try:
            queryset = FeedPost.objects.all().order_by('-created_at')
            
            # Filter by profile_id
            profile_id = self.request.query_params.get('profile_id')
            if profile_id:
                queryset = queryset.filter(profile=profile_id)
            
            # Filter by project_type
            project_type = self.request.query_params.get('project_type')
            if project_type:
                queryset = queryset.filter(project_type=project_type)
            
            # Handle pagination range
            range_header = self.request.headers.get('Range')
            if range_header:
                try:
                    start, end = map(int, range_header.split('-'))
                    queryset = queryset[start:end+1]
                except (ValueError, TypeError):
                    pass
            
            return queryset
        except Exception as e:
            logger.error(f"Error in FeedPostListView.get_queryset: {e}")
            return FeedPost.objects.none()

    @swagger_auto_schema(
        operation_summary='List feed posts',
        operation_description='Get all feed posts with optional filtering',
        responses={
            200: FeedPostSerializer(many=True),
            400: openapi.Response(description="Validation Error")
        }
    )
    def get(self, request, *args, **kwargs):
        try:
            return super().get(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error in FeedPostListView.get: {e}")
            return Response(
                {"error": "An error occurred while fetching feed posts"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_summary='Create feed post',
        operation_description='Create a new feed post',
        request_body=FeedPostSerializer,
        responses={
            201: openapi.Response(
                description="Post created successfully.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'id': openapi.Schema(type=openapi.TYPE_STRING, example='uuid'),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, example='Post created successfully')
                    }
                )
            ),
            400: openapi.Response(description="Validation Error")
        }
    )
    def post(self, request, *args, **kwargs):
        profile_id = request.data.get('profile_id')
        if not profile_id:
            return Response({'error': 'profile_id is required'}, status=400)
        try:
            user_profile = Profile.objects.get(id=profile_id)
            feed_post = self.get_serializer(data=request.data).save(profile=user_profile)
            # Trigger notification for new feed post
            notify_new_feed_posted(feed_post)
            return Response({
                "id": feed_post.id,
                "message": "Post created successfully"
            }, status=status.HTTP_201_CREATED)
        except Profile.DoesNotExist:
            return Response({'error': 'Profile not found'}, status=404)
        except Exception as e:
            raise serializers.ValidationError(f"User profile not found: {str(e)}")

class FeedPostDetailView(generics.RetrieveDestroyAPIView):
    queryset = FeedPost.objects.all()
    serializer_class = FeedPostSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    @swagger_auto_schema(
        operation_summary='Get feed post by ID',
        operation_description='Get a specific feed post by its ID',
        responses={
            200: FeedPostSerializer(),
            404: openapi.Response(description="Not Found")
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary='Delete feed post',
        operation_description='Delete a specific feed post by its ID',
        responses={
            200: openapi.Response(
                description="Post deleted successfully.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING, example='Post deleted successfully')
                    }
                )
            ),
            404: openapi.Response(description="Not Found")
        }
    )
    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({
            "message": "Post deleted successfully"
        }, status=status.HTTP_200_OK)

class FeedPostMediaView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, post_id):
        try:
            return FeedPost.objects.get(id=post_id)
        except FeedPost.DoesNotExist:
            return None

    @swagger_auto_schema(
        operation_summary='Delete media from post',
        operation_description='Delete only the media file from a post while keeping the post itself',
        responses={
            200: openapi.Response(
                description="Media deleted successfully.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING, example='Media deleted successfully')
                    }
                )
            ),
            404: openapi.Response(description="Not Found")
        }
    )
    def delete(self, request, *args, **kwargs):
        post_id = kwargs.get('id')
        instance = self.get_object(post_id)
        if not instance:
            return Response({
                "error": "Post not found"
            }, status=status.HTTP_404_NOT_FOUND)

        if instance.media_url:
            try:
                # Delete the file from storage
                if os.path.isfile(instance.media_url.path):
                    os.remove(instance.media_url.path)
                # Clear the media_url field
                instance.media_url = None
                instance.save()
                return Response({
                    "message": "Media deleted successfully"
                }, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({
                    "error": f"Error deleting media: {str(e)}"
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response({
            "message": "No media to delete"
        }, status=status.HTTP_200_OK)

class FollowUserView(APIView):
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary='Follow a profile',
        operation_description='Follow another profile by providing their profile ID',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['following_id'],
            properties={
                'profile_id': openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description='ID of the profile to follow',
                    example=1
                ),
                'following_id': openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description='ID of the profile to follow',
                    example=1
                )
            }
        ),
        responses={
            201: openapi.Response(
                description="Profile followed successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example='Followed successfully.'
                        )
                    }
                )
            ),
            400: openapi.Response(
                description="Bad Request",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example='profile_id and following_id are required'
                        )
                    }
                )
            ),
            401: openapi.Response(description="Unauthorized")
        },
        tags=['follow']
    )
    def post(self, request, *args, **kwargs):
        profile_id = request.data.get('profile_id')
        following_id = request.data.get('following_id')
        if not profile_id or not following_id:
            return Response({'error': 'profile_id and following_id are required'}, status=400)
        try:
            follower = Profile.objects.get(id=profile_id)
            following = Profile.objects.get(id=following_id)
        except Profile.DoesNotExist:
            return Response({'error': 'Profile not found'}, status=404)
        
        # Check if already following
        if UserFollow.objects.filter(follower=follower, following=following).exists():
            return Response({
                'error': 'Already following this profile'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create follow relationship
        UserFollow.objects.create(follower=follower, following=following)
        
        return Response({
            'message': 'Followed successfully.'
        }, status=status.HTTP_201_CREATED)

class UnfollowUserView(APIView):
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary='Unfollow a profile',
        operation_description='Unfollow another profile by providing their profile ID',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['following_id'],
            properties={
                'profile_id': openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description='ID of the profile to unfollow',
                    example=1
                ),
                'following_id': openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description='ID of the profile to unfollow',
                    example=1
                )
            }
        ),
        responses={
            200: openapi.Response(
                description="Profile unfollowed successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example='Unfollowed successfully.'
                        )
                    }
                )
            ),
            400: openapi.Response(
                description="Bad Request",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example='profile_id and following_id are required'
                        )
                    }
                )
            ),
            401: openapi.Response(description="Unauthorized")
        },
        tags=['follow']
    )
    def delete(self, request, *args, **kwargs):
        try:
            profile_id = request.data.get('profile_id')
            following_id = request.data.get('following_id')
            if not profile_id or not following_id:
                return Response({'error': 'profile_id and following_id are required'}, status=400)
            user_profile = Profile.objects.get(id=profile_id)
            following_profile = Profile.objects.get(id=following_id)

            follow_relationship = UserFollow.objects.filter(
                follower=user_profile, 
                following=following_profile
            ).first()

            if not follow_relationship:
                return Response({
                    'error': 'Not following this profile'
                }, status=status.HTTP_400_BAD_REQUEST)

            follow_relationship.delete()
            return Response({
                'message': 'Unfollowed successfully.'
            }, status=status.HTTP_200_OK)

        except Profile.DoesNotExist:
            return Response({
                'error': 'Profile not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'error': f'Error unfollowing profile: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            

class FollowersListView(APIView):
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary='Get profile followers',
        operation_description='Get list of profiles who are following the specified profile (or current profile if no profile_id provided)',
        manual_parameters=[
            openapi.Parameter(
                'profile_id',
                openapi.IN_QUERY,
                description='ID of the profile whose followers to get (optional, defaults to current profile)',
                type=openapi.TYPE_INTEGER,
                required=False,
                example=1
            )
        ],
        responses={
            200: UserFollowSerializer(many=True),
            401: openapi.Response(description="Unauthorized")
        },
        tags=['follow']
    )
    def get(self, request, *args, **kwargs):
        try:
            # Get the target profile (current user's profile by default)
            profile_id = request.query_params.get('profile_id')
            if profile_id:
                target_profile = Profile.objects.get(id=profile_id)
            else:
                target_profile = request.user.profile
            
            # Get followers
            followers = UserFollow.objects.filter(following=target_profile).select_related('follower')
            
            serializer = UserFollowSerializer(followers, many=True)
            return Response(serializer.data)
            
        except Exception as e:
            return Response({
                'error': f'Error getting followers: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class FollowingListView(APIView):
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary='Get profiles being followed',
        operation_description='Get list of profiles that the specified profile is following (or current profile if no profile_id provided)',
        manual_parameters=[
            openapi.Parameter(
                'profile_id',
                openapi.IN_QUERY,
                description='ID of the profile whose following list to get (optional, defaults to current profile)',
                type=openapi.TYPE_INTEGER,
                required=False,
                example=1
            )
        ],
        responses={
            200: UserFollowSerializer(many=True),
            401: openapi.Response(description="Unauthorized")
        },
        tags=['follow']
    )
    def get(self, request, *args, **kwargs):
        try:
            # Get the target profile (current user's profile by default)
            profile_id = request.query_params.get('profile_id')
            if profile_id:
                target_profile = Profile.objects.get(id=profile_id)
            else:
                target_profile = request.user.profile
            
            # Get following
            following = UserFollow.objects.filter(follower=target_profile).select_related('following')
            
            serializer = UserFollowSerializer(following, many=True)
            return Response(serializer.data)
            
        except Exception as e:
            return Response({
                'error': f'Error getting following: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 
    