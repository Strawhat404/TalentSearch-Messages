from django.shortcuts import render
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from drf_spectacular.utils import extend_schema, OpenApiParameter
from .models import CommentReaction
from .serializers import CommentReactionSerializer, CommentReactionCreateSerializer

# Create your views here.

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of a reaction to modify it.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True
        # Write permissions are only allowed to the owner
        return obj.user == request.user

class CommentReactionViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    serializer_class = CommentReactionSerializer
    queryset = CommentReaction.objects.select_related(
        'user',
        'user__profile',
        'comment'
    )

    def get_queryset(self):
        queryset = super().get_queryset()
        comment_id = self.request.query_params.get('comment_id')
        user_id = self.request.query_params.get('user_id')
        is_dislike = self.request.query_params.get('is_dislike')

        if comment_id:
            queryset = queryset.filter(comment_id=comment_id)
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        if is_dislike is not None:
            queryset = queryset.filter(is_dislike=is_dislike.lower() == 'true')

        # Filter out reactions that don't belong to the user for non-safe methods
        if self.request.method not in permissions.SAFE_METHODS:
            queryset = queryset.filter(user=self.request.user)

        return queryset

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return CommentReactionCreateSerializer
        return CommentReactionSerializer

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='comment_id',
                type=str,
                description='Filter reactions by comment ID'
            ),
            OpenApiParameter(
                name='user_id',
                type=str,
                description='Filter reactions by user ID'
            ),
            OpenApiParameter(
                name='is_dislike',
                type=bool,
                description='Filter by reaction type (True for dislikes, False for likes)'
            ),
        ],
        responses={200: CommentReactionSerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        request=CommentReactionCreateSerializer,
        responses={201: CommentReactionSerializer}
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            {
                "message": "Reaction added successfully",
                "data": serializer.data
            },
            status=status.HTTP_201_CREATED,
            headers=headers
        )

    @extend_schema(
        request=CommentReactionCreateSerializer,
        responses={200: CommentReactionSerializer}
    )
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(
            {
                "message": "Reaction updated successfully",
                "data": serializer.data
            }
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {"message": "Reaction removed successfully"},
            status=status.HTTP_200_OK
        )

    @extend_schema(
        request=CommentReactionCreateSerializer,
        responses={200: CommentReactionSerializer}
    )
    @action(detail=False, methods=['post'])
    def toggle(self, request):
        """
        Toggle between like and dislike for a comment.
        If no reaction exists, creates a new one.
        If a reaction exists, switches between like and dislike.
        """
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        comment = serializer.validated_data['comment']
        is_dislike = serializer.validated_data['is_dislike']
        
        # Get existing reaction if any
        existing_reaction = CommentReaction.objects.filter(
            comment=comment,
            user=request.user
        ).first()
        
        if existing_reaction:
            # If same reaction type, remove it
            if existing_reaction.is_dislike == is_dislike:
                existing_reaction.delete()
                return Response(
                    {
                        "message": "Reaction removed successfully",
                        "data": None
                    },
                    status=status.HTTP_200_OK
                )
            # If different reaction type, update it
            existing_reaction.is_dislike = is_dislike
            existing_reaction.save()
            reaction = existing_reaction
        else:
            # Create new reaction
            reaction = CommentReaction.objects.create(
                comment=comment,
                user=request.user,
                is_dislike=is_dislike
            )
        
        return Response(
            {
                "message": "Reaction toggled successfully",
                "data": CommentReactionSerializer(reaction).data
            },
            status=status.HTTP_200_OK
        )
