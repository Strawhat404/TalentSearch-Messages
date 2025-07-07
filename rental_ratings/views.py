from django.shortcuts import render
from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Avg, Count, Case, When, Value, IntegerField
from django.utils import timezone
from datetime import timedelta
from .models import Rating
from .serializers import RatingSerializer, RatingStatsSerializer
from rental_items.models import RentalItem
from rental_items.permissions import IsOwnerOrReadOnly
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

# Create a custom permission for reporting
class CanReportRating(IsAuthenticated):
    """
    Custom permission that allows any authenticated user to report ratings.
    """
    def has_object_permission(self, request, view, obj):
        # Any authenticated user can report any rating
        return True

# Create your views here.

class RatingViewSet(viewsets.ModelViewSet):
    serializer_class = RatingSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    http_method_names = ['get', 'post', 'delete', 'put', 'patch']
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {
        'item_id': ['exact'],
        'user': ['exact'],
        'rating': ['exact', 'gte', 'lte', 'in'],
        'is_verified_purchase': ['exact'],
        'reported': ['exact'],
        'is_edited': ['exact'],
        'created_at': ['gte', 'lte', 'date', 'date__gte', 'date__lte'],
    }
    search_fields = ['comment', 'user__email', 'user__username']
    ordering_fields = ['rating', 'created_at', 'updated_at', 'helpful_votes']
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = Rating.objects.select_related('user', 'user__profile').all()
        
        # Advanced filtering
        min_rating = self.request.query_params.get('min_rating')
        max_rating = self.request.query_params.get('max_rating')
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        has_comment = self.request.query_params.get('has_comment')
        verified_only = self.request.query_params.get('verified_only')
        recent_only = self.request.query_params.get('recent_only')
        
        if min_rating:
            queryset = queryset.filter(rating__gte=int(min_rating))
        if max_rating:
            queryset = queryset.filter(rating__lte=int(max_rating))
        if date_from:
            queryset = queryset.filter(created_at__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__lte=date_to)
        if has_comment == 'true':
            queryset = queryset.exclude(comment='')
        if verified_only == 'true':
            queryset = queryset.filter(is_verified_purchase=True)
        if recent_only == 'true':
            # Last 30 days
            thirty_days_ago = timezone.now() - timedelta(days=30)
            queryset = queryset.filter(created_at__gte=thirty_days_ago)
            
        # Advanced sorting
        sort_by = self.request.query_params.get('sort_by')
        if sort_by == 'helpful':
            queryset = queryset.order_by('-helpful_votes', '-created_at')
        elif sort_by == 'rating_high':
            queryset = queryset.order_by('-rating', '-created_at')
        elif sort_by == 'rating_low':
            queryset = queryset.order_by('rating', '-created_at')
        elif sort_by == 'recent':
            queryset = queryset.order_by('-created_at')
        elif sort_by == 'oldest':
            queryset = queryset.order_by('created_at')
        elif sort_by == 'verified_first':
            queryset = queryset.order_by('-is_verified_purchase', '-created_at')
            
        return queryset

    def perform_create(self, serializer):
        item_id = self.request.data.get('item_id')
        # Verify that the rental item exists
        get_object_or_404(RentalItem, id=item_id)
        serializer.save(
            item_id=item_id,
            user=self.request.user
        )

    @action(detail=False, methods=['get'])
    def search_advanced(self, request):
        """Advanced search with multiple criteria"""
        query = request.query_params.get('q', '')
        item_id = request.query_params.get('item_id')
        min_rating = request.query_params.get('min_rating')
        max_rating = request.query_params.get('max_rating')
        verified_only = request.query_params.get('verified_only')
        date_range = request.query_params.get('date_range')  # 'week', 'month', 'year'
        
        queryset = self.get_queryset()
        
        # Text search
        if query:
            queryset = queryset.filter(
                Q(comment__icontains=query) |
                Q(user__email__icontains=query) |
                Q(user__username__icontains=query)
            )
        
        # Item filter
        if item_id:
            queryset = queryset.filter(item_id=item_id)
        
        # Rating range
        if min_rating:
            queryset = queryset.filter(rating__gte=int(min_rating))
        if max_rating:
            queryset = queryset.filter(rating__lte=int(max_rating))
        
        # Verified purchases only
        if verified_only == 'true':
            queryset = queryset.filter(is_verified_purchase=True)
        
        # Date range filter
        if date_range:
            now = timezone.now()
            if date_range == 'week':
                start_date = now - timedelta(days=7)
            elif date_range == 'month':
                start_date = now - timedelta(days=30)
            elif date_range == 'year':
                start_date = now - timedelta(days=365)
            else:
                start_date = None
            
            if start_date:
                queryset = queryset.filter(created_at__gte=start_date)
        
        # Order by relevance (helpful votes + recency)
        queryset = queryset.annotate(
            relevance_score=Case(
                When(is_verified_purchase=True, then=Value(10)),
                default=Value(0),
                output_field=IntegerField(),
            )
        ).order_by('-relevance_score', '-helpful_votes', '-created_at')
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get comprehensive rating statistics"""
        item_id = request.query_params.get('item_id')
        user_id = request.query_params.get('user_id')
        
        if item_id:
            stats = Rating.get_item_rating_stats(item_id)
        elif user_id:
            stats = Rating.get_user_rating_stats(user_id)
        else:
            # Global statistics
            queryset = self.get_queryset()
            total_ratings = queryset.count()
            
            if total_ratings == 0:
                stats = {
                    'total_ratings': 0,
                    'average_rating': 0,
                    'rating_distribution': {1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
                    'verified_ratings': 0,
                    'recent_ratings': 0,
                    'top_rated_items': [],
                    'most_active_users': []
                }
            else:
                average_rating = queryset.aggregate(avg=Avg('rating'))['avg']
                
                # Rating distribution
                distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
                for rating in queryset.values_list('rating', flat=True):
                    distribution[rating] += 1
                
                for key in distribution:
                    distribution[key] = (distribution[key] / total_ratings) * 100
                
                # Additional stats
                verified_ratings = queryset.filter(is_verified_purchase=True).count()
                recent_ratings = queryset.filter(
                    created_at__gte=timezone.now() - timedelta(days=30)
                ).count()
                
                # Top rated items
                top_items = queryset.values('item_id').annotate(
                    avg_rating=Avg('rating'),
                    count=Count('id')
                ).filter(count__gte=3).order_by('-avg_rating')[:10]
                
                # Most active users
                active_users = queryset.values('user__email').annotate(
                    count=Count('id')
                ).order_by('-count')[:10]
                
                stats = {
                    'total_ratings': total_ratings,
                    'average_rating': round(average_rating, 2),
                    'rating_distribution': distribution,
                    'verified_ratings': verified_ratings,
                    'recent_ratings': recent_ratings,
                    'top_rated_items': list(top_items),
                    'most_active_users': list(active_users)
                }
        
        return Response(stats)

    @action(detail=True, methods=['post'])
    def mark_helpful(self, request, pk=None):
        """Mark a rating as helpful"""
        rating = self.get_object()
        rating.helpful_votes += 1
        rating.save()
        
        return Response({
            'message': 'Rating marked as helpful',
            'helpful_votes': rating.helpful_votes
        })

    @action(detail=True, methods=['post'], permission_classes=[CanReportRating])
    def report(self, request, pk=None):
        """Report a rating"""
        rating = self.get_object()
        
        # Prevent users from reporting their own ratings
        if rating.user == request.user:
            return Response({
                'error': 'You cannot report your own rating'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        rating.reported = True
        rating.save()
        
        return Response({
            'message': 'Rating reported successfully'
        })

    @action(detail=False, methods=['get'])
    def by_item(self, request):
        """Get all ratings for a specific item with enhanced filtering"""
        item_id = request.query_params.get('item_id')
        if not item_id:
            return Response(
                {'error': 'item_id parameter is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = self.get_queryset().filter(item_id=item_id)
        
        # Get item details
        try:
            item = RentalItem.objects.get(id=item_id)
            item_details = {
                'id': str(item.id),
                'name': item.name,
                'image': item.image.url if item.image else None
            }
        except RentalItem.DoesNotExist:
            item_details = None
        
        # Get rating statistics for this item
        stats = Rating.get_item_rating_stats(item_id)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response_data = {
                'item_details': item_details,
                'statistics': stats,
                'ratings': self.get_paginated_response(serializer.data).data
            }
            return Response(response_data)
        
        serializer = self.get_serializer(queryset, many=True)
        response_data = {
            'item_details': item_details,
            'statistics': stats,
            'ratings': serializer.data
        }
        return Response(response_data)

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
                name='max_rating',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_INTEGER,
                description='Filter by maximum rating value'
            ),
            openapi.Parameter(
                name='verified_only',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_BOOLEAN,
                description='Show only verified purchase ratings'
            ),
            openapi.Parameter(
                name='sort_by',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description='Sort by: helpful, rating_high, rating_low, recent, oldest, verified_first'
            )
        ],
        responses={
            200: RatingSerializer(many=True),
            400: openapi.Response(description='Invalid parameters'),
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
        summary='Retrieve a rating',
        description='Retrieves a rating by its ID.',
        responses={
            200: RatingSerializer,
            404: openapi.Response(description='Rating not found'),
        },
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['rental_ratings'],
        summary='Update a rating',
        description='Updates a rating. Only the owner can perform this action.',
        request_body=RatingSerializer,
        responses={
            200: RatingSerializer,
            400: openapi.Response(description='Validation error'),
            403: openapi.Response(description='Permission denied'),
            404: openapi.Response(description='Rating not found'),
        },
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['rental_ratings'],
        summary='Partially update a rating',
        description='Partially updates a rating. Only the owner can perform this action.',
        request_body=RatingSerializer,
        responses={
            200: RatingSerializer,
            400: openapi.Response(description='Validation error'),
            403: openapi.Response(description='Permission denied'),
            404: openapi.Response(description='Rating not found'),
        },
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

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
        }, status=status.HTTP_204_NO_CONTENT)
