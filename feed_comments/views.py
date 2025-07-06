from django.shortcuts import render
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q, Count
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import Comment, CommentLike
from .serializers import (
    CommentSerializer,
    CommentCreateSerializer,
    CommentLikeSerializer,
    ReplyCreateSerializer,
    ReplySerializer
)

# Create your views here.

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of a comment to edit it.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True
        # Write permissions are only allowed to the owner
        try:
            return obj.profile == request.user.profile
        except:
            return False

class CommentViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    serializer_class = CommentSerializer
    pagination_class = PageNumberPagination
    queryset = Comment.objects.select_related(
        'profile',
        'profile__user',
        'post',
        'parent'
    ).prefetch_related(
        'replies',
        'replies__profile',
        'replies__profile__user',
        'likes'
    )

    def get_queryset(self):
        queryset = super().get_queryset()
        post_id = self.request.query_params.get('post_id')
        parent_id = self.request.query_params.get('parent_id')

        if post_id:
            queryset = queryset.filter(post_id=post_id)
        if parent_id:
            queryset = queryset.filter(parent_id=parent_id)
        else:
            # By default, only show top-level comments
            queryset = queryset.filter(parent__isnull=True)

        return queryset

    def get_serializer_class(self):
        if self.action == 'create':
            return CommentCreateSerializer
        return CommentSerializer

    def perform_create(self, serializer):
        # Get the user's profile
        try:
            user_profile = self.request.user.profile
            serializer.save(profile=user_profile)
        except Exception as e:
            raise serializers.ValidationError(f"User profile not found: {str(e)}")

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'post_id', openapi.IN_QUERY, description='Filter comments by post ID', type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'parent_id', openapi.IN_QUERY, description='Filter replies by parent comment ID', type=openapi.TYPE_STRING
            ),
        ],
        responses={200: CommentSerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        request_body=CommentCreateSerializer,
        responses={201: CommentSerializer}
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        request_body=CommentLikeSerializer,
        responses={200: CommentSerializer}
    )
    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        comment = self.get_object()
        is_like = request.data.get('is_like', True)
        
        # Get the user's profile
        try:
            user_profile = request.user.profile
        except:
            return Response(
                {"error": "User profile not found"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get or create the like object
        like, created = CommentLike.objects.get_or_create(
            comment=comment,
            profile=user_profile,
            defaults={'is_like': is_like}
        )
        
        # Refresh the comment from database to get latest counts
        comment.refresh_from_db()
        
        if not created:
            if like.is_like == is_like:
                # If clicking the same button, remove the like/dislike
                like.delete()
                if is_like:
                    comment.likes_count = max(0, comment.likes_count - 1)
                else:
                    comment.dislikes_count = max(0, comment.dislikes_count - 1)
            else:
                # If switching from like to dislike or vice versa
                like.is_like = is_like
                like.save()
                if is_like:
                    comment.likes_count += 1
                    comment.dislikes_count = max(0, comment.dislikes_count - 1)
                else:
                    comment.dislikes_count += 1
                    comment.likes_count = max(0, comment.likes_count - 1)
        else:
            # New like/dislike
            if is_like:
                comment.likes_count += 1
            else:
                comment.dislikes_count += 1
        
        comment.save()
        # Refresh from database to ensure we have the latest counts
        comment.refresh_from_db()
        return Response(self.get_serializer(comment).data)

    @action(detail=True, methods=['get'])
    def replies(self, request, pk=None):
        comment = self.get_object()
        replies = comment.replies.all()
        serializer = self.get_serializer(replies, many=True)
        return Response(serializer.data)

    # 🆕 COOL NEW REPLY ENDPOINTS
    
    @swagger_auto_schema(
        request_body=ReplyCreateSerializer,
        responses={201: ReplySerializer},
        operation_description="Create a reply to a specific comment"
    )
    @action(detail=True, methods=['post'], url_path='reply')
    def create_reply(self, request, pk=None):
        """
        🚀 Create a reply to a specific comment
        This is a cool and intuitive way to reply to comments!
        """
        parent_comment = self.get_object()
        
        # Validate that we're not replying to a reply
        if parent_comment.parent is not None:
            return Response(
                {"error": "Cannot reply to a reply. Only top-level comments can have replies."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = ReplyCreateSerializer(data=request.data)
        if serializer.is_valid():
            # Get the user's profile
            try:
                user_profile = request.user.profile
            except:
                return Response(
                    {"error": "User profile not found"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            reply = serializer.save(
                profile=user_profile,
                post=parent_comment.post,
                parent=parent_comment
            )
            return Response(
                ReplySerializer(reply, context={'request': request}).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        responses={200: ReplySerializer(many=True)},
        operation_description="Get all replies for a specific comment with pagination"
    )
    @action(detail=True, methods=['get'], url_path='replies')
    def get_replies(self, request, pk=None):
        """
        📝 Get all replies for a comment
        Returns paginated replies with user info and like counts
        """
        comment = self.get_object()
        replies = comment.replies.select_related(
            'profile', 'profile__user'
        ).prefetch_related('likes').order_by('created_at')
        
        # Add pagination
        page = self.paginate_queryset(replies)
        if page is not None:
            serializer = ReplySerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = ReplySerializer(replies, many=True, context={'request': request})
        return Response(serializer.data)

    @swagger_auto_schema(
        responses={200: openapi.Response(
            description="Comment thread with replies",
            schema=CommentSerializer
        )},
        operation_description="Get a comment with all its replies in a thread format"
    )
    @action(detail=True, methods=['get'], url_path='thread')
    def get_thread(self, request, pk=None):
        """
        🧵 Get a complete comment thread
        Returns the comment with all its replies in a nested format
        """
        comment = self.get_object()
        # Get the comment with all its replies
        thread_comment = Comment.objects.select_related(
            'profile', 'profile__user', 'post'
        ).prefetch_related(
            'replies__profile',
            'replies__profile__user',
            'replies__likes',
            'likes'
        ).get(id=comment.id)
        
        serializer = CommentSerializer(thread_comment, context={'request': request})
        return Response(serializer.data)

    @swagger_auto_schema(
        responses={200: openapi.Response(
            description="Comment statistics",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'total_replies': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'total_likes': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'total_dislikes': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'reply_users': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING))
                }
            )
        )},
        operation_description="Get statistics for a comment including reply count and user engagement"
    )
    @action(detail=True, methods=['get'], url_path='stats')
    def get_stats(self, request, pk=None):
        """
        📊 Get comment statistics
        Returns engagement metrics for the comment
        """
        comment = self.get_object()
        
        # Get unique users who replied
        reply_users = comment.replies.values_list('profile__user__username', flat=True).distinct()
        
        stats = {
            'total_replies': comment.replies.count(),
            'total_likes': comment.likes_count,
            'total_dislikes': comment.dislikes_count,
            'reply_users': list(reply_users),
            'engagement_score': comment.likes_count + comment.replies.count() * 2  # Weight replies more
        }
        
        return Response(stats)

    @swagger_auto_schema(
        responses={200: ReplySerializer(many=True)},
        operation_description="Get the most popular replies for a comment"
    )
    @action(detail=True, methods=['get'], url_path='top-replies')
    def get_top_replies(self, request, pk=None):
        """
        🔥 Get the most popular replies
        Returns replies sorted by engagement (likes + replies)
        """
        comment = self.get_object()
        limit = int(request.query_params.get('limit', 5))
        
        # Get replies with engagement metrics
        replies = comment.replies.annotate(
            engagement=Count('likes', filter=Q(likes__is_like=True)) + 
                     Count('replies') * 2
        ).order_by('-engagement', '-created_at')[:limit]
        
        serializer = ReplySerializer(replies, many=True, context={'request': request})
        return Response(serializer.data)
