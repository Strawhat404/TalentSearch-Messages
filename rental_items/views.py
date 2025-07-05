from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from .models import RentalItem, RentalItemRating, Wishlist
from .serializers import (
    RentalItemSerializer,
    RentalItemListSerializer,
    RentalItemUpdateSerializer,
    RentalItemRatingSerializer,
    WishlistSerializer
)
from .permissions import IsOwnerOrReadOnly, IsAdminOrReadOnly
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from authapp.services import notify_new_rental_posted, notify_rental_verification_status
from rest_framework.generics import ListCreateAPIView
from rest_framework.viewsets import ModelViewSet

class RentalItemViewSet(ModelViewSet):
    queryset = RentalItem.objects.all()
    serializer_class = RentalItemSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['type', 'category', 'available', 'featured_item', 'approved', 'user']
    search_fields = ['name', 'description']
    ordering_fields = ['daily_rate', 'created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return RentalItemListSerializer
        elif self.action in ['update', 'partial_update']:
            return RentalItemUpdateSerializer
        return RentalItemSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by price range
        min_rate = self.request.query_params.get('min_rate')
        max_rate = self.request.query_params.get('max_rate')
        
        if min_rate:
            queryset = queryset.filter(daily_rate__gte=min_rate)
        if max_rate:
            queryset = queryset.filter(daily_rate__lte=max_rate)
            
        return queryset

    def perform_create(self, serializer):
        rental_item = serializer.save(user=self.request.user)
        # Trigger notification for new rental item
        notify_new_rental_posted(rental_item)
        return rental_item

    @action(detail=True, methods=['put'], permission_classes=[IsAdminUser])
    def approve(self, request, pk=None):
        rental_item = self.get_object()
        rental_item.approved = True
        rental_item.save()
        
        # Trigger notification for rental approval
        notify_rental_verification_status(rental_item, request.user, True)
        
        return Response({
            'id': str(rental_item.id),
            'message': 'Rental item approved successfully.',
            'approved': True
        })

    @action(detail=True, methods=['put'], permission_classes=[IsAdminUser])
    def reject(self, request, pk=None):
        rental_item = self.get_object()
        rental_item.approved = False
        rental_item.save()
        
        reason = request.data.get('reason', '')
        
        # Trigger notification for rental rejection
        notify_rental_verification_status(rental_item, request.user, False, reason)
        
        return Response({
            'id': str(rental_item.id),
            'message': 'Rental item rejected successfully.',
            'approved': False,
            'reason': reason
        })

    @swagger_auto_schema(
        tags=['rental_items'],
        summary='Update rental item',
        description='Update an existing rental item',
        request=RentalItemUpdateSerializer,
        responses={
            200: RentalItemSerializer,
            400: openapi.Response(description='Validation error'),
            403: openapi.Response(description='Permission denied'),
            404: openapi.Response(description='Rental item not found'),
        },
        help_text='Update an existing rental item',
        example={
                    'id': 'uuid',
                    'name': 'Updated Item Name',
                    'type': 'equipment',
                    'category': 'tools',
                    'daily_rate': 50.00,
                    'available': True,
                    'featured_item': False,
                    'approved': True,
                    'user_profile': {
                        'name': 'Owner Name',
                        'photo': 'photo_url'
                    }
        }
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['rental_items'],
        summary='Delete rental item',
        description='Delete a rental item',
        responses={
            204: None,
            403: openapi.Response(description='Permission denied'),
            404: openapi.Response(description='Rental item not found'),
        },
        help_text='Delete a rental item',
        example=None
    )
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({
            'message': 'Rental item deleted successfully.'
        })

class RatingViewSet(viewsets.ModelViewSet):
    serializer_class = RentalItemRatingSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    http_method_names = ['get', 'post', 'delete', 'put', 'patch']  # Only allo, POST, DELETE, pUT

    def get_queryset(self):
        queryset = RentalItemRating.objects.all()
        
        # Filter by item_id
        item_id = self.request.query_params.get('item_id')
        if item_id:
            queryset = queryset.filter(rental_item_id=item_id)
            
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
        rental_item = get_object_or_404(RentalItem, id=item_id)
        serializer.save(
            rental_item=rental_item,
            user=self.request.user
        )

    @swagger_auto_schema(
        tags=['rental_items'],
        summary='Delete rating',
        description='Delete a rating for a rental item',
        responses={
            200: openapi.Response(description='Rating deleted successfully'),
            403: openapi.Response(description='Permission denied'),
            404: openapi.Response(description='Rating not found'),
        },
        help_text='Delete a rating for a rental item',
        example={'message': 'Rating deleted successfully.'}
    )
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({
            'message': 'Rating deleted successfully.'
        })

class RentalItemListCreateView(ListCreateAPIView):
    queryset = RentalItem.objects.all()
    serializer_class = RentalItemSerializer

class WishlistViewSet(viewsets.ModelViewSet):
    serializer_class = WishlistSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'delete']

    def get_queryset(self):
        return Wishlist.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @swagger_auto_schema(
        tags=['wishlist'],
        summary='Get all wishlist items',
        description='Retrieve all items in the authenticated user\'s wishlist',
        responses={
            200: WishlistSerializer(many=True),
            401: openapi.Response(description='Authentication required'),
        },
        help_text='Get all items in user\'s wishlist',
        example=[
            {
                'id': 'uuid',
                'rental_item': {
                    'id': 'uuid',
                    'name': 'Camera Equipment',
                    'type': 'electronics',
                    'category': 'photography',
                    'daily_rate': 50.00,
                    'image': 'image_url',
                    'user_profile': {
                        'name': 'Owner Name',
                        'photo': 'photo_url'
                    }
                },
                'created_at': '2024-01-01T12:00:00Z'
            }
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['wishlist'],
        summary='Add item to wishlist',
        description='Add a rental item to the authenticated user\'s wishlist',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'rental_item_id': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_UUID, description='UUID of the rental item to add to wishlist')
            },
            required=['rental_item_id']
        ),
        responses={
            201: WishlistSerializer,
            400: openapi.Response(description='Validation error'),
            401: openapi.Response(description='Authentication required'),
            404: openapi.Response(description='Rental item not found'),
        },
        help_text='Add a rental item to wishlist',
        example={
            'rental_item_id': 'uuid-of-rental-item'
        }
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['wishlist'],
        summary='Get wishlist count',
        description='Get the total count of items in the authenticated user\'s wishlist',
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'count': openapi.Schema(type=openapi.TYPE_INTEGER, description='Number of items in wishlist')
                }
            ),
            401: openapi.Response(description='Authentication required'),
        },
        help_text='Get wishlist count',
        example={'count': 5}
    )
    @action(detail=False, methods=['get'])
    def count(self, request):
        """Get the count of items in user's wishlist"""
        count = self.get_queryset().count()
        return Response({'count': count})

    @swagger_auto_schema(
        tags=['wishlist'],
        summary='Check if item is in wishlist',
        description='Check if a specific rental item is in the authenticated user\'s wishlist',
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'is_in_wishlist': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Whether the item is in wishlist'),
                    'wishlist_item_id': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_UUID, description='Wishlist item ID if found'),
                    'added_at': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME, description='When item was added to wishlist')
                }
            ),
            401: openapi.Response(description='Authentication required'),
        },
        help_text='Check if item is in wishlist',
        example={
            'is_in_wishlist': True,
            'wishlist_item_id': 'uuid',
            'added_at': '2024-01-01T12:00:00Z'
        }
    )
    @action(detail=True, methods=['get'])
    def check(self, request, pk=None):
        """Check if a specific item is in user's wishlist"""
        try:
            wishlist_item = self.get_queryset().get(rental_item_id=pk)
            return Response({
                'is_in_wishlist': True,
                'wishlist_item_id': str(wishlist_item.id),
                'added_at': wishlist_item.created_at
            })
        except Wishlist.DoesNotExist:
            return Response({
                'is_in_wishlist': False
            })

    @swagger_auto_schema(
        tags=['wishlist'],
        summary='Remove item from wishlist',
        description='Remove a rental item from the authenticated user\'s wishlist',
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'message': openapi.Schema(type=openapi.TYPE_STRING, description='Success message')
                }
            ),
            401: openapi.Response(description='Authentication required'),
            404: openapi.Response(description='Item not found in wishlist'),
        },
        help_text='Remove item from wishlist',
        example={'message': 'Item removed from wishlist successfully.'}
    )
    def destroy(self, request, *args, **kwargs):
        """Remove item from wishlist by rental item ID"""
        rental_item_id = kwargs.get('pk')
        try:
            wishlist_item = self.get_queryset().get(rental_item_id=rental_item_id)
            wishlist_item.delete()
            return Response({
                'message': 'Item removed from wishlist successfully.'
            }, status=status.HTTP_200_OK)
        except Wishlist.DoesNotExist:
            return Response({
                'message': 'Item not found in wishlist.'
            }, status=status.HTTP_404_NOT_FOUND)
