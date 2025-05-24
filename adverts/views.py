from rest_framework import generics, status
from rest_framework.response import Response
from .models import Advert
from .serializers import AdvertSerializer
from talentsearch.throttles import CreateRateThrottle
from drf_spectacular.utils import extend_schema, OpenApiTypes
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

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        response.data = {
            "id": str(self.get_object().id),
            "message": "Advert updated successfully."
        }
        return response

    def destroy(self, request, *args, **kwargs):
        super().destroy(request, *args, **kwargs)
        return Response({
            "message": "Advert deleted successfully."
        }, status=status.HTTP_200_OK)