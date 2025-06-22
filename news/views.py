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
    throttle_classes = [CreateRateThrottle]

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        GET requests are public, other methods require admin authentication.
        """
        if self.request.method == 'GET':
            return []  # Public access for reading news
        return [IsAuthenticated(), IsAdminUser()]  # Admin access for creating news

    @swagger_auto_schema(
        operation_summary='List news (Public)',
        operation_description='Get all published news articles - no authentication required',
        responses={200: NewsSerializer(many=True)}
    )
    def get(self, request):
        # Only return published news for public access
        news = News.objects.filter(status='published').order_by('-created_at')
        serializer = NewsSerializer(news, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_summary='Create news (Admin only)',
        operation_description='Create a new news article - requires admin authentication',
        request_body=NewsSerializer,
        responses={
            201: NewsSerializer,
            400: openapi.Response(description="Validation Error"),
            401: openapi.Response(description="Authentication required"),
            403: openapi.Response(description="Admin privileges required")
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
    throttle_classes = [CreateRateThrottle]

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        GET requests are public, other methods require admin authentication.
        """
        if self.request.method == 'GET':
            return []  # Public access for reading specific news
        return [IsAuthenticated(), IsAdminUser()]  # Admin access for updating/deleting news

    @swagger_auto_schema(
        operation_summary='Get news detail (Public)',
        operation_description='Get a specific news article by ID - no authentication required',
        responses={
            200: NewsSerializer,
            404: openapi.Response(description="Not Found")
        }
    )
    def get(self, request, id):
        # Only return published news for public access
        try:
            news = News.objects.get(id=id, status='published')
            serializer = NewsSerializer(news)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except News.DoesNotExist:
            return Response({"message": "News not found or not published."}, status=status.HTTP_404_NOT_FOUND)

    @swagger_auto_schema(
        operation_summary='Update news (Admin only)',
        operation_description='Update a news article by ID - requires admin authentication',
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
            401: openapi.Response(description="Authentication required"),
            403: openapi.Response(description="Admin privileges required"),
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
        operation_summary='Delete news (Admin only)',
        operation_description='Delete a news article by ID - requires admin authentication',
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
            401: openapi.Response(description="Authentication required"),
            403: openapi.Response(description="Admin privileges required"),
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