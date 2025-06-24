from rest_framework import generics, status
from rest_framework.response import Response
from .models import Advert
from .serializers import AdvertSerializer
from talentsearch.throttles import CreateRateThrottle
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.core.files.storage import default_storage
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied
from .permissions import IsAdvertOwnerOrReadOnly, IsAuthenticatedForModification

class AdvertView(APIView):
    def get_permissions(self):
        """
        Allow public access for GET requests, require authentication for POST
        """
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_queryset(self):
        """
        Return appropriate queryset based on authentication status
        - Public users see only published adverts
        - Authenticated users see all adverts
        """
        if self.request.user.is_authenticated:
            return Advert.objects.all()
        else:
            # For public access, show only published adverts that are currently running
            now = timezone.now()
            return Advert.objects.filter(
                status='published',
                run_from__lte=now,
                run_to__gte=now
            )

    @swagger_auto_schema(
        operation_summary='List advertisements',
        operation_description='Get all advertisements (public access shows only published adverts)',
        responses={
            200: AdvertSerializer(many=True),
        }
    )
    def get(self, request):
        adverts = self.get_queryset()
        serializer = AdvertSerializer(adverts, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_summary='Create advertisement',
        operation_description='Create a new advertisement (requires authentication)',
        request_body=AdvertSerializer,
        responses={
            201: openapi.Response(
                description="Advert created successfully.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'id': openapi.Schema(type=openapi.TYPE_STRING, example='uuid'),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, example='Advert created successfully.')
                    }
                )
            ),
            400: openapi.Response(description="Validation Error"),
            401: openapi.Response(description="Authentication Required")
        }
    )
    def post(self, request):
        serializer = AdvertSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "id": serializer.data['id'],
                "message": "Advert created successfully."
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AdvertListCreateView(generics.ListCreateAPIView):
    serializer_class = AdvertSerializer
    permission_classes = [IsAuthenticatedForModification]

    def get_throttles(self):
        """
        Apply throttling only to modification operations
        """
        if self.request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            return [CreateRateThrottle()]
        return []

    def get_queryset(self):
        """
        Return appropriate queryset based on authentication status using custom manager
        """
        return Advert.objects.for_user(self.request.user)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        response.data = {
            "id": response.data["id"],
            "message": "Advert created successfully."
        }
        return response

    @swagger_auto_schema(
        operation_summary='List advertisements',
        operation_description='Get all advertisements (public access shows only published adverts)',
        responses={
            200: AdvertSerializer(many=True),
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary='Create advertisement',
        operation_description='Create a new advertisement (requires authentication)',
        request_body=AdvertSerializer,
        responses={
            201: openapi.Response(
                description="Advert created successfully.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'id': openapi.Schema(type=openapi.TYPE_STRING, example='uuid'),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, example='Advert created successfully.')
                    }
                )
            ),
            400: openapi.Response(description="Validation Error"),
            401: openapi.Response(description="Authentication Required")
        }
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class AdvertRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AdvertSerializer
    lookup_field = "id"
    permission_classes = [IsAdvertOwnerOrReadOnly]

    def get_throttles(self):
        """
        Apply throttling only to modification operations
        """
        if self.request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            return [CreateRateThrottle()]
        return []

    def get_queryset(self):
        """
        Return appropriate queryset based on authentication status using custom manager
        """
        return Advert.objects.for_user(self.request.user)

    @swagger_auto_schema(
        operation_summary='Get advertisement',
        operation_description='Get a specific advertisement by ID (public access shows only published adverts)',
        responses={
            200: AdvertSerializer(),
            404: openapi.Response(description="Not Found")
        }
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary='Update advertisement',
        operation_description='Update an existing advertisement (requires authentication and ownership)',
        request_body=AdvertSerializer,
        responses={
            200: openapi.Response(
                description="Advert updated successfully.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'id': openapi.Schema(type=openapi.TYPE_STRING, example='uuid'),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, example='Advert updated successfully.')
                    }
                )
            ),
            400: openapi.Response(description="Validation Error"),
            401: openapi.Response(description="Authentication Required"),
            403: openapi.Response(description="Permission Denied - You can only modify your own adverts"),
            404: openapi.Response(description="Not Found")
        }
    )
    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        response.data = {
            "id": str(self.get_object().id),
            "message": "Advert updated successfully."
        }
        return response

    @swagger_auto_schema(
        operation_summary='Delete advertisement',
        operation_description='Delete an advertisement (requires authentication and ownership)',
        responses={
            200: openapi.Response(
                description="Advert deleted successfully.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING, example='Advert deleted successfully.')
                    }
                )
            ),
            401: openapi.Response(description="Authentication Required"),
            403: openapi.Response(description="Permission Denied - You can only delete your own adverts"),
            404: openapi.Response(description="Not Found")
        }
    )
    def destroy(self, request, *args, **kwargs):
        super().destroy(request, *args, **kwargs)
        return Response({
            "message": "Advert deleted successfully."
        }, status=status.HTTP_200_OK)