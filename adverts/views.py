from rest_framework import generics, status
from rest_framework.response import Response
from .models import Advert
from .serializers import AdvertSerializer
from talentsearch.throttles import CreateRateThrottle
from drf_spectacular.utils import extend_schema, OpenApiTypes, OpenApiExample
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

class AdvertView(APIView):
    permission_classes = [IsAuthenticated]
    @extend_schema(
        tags=['adverts'],
        summary='List or create advertisements',
        description='Get all advertisements or create a new one',
        request=AdvertSerializer,
        responses={
            200: AdvertSerializer(many=True),
            201: AdvertSerializer,
            400: OpenApiTypes.OBJECT,
        }
    )
    def get(self, request):
        adverts = Advert.objects.all()
        serializer = AdvertSerializer(adverts, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        tags=['adverts'],
        summary='Create advertisement',
        description='Create a new advertisement',
        request=AdvertSerializer,
        responses={
            201: AdvertSerializer,
            400: OpenApiTypes.OBJECT,
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
    queryset = Advert.objects.all()
    serializer_class = AdvertSerializer
    throttle_classes = [CreateRateThrottle]

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        response.data = {
            "id": response.data["id"],
            "message": "Advert created successfully."
        }
        return response

class AdvertRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Advert.objects.all()
    serializer_class = AdvertSerializer
    lookup_field = "id"
    throttle_classes = [CreateRateThrottle]

    @extend_schema(
        tags=['adverts'],
        summary='Get advertisement',
        description='Get a specific advertisement by ID',
        responses={
            200: AdvertSerializer,
            404: OpenApiTypes.OBJECT,
        },
        examples=[
            OpenApiExample(
                'Success Response',
                value={
                    'id': 'uuid',
                    'title': 'Advertisement Title',
                    'description': 'Advertisement description',
                    'price': 100.00,
                    'location': 'Location',
                    'created_at': '2024-03-20T10:00:00Z',
                    'updated_at': '2024-03-20T10:00:00Z'
                },
                status_codes=['200']
            ),
            OpenApiExample(
                'Not Found',
                value={'error': 'Advertisement not found'},
                status_codes=['404']
            )
        ]
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        tags=['adverts'],
        summary='Update advertisement',
        description='Update an existing advertisement',
        request=AdvertSerializer,
        responses={
            200: AdvertSerializer,
            400: OpenApiTypes.OBJECT,
            403: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
        },
        examples=[
            OpenApiExample(
                'Success Response',
                value={
                    'id': 'uuid',
                    'title': 'Updated Title',
                    'description': 'Updated description',
                    'price': 150.00,
                    'location': 'Updated location',
                    'created_at': '2024-03-20T10:00:00Z',
                    'updated_at': '2024-03-20T10:05:00Z'
                },
                status_codes=['200']
            ),
            OpenApiExample(
                'Validation Error',
                value={
                    'title': ['This field is required.'],
                    'price': ['Must be greater than 0.']
                },
                status_codes=['400']
            )
        ]
    )
    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        response.data = {
            "id": str(self.get_object().id),
            "message": "Advert updated successfully."
        }
        return response

    @extend_schema(
        tags=['adverts'],
        summary='Delete advertisement',
        description='Delete an advertisement',
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
        super().destroy(request, *args, **kwargs)
        return Response({
            "message": "Advert deleted successfully."
        }, status=status.HTTP_200_OK)