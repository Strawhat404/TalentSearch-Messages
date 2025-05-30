from rest_framework import generics, status
from rest_framework.response import Response
from .models import Advert
from .serializers import AdvertSerializer
from talentsearch.throttles import CreateRateThrottle
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

class AdvertView(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        operation_summary='List advertisements',
        operation_description='Get all advertisements',
        responses={
            200: AdvertSerializer(many=True),
        }
    )
    def get(self, request):
        adverts = Advert.objects.all()
        serializer = AdvertSerializer(adverts, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_summary='Create advertisement',
        operation_description='Create a new advertisement',
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
            400: openapi.Response(description="Validation Error")
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

    @swagger_auto_schema(
        operation_summary='Get advertisement',
        operation_description='Get a specific advertisement by ID',
        responses={
            200: AdvertSerializer(),
            404: openapi.Response(description="Not Found")
        }
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary='Update advertisement',
        operation_description='Update an existing advertisement',
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
            403: openapi.Response(description="Permission Denied"),
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
        operation_description='Delete an advertisement',
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
            403: openapi.Response(description="Permission Denied"),
            404: openapi.Response(description="Not Found")
        }
    )
    def destroy(self, request, *args, **kwargs):
        super().destroy(request, *args, **kwargs)
        return Response({
            "message": "Advert deleted successfully."
        }, status=status.HTTP_200_OK)