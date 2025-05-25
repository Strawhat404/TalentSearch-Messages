from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import Rating
from .serializers import RatingSerializer
from rental_items.models import RentalItem
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample, OpenApiTypes

# Create your views here.

class RatingViewSet(viewsets.ModelViewSet):
    serializer_class = RatingSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'delete']  # Only allow GET, POST, DELETE

    def get_queryset(self):
        queryset = Rating.objects.all()
        
        # Filter by item_id
        item_id = self.request.query_params.get('item_id')
        if item_id:
            queryset = queryset.filter(item_id=item_id)
            
        # Filter by user_id
        user_id = self.request.query_params.get('user_id')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
            
        # Filter by minimum rating
        min_rating = self.request.query_params.get('min_rating')
        if min_rating:
            queryset = queryset.filter(rating__gte=min_rating)
            
        # Sort by
        sort = self.request.query_params.get('sort')
        if sort == 'newest':
            queryset = queryset.order_by('-created_at')
        elif sort == 'highest':
            queryset = queryset.order_by('-rating', '-created_at')
        elif sort == 'lowest':
            queryset = queryset.order_by('rating', '-created_at')
        else:
            queryset = queryset.order_by('-created_at')
            
        return queryset

    def perform_create(self, serializer):
        item_id = self.request.data.get('item_id')
        # Verify that the rental item exists
        get_object_or_404(RentalItem, id=item_id)
        serializer.save(
            item_id=item_id,
            user=self.request.user
        )

    @extend_schema(
        tags=['rental_ratings'],
        summary='List ratings',
        description='Get all ratings with optional filtering',
        parameters=[
            OpenApiParameter(
                name='item_id',
                type=str,
                description='Filter ratings by item ID'
            ),
            OpenApiParameter(
                name='user_id',
                type=str,
                description='Filter ratings by user ID'
            ),
            OpenApiParameter(
                name='min_rating',
                type=int,
                description='Filter by minimum rating value'
            ),
            OpenApiParameter(
                name='sort',
                type=str,
                description='Sort by: newest, highest, lowest'
            )
        ],
        responses={
            200: RatingSerializer(many=True),
            400: OpenApiTypes.OBJECT,
        },
        examples=[
            OpenApiExample(
                'Success Response',
                value=[{
                    'id': 'uuid',
                    'item_id': 'item_uuid',
                    'user_id': 'user_uuid',
                    'rating': 5,
                    'comment': 'Great item!',
                    'created_at': '2024-03-20T10:00:00Z',
                    'user_profile': {
                        'name': 'User Name',
                        'photo': 'photo_url'
                    },
                    'item_details': {
                        'name': 'Item Name',
                        'image': 'image_url'
                    }
                }],
                status_codes=['200']
            ),
            OpenApiExample(
                'Invalid Parameters',
                value={'error': 'Invalid sort parameter'},
                status_codes=['400']
            )
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        tags=['rental_ratings'],
        summary='Create rating',
        description='Create a new rating for a rental item',
        request=RatingSerializer,
        responses={
            201: RatingSerializer,
            400: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
        },
        examples=[
            OpenApiExample(
                'Success Response',
                value={
                    'id': 'uuid',
                    'item_id': 'item_uuid',
                    'user_id': 'user_uuid',
                    'rating': 5,
                    'comment': 'Great item!',
                    'created_at': '2024-03-20T10:00:00Z'
                },
                status_codes=['201']
            ),
            OpenApiExample(
                'Validation Error',
                value={
                    'rating': ['Rating must be between 1 and 5.'],
                    'item_id': ['This field is required.']
                },
                status_codes=['400']
            ),
            OpenApiExample(
                'Item Not Found',
                value={'error': 'Rental item not found'},
                status_codes=['404']
            )
        ]
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(
        tags=['rental_ratings'],
        summary='Delete rating',
        description='Delete a rating',
        responses={
            204: None,
            403: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
        },
        examples=[
            OpenApiExample(
                'Success Response',
                value=None,
                status_codes=['204']
            ),
            OpenApiExample(
                'Permission Denied',
                value={'detail': 'You do not have permission to perform this action.'},
                status_codes=['403']
            )
        ]
    )
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({
            'message': 'Rating deleted successfully.'
        })
