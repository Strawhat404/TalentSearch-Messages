from rest_framework import generics, status
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

logger = logging.getLogger(__name__)

class FeedPostListView(generics.ListCreateAPIView):
    serializer_class = FeedPostSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        try:
            queryset = FeedPost.objects.all().order_by('-created_at')
            
            # Filter by user_id
            user_id = self.request.query_params.get('user_id')
            if user_id:
                queryset = queryset.filter(user_id=user_id)
            
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
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response({
            "id": serializer.data['id'],
            "message": "Post created successfully"
        }, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        feed_post = serializer.save(user=self.request.user)
        # Trigger notification for new feed post
        notify_new_feed_posted(feed_post)
        return feed_post

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
        operation_summary='Follow a user',
        operation_description='Follow another user by providing their user ID',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['following_id'],
            properties={
                'following_id': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_UUID,
                    description='ID of the user to follow',
                    example='123e4567-e89b-12d3-a456-426614174000'
                )
            }
        ),
        responses={
            201: openapi.Response(
                description="User followed successfully",
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
                            example='following_id is required'
                        )
                    }
                )
            ),
            401: openapi.Response(description="Unauthorized")
        },
        tags=['follow']
    )
    def post(self, request, *args, **kwargs):
        following_id = request.data.get('following_id')
        if not following_id:
            return Response({'error': 'following_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        if str(request.user.id) == str(following_id):
            return Response({'error': 'You cannot follow yourself.'}, status=status.HTTP_400_BAD_REQUEST)
        follow, created = UserFollow.objects.get_or_create(follower=request.user, following_id=following_id)
        if not created:
            return Response({'error': 'Already following.'}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'message': 'Followed successfully.'}, status=status.HTTP_201_CREATED)

class UnfollowUserView(APIView):
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary='Unfollow a user',
        operation_description='Unfollow another user by providing their user ID',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['following_id'],
            properties={
                'following_id': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_UUID,
                    description='ID of the user to unfollow',
                    example='123e4567-e89b-12d3-a456-426614174000'
                )
            }
        ),
        responses={
            200: openapi.Response(
                description="User unfollowed successfully",
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
                            example='following_id is required'
                        )
                    }
                )
            ),
            401: openapi.Response(description="Unauthorized")
        },
        tags=['follow']
    )
    def delete(self, request, *args, **kwargs):
        following_id = request.data.get('following_id')
        if not following_id:
            return Response({'error': 'following_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        deleted, _ = UserFollow.objects.filter(follower=request.user, following_id=following_id).delete()
        if deleted:
            return Response({'message': 'Unfollowed successfully.'}, status=status.HTTP_200_OK)
        return Response({'error': 'Not following.'}, status=status.HTTP_400_BAD_REQUEST)

class FollowersListView(APIView):
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary='Get user followers',
        operation_description='Get list of users who are following the specified user (or current user if no user_id provided)',
        manual_parameters=[
            openapi.Parameter(
                'user_id',
                openapi.IN_QUERY,
                description='ID of the user whose followers to get (optional, defaults to current user)',
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_UUID,
                required=False,
                example='123e4567-e89b-12d3-a456-426614174000'
            )
        ],
        responses={
            200: UserFollowSerializer(many=True),
            401: openapi.Response(description="Unauthorized")
        },
        tags=['follow']
    )
    def get(self, request, *args, **kwargs):
        user_id = request.query_params.get('user_id', request.user.id)
        followers = UserFollow.objects.filter(following_id=user_id)
        serializer = UserFollowSerializer(followers, many=True)
        return Response(serializer.data)

class FollowingListView(APIView):
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary='Get users being followed',
        operation_description='Get list of users that the specified user is following (or current user if no user_id provided)',
        manual_parameters=[
            openapi.Parameter(
                'user_id',
                openapi.IN_QUERY,
                description='ID of the user whose following list to get (optional, defaults to current user)',
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_UUID,
                required=False,
                example='123e4567-e89b-12d3-a456-426614174000'
            )
        ],
        responses={
            200: UserFollowSerializer(many=True),
            401: openapi.Response(description="Unauthorized")
        },
        tags=['follow']
    )
    def get(self, request, *args, **kwargs):
        user_id = request.query_params.get('user_id', request.user.id)
        following = UserFollow.objects.filter(follower_id=user_id)
        serializer = UserFollowSerializer(following, many=True)
        return Response(serializer.data) 