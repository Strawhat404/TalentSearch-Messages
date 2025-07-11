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
from django.shortcuts import get_object_or_404
from rest_framework.generics import RetrieveUpdateDestroyAPIView
from rest_framework.generics import ListAPIView

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

class FeedPostDetailView(RetrieveUpdateDestroyAPIView):
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

class FeedLikeToggleView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, post_id):
        """Check if current user has liked this post"""
        try:
            post = FeedPost.objects.get(id=post_id)
            user_profile = request.user.profile
            has_liked = FeedLike.objects.filter(post=post, profile=user_profile).exists()
            
            return Response({
                'has_liked': has_liked,
                'likes_count': post.likes.count()
            })
        except FeedPost.DoesNotExist:
            return Response({'error': 'Post not found'}, status=404)

    def post(self, request, post_id):
        """Toggle like/unlike for a post"""
        try:
            post = FeedPost.objects.get(id=post_id)
            user_profile = request.user.profile
            
            # Check if user already liked this post
            existing_like = FeedLike.objects.filter(post=post, profile=user_profile).first()
            
            if existing_like:
                # Unlike: delete the existing like
                existing_like.delete()
                action = 'unliked'
            else:
                # Like: create a new like
                FeedLike.objects.create(post=post, profile=user_profile)
                action = 'liked'
            
            return Response({
                'action': action,
                'has_liked': not existing_like,  # True if we just liked, False if we just unliked
                'likes_count': post.likes.count()
            })
            
        except FeedPost.DoesNotExist:
            return Response({'error': 'Post not found'}, status=404)
        except Exception as e:
            return Response({'error': str(e)}, status=500)

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
            return CommentCreateSerializer  # For input/validation
        return CommentSerializer  # For GET/list

    def perform_create(self, serializer):
        post_id = self.kwargs['post_id']
        serializer.save(profile=self.request.user.profile, post_id=post_id)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        # Use CommentSerializer for output
        full_serializer = CommentSerializer(serializer.instance, context={'request': request})
        headers = self.get_success_headers(serializer.data)
        return Response(full_serializer.data, status=201, headers=headers)

class CommentReplyCreateView(generics.CreateAPIView):
    serializer_class = ReplyCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_summary='Reply to a comment',
        operation_description='Create a reply to a specific comment by parent_id',
        request_body=ReplyCreateSerializer,
        responses={201: CommentSerializer()}
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def perform_create(self, serializer):
        parent_id = self.kwargs.get('parent_id')
        parent = Comment.objects.get(id=parent_id)
        serializer.save(profile=self.request.user.profile, parent=parent, post=parent.post)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        # Use CommentSerializer for output
        full_serializer = CommentSerializer(serializer.instance, context={'request': request})
        headers = self.get_success_headers(serializer.data)
        return Response(full_serializer.data, status=201, headers=headers)

class CommentLikeCreateView(generics.CreateAPIView):
    serializer_class = CommentLikeSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary='Like or unlike a comment',
        operation_description='Toggle like/unlike for a comment by comment_id. If already liked, it will unlike; if not liked, it will like.',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'is_like': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Like (true) or unlike (false)', default=True)
            }
        ),
        responses={
            200: openapi.Response(
                description="Comment like toggled successfully.",
                schema=CommentLikeSerializer()
            ),
            201: openapi.Response(
                description="Comment liked successfully.",
                schema=CommentLikeSerializer()
            ),
            400: openapi.Response(description="Validation Error"),
            401: openapi.Response(description="Authentication Required")
        }
    )
    def post(self, request, *args, **kwargs):
        comment_id = self.kwargs['comment_id']
        profile = self.request.user.profile
        is_like = request.data.get('is_like', True)

        # Try to find an existing like
        existing_like = CommentLike.objects.filter(comment_id=comment_id, profile=profile).first()

        if existing_like:
            # If is_like is False or user wants to unlike, delete the like
            if not is_like:
                existing_like.delete()
                return Response({'message': 'Comment unliked successfully.'}, status=status.HTTP_200_OK)
            else:
                return Response({'message': 'Comment already liked.'}, status=status.HTTP_200_OK)
        else:
            # If is_like is True or not provided, create a like
            if is_like:
                serializer = self.get_serializer(data={'comment': comment_id, 'is_like': True})
                serializer.is_valid(raise_exception=True)
                serializer.save(profile=profile)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response({'message': 'Comment is not liked yet.'}, status=status.HTTP_400_BAD_REQUEST)

class CommentDeleteView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Comment.objects.all()
    lookup_field = 'id'

    @swagger_auto_schema(
        operation_summary='Delete a comment or reply',
        operation_description='Delete a comment or reply by its ID (only the author can delete).',
        responses={
            204: openapi.Response(
                description="Comment deleted successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING, example='Comment deleted successfully')
                    }
                )
            ),
            404: openapi.Response(
                description="Comment not found or not authorized",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(type=openapi.TYPE_STRING, example='Not found.')
                    }
                )
            ),
        }
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)

    def get_object(self):
        comment_id = self.kwargs['id']
        user_profile = self.request.user.profile
        
        # Only allow user to delete their own comments
        return get_object_or_404(
            Comment, 
            id=comment_id, 
            profile=user_profile
        )

    def destroy(self, request, *args, **kwargs):
        comment = self.get_object()
        comment.delete()
        return Response({
            'message': 'Comment deleted successfully'
        }, status=204)

class ProfileFollowCountsView(APIView):
    def get(self, request, profile_id):
        profile = Profile.objects.get(id=profile_id)
        follower_count = profile.followers.count()
        following_count = profile.following.count()
        return Response({
            "follower_count": follower_count,
            "following_count": following_count
        })

class CommentRepliesListView(generics.ListAPIView):
    serializer_class = CommentSerializer
    permission_classes = [permissions.AllowAny]  # or IsAuthenticated if needed

    @swagger_auto_schema(
        operation_summary='List replies to a comment',
        operation_description='Get all replies for a specific comment by parent_id',
        responses={200: CommentSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        """List replies to a comment"""
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        parent_id = self.kwargs['parent_id']
        return Comment.objects.filter(parent_id=parent_id).order_by('created_at')

class CommentLikeListView(generics.ListAPIView):
    serializer_class = CommentLikeSerializer
    permission_classes = [permissions.AllowAny]  # or IsAuthenticated if you want

    @swagger_auto_schema(
        operation_summary='List likes for a comment',
        operation_description='Get all likes for a specific comment by comment_id',
        responses={200: CommentLikeSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        comment_id = self.kwargs['comment_id']
        return CommentLike.objects.filter(comment_id=comment_id)
