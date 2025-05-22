from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from .models import RentalItem, RentalItemRating
from .serializers import (
    RentalItemSerializer,
    RentalItemListSerializer,
    RentalItemUpdateSerializer,
    RentalItemRatingSerializer
)
from .permissions import IsOwnerOrReadOnly, IsAdminOrReadOnly

class RentalItemViewSet(viewsets.ModelViewSet):
    queryset = RentalItem.objects.all()
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
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['put'], permission_classes=[IsAdminUser])
    def approve(self, request, pk=None):
        rental_item = self.get_object()
        rental_item.approved = True
        rental_item.save()
        return Response({
            'id': str(rental_item.id),
            'message': 'Rental item approved successfully.',
            'approved': True
        })

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({
            'message': 'Rental item deleted successfully.'
        })

class RatingViewSet(viewsets.ModelViewSet):
    serializer_class = RentalItemRatingSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'delete']  # Only allow GET, POST, DELETE

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

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({
            'message': 'Rating deleted successfully.'
        })
