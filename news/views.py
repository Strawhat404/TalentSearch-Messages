from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from .models import News
from .serializers import NewsSerializer
from django.shortcuts import get_object_or_404
from talentsearch.throttles import CreateRateThrottle
from rest_framework import generics
from .models import NewsImage
from .serializers import NewsImageSerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

class NewsView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]
    throttle_classes = [CreateRateThrottle]

    @swagger_auto_schema(
        operation_summary='List news',
        operation_description='Get all news articles',
        responses={200: NewsSerializer(many=True)}
    )
    def get(self, request):
        news = News.objects.all()
        serializer = NewsSerializer(news, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_summary='Create news',
        operation_description='Create a new news article',
        request_body=NewsSerializer,
        responses={
            201: NewsSerializer,
            400: openapi.Response(description="Validation Error")
        }
    )
    def post(self, request):
        serializer = NewsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "id": serializer.data['id'],
                "message": "News created successfully."
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class NewsDetailView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]
    throttle_classes = [CreateRateThrottle]

    @swagger_auto_schema(
        operation_summary='Update news',
        operation_description='Update a news article by ID',
        request_body=NewsSerializer,
        responses={
            200: openapi.Response(
                description="News updated successfully.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'id': openapi.Schema(type=openapi.TYPE_STRING, example='uuid'),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, example='News updated successfully.')
                    }
                )
            ),
            400: openapi.Response(description="Validation Error"),
            404: openapi.Response(description="Not Found")
        }
    )
    def put(self, request, id):
        news = get_object_or_404(News, id=id)
        serializer = NewsSerializer(news, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "id": id,
                "message": "News updated successfully."
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_summary='Delete news',
        operation_description='Delete a news article by ID',
        responses={
            200: openapi.Response(
                description="News deleted successfully.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING, example='News deleted successfully.')
                    }
                )
            ),
            404: openapi.Response(description="Not Found")
        }
    )
    def delete(self, request, id):
        news = get_object_or_404(News, id=id)
        news.delete()
        return Response({"message": "News deleted successfully."}, status=status.HTTP_200_OK)

class NewsImageDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = NewsImage.objects.all()
    serializer_class = NewsImageSerializer
    lookup_field = 'id'