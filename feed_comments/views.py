from django.shortcuts import render
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import Comment, CommentLike
from .serializers import (
    CommentSerializer,
    CommentCreateSerializer,
    CommentLikeSerializer
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
        return obj.user == request.user

class CommentViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    serializer_class = CommentSerializer
    queryset = Comment.objects.select_related(
        'user',
        'user__profile',
        'post',
        'parent'
    ).prefetch_related(
        'replies',
        'replies__user',
        'replies__user__profile',
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
        serializer.save(user=self.request.user)

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
        
        # Get or create the like object
        like, created = CommentLike.objects.get_or_create(
            comment=comment,
            user=request.user,
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
