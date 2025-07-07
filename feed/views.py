from django.shortcuts import render
from rest_framework import viewsets, permissions, generics
from .models import FeedPost
from .serializers import FeedPostSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
import os
from userprofile.models import Profile
from .models import Follow
from .serializers import FollowSerializer
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from .models import FeedLike
from .serializers import FeedLikeSerializer
from .models import Comment
from .serializers import CommentSerializer, CommentCreateSerializer
from .models import CommentLike
from .serializers import CommentLikeSerializer, ReplyCreateSerializer

# Create your views here.

class FeedPostViewSet(viewsets.ModelViewSet):
    queryset = FeedPost.objects.all().order_by('-created_at')
    serializer_class = FeedPostSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class FeedPostListView(generics.ListCreateAPIView):
    serializer_class = FeedPostSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = FeedPost.objects.all().order_by('-created_at')
        profile_id = self.request.query_params.get('profile_id')
        if profile_id:
            queryset = queryset.filter(profile_id=profile_id)
        return queryset

    def perform_create(self, serializer):
        # This sets the profile automatically from the logged-in user
        serializer.save(profile=self.request.user.profile)

class FeedPostDetailView(generics.RetrieveDestroyAPIView):
    queryset = FeedPost.objects.all()
    serializer_class = FeedPostSerializer
    lookup_field = 'id'

class FeedPostMediaView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        post_id = kwargs.get('id')
        try:
            post = FeedPost.objects.get(id=post_id)
        except FeedPost.DoesNotExist:
            return Response({"error": "Post not found"}, status=status.HTTP_404_NOT_FOUND)

        if post.media_url:
            try:
                if os.path.isfile(post.media_url.path):
                    os.remove(post.media_url.path)
                post.media_url = None
                post.save()
                return Response({"message": "Media deleted successfully"}, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({"error": f"Error deleting media: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response({"message": "No media to delete"}, status=status.HTTP_200_OK)

class FollowUserView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary='Follow a profile',
        operation_description='Follow another profile by providing their profile ID',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['profile_id', 'following_id'],
            properties={
                'profile_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the follower'),
                'following_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the profile to follow'),
            }
        ),
        responses={
            201: openapi.Response(
                description="Profile followed successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING, example='Followed successfully.')
                    }
                )
            ),
            400: openapi.Response(
                description="Bad Request",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(type=openapi.TYPE_STRING, example='Already following this profile')
                    }
                )
            ),
            404: openapi.Response(
                description="Not Found",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(type=openapi.TYPE_STRING, example='Profile not found')
                    }
                )
            ),
        }
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
        if Follow.objects.filter(follower=follower, following=following).exists():
            return Response({
                'error': 'Already following this profile'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create follow relationship
        Follow.objects.create(follower=follower, following=following)
        
        return Response({
            'message': 'Followed successfully.'
        }, status=status.HTTP_201_CREATED)

class UnfollowUserView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        profile_id = request.data.get('profile_id')
        following_id = request.data.get('following_id')
        if not profile_id or not following_id:
            return Response({'error': 'profile_id and following_id are required'}, status=400)
        try:
            user_profile = Profile.objects.get(id=profile_id)
            following_profile = Profile.objects.get(id=following_id)
        except Profile.DoesNotExist:
            return Response({'error': 'Profile not found'}, status=404)

        follow_relationship = Follow.objects.filter(
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

class FollowersListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            # Get profile_id from query params and clean it
            profile_id = request.query_params.get('profile_id')
            
            if profile_id:
                # Clean the profile_id (remove trailing slash, etc.)
                profile_id = str(profile_id).strip().rstrip('/')
                
                # Validate it's a valid integer
                if not profile_id.isdigit():
                    return Response(
                        {"error": "Invalid profile_id. Must be a number."}, 
                        status=400
                    )
                
                # Get the target profile
                target_profile = Profile.objects.get(id=int(profile_id))
            else:
                # If no profile_id provided, use current user's profile
                target_profile = request.user.profile
            
            # Get followers
            followers = Follow.objects.filter(following=target_profile)
            serializer = FollowSerializer(followers, many=True)
            
            return Response(serializer.data)
            
        except Profile.DoesNotExist:
            return Response(
                {"error": "Profile not found"}, 
                status=404
            )
        except Exception as e:
            return Response(
                {"error": f"An error occurred: {str(e)}"}, 
                status=500
            )

class FollowingListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            # Get profile_id from query params and clean it
            profile_id = request.query_params.get('profile_id')
            
            if profile_id:
                # Clean the profile_id (remove trailing slash, etc.)
                profile_id = str(profile_id).strip().rstrip('/')
                
                # Validate it's a valid integer
                if not profile_id.isdigit():
                    return Response(
                        {"error": "Invalid profile_id. Must be a number."}, 
                        status=400
                    )
                
                # Get the target profile
                target_profile = Profile.objects.get(id=int(profile_id))
            else:
                # If no profile_id provided, use current user's profile
                target_profile = request.user.profile
            
            # Get following
            following = Follow.objects.filter(follower=target_profile)
            serializer = FollowSerializer(following, many=True)
            
            return Response(serializer.data)
            
        except Profile.DoesNotExist:
            return Response(
                {"error": "Profile not found"}, 
                status=404
            )
        except Exception as e:
            return Response(
                {"error": f"An error occurred: {str(e)}"}, 
                status=500
            )

class FeedLikeCreateView(generics.CreateAPIView):
    serializer_class = FeedLikeSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        post_id = self.kwargs['post_id']
        serializer.save(profile=self.request.user.profile, post_id=post_id)

class FeedLikeDeleteView(generics.DestroyAPIView):
    queryset = FeedLike.objects.all()
    serializer_class = FeedLikeSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'

# class CommentListCreateView(generics.ListCreateAPIView):
#     serializer_class = CommentCreateSerializer
#     permission_classes = [IsAuthenticated]

#     def get_queryset(self):
#         post_id = self.kwargs['post_id']
#         return Comment.objects.filter(post_id=post_id, parent=None).order_by('-created_at')

#     def perform_create(self, serializer):
#         post_id = self.kwargs['post_id']
#         serializer.save(profile=self.request.user.profile, post_id=post_id)

class CommentListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        post_id = self.kwargs['post_id']
        return Comment.objects.filter(post_id=post_id, parent=None).order_by('-created_at')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CommentCreateSerializer
        return CommentSerializer

    def perform_create(self, serializer):
        post_id = self.kwargs['post_id']
        serializer.save(profile=self.request.user.profile, post_id=post_id)

class CommentReplyCreateView(generics.CreateAPIView):
    serializer_class = ReplyCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        parent_id = self.kwargs.get('parent_id')
        parent = Comment.objects.get(id=parent_id)
        serializer.save(profile=self.request.user.profile, parent=parent, post=parent.post)

class CommentLikeCreateView(generics.CreateAPIView):
    serializer_class = CommentLikeSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        comment_id = self.kwargs['comment_id']
        serializer.save(profile=self.request.user.profile, comment_id=comment_id)

class ProfileFollowCountsView(APIView):
    def get(self, request, profile_id):
        profile = Profile.objects.get(id=profile_id)
        follower_count = profile.followers.count()
        following_count = profile.following.count()
        return Response({
            "follower_count": follower_count,
            "following_count": following_count
        })
