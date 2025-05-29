from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import Rating
from .serializers import RatingSerializer
from rental_items.models import RentalItem
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

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

    @swagger_auto_schema(
        tags=['rental_ratings'],
        summary='List ratings',
        description='Get all ratings with optional filtering',
        parameters=[
            openapi.Parameter(
                name='item_id',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description='Filter ratings by item ID'
            ),
            openapi.Parameter(
                name='user_id',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description='Filter ratings by user ID'
            ),
            openapi.Parameter(
                name='min_rating',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_INTEGER,
                description='Filter by minimum rating value'
            ),
            openapi.Parameter(
                name='sort',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description='Sort by: newest, highest, lowest'
            )
        ],
        responses={
            200: RatingSerializer(many=True),
            400: openapi.Response(description='Invalid sort parameter'),
        },
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['rental_ratings'],
        summary='Create rating',
        description='Create a new rating for a rental item',
        request=RatingSerializer,
        responses={
            201: RatingSerializer,
            400: openapi.Response(description='Validation error'),
            404: openapi.Response(description='Rental item not found'),
        },
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['rental_ratings'],
        summary='Delete rating',
        description='Delete a rating',
        responses={
            204: None,
            403: openapi.Response(description='Permission denied'),
            404: openapi.Response(description='Rating not found'),
        },
    )
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({
            'message': 'Rating deleted successfully.'
        })
