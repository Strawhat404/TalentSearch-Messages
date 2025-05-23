from rest_framework import generics, status, serializers
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import FeedLike
from .serializers import FeedLikeSerializer
from drf_spectacular.utils import extend_schema, OpenApiTypes
import uuid

class FeedLikeListView(generics.ListCreateAPIView):
    serializer_class = FeedLikeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = FeedLike.objects.all()
        post_id = self.request.query_params.get('post_id')
        user_id = self.request.query_params.get('user_id')

        # Apply filters one at a time
        if post_id:
            try:
                post_id = uuid.UUID(post_id)
                queryset = queryset.filter(post_id=post_id)
            except ValueError:
                return FeedLike.objects.none()

        if user_id:
            try:
                user_id = int(user_id)
                queryset = queryset.filter(user_id=user_id)
            except ValueError:
                return FeedLike.objects.none()

        return queryset.order_by('-created_at')

    @extend_schema(
        tags=['feed_likes'],
        summary='List feed likes',
        description='Get all feed likes with optional filtering by post_id and user_id',
        responses={200: FeedLikeSerializer(many=True), 400: OpenApiTypes.OBJECT}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        tags=['feed_likes'],
        summary='Like a post',
        description='Create a new like for a post',
        request=FeedLikeSerializer,
        responses={201: OpenApiTypes.OBJECT, 400: OpenApiTypes.OBJECT}
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class FeedLikeDeleteView(generics.GenericAPIView):
    serializer_class = FeedLikeSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['feed_likes'],
        summary='Unlike a post',
        description='Remove a like from a post',
        request=FeedLikeSerializer,
        responses={200: OpenApiTypes.OBJECT, 404: OpenApiTypes.OBJECT}
    )
    def delete(self, request, *args, **kwargs):
        post_id = request.data.get('post_id')

        if not post_id:
            return Response({'error': 'post_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            post_uuid = uuid.UUID(post_id)
        except ValueError:
            return Response({'error': 'Invalid UUID format for post_id'}, status=status.HTTP_400_BAD_REQUEST)

        like = FeedLike.objects.filter(post_id=post_uuid, user=request.user).first()
        if not like:
            return Response({'error': 'Like not found'}, status=status.HTTP_404_NOT_FOUND)

        like.delete()
        return Response({'message': 'Post unliked successfully'}, status=status.HTTP_200_OK)
