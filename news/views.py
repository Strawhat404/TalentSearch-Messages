from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import News
from .serializers import NewsSerializer
from django.shortcuts import get_object_or_404

# GET: Fetch all news
class NewsListView(APIView):
    def get(self, request):
        news = News.objects.all()
        serializer = NewsSerializer(news, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

# POST: Create news
class NewsCreateView(APIView):
    def post(self, request):
        serializer = NewsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "id": serializer.data['id'],
                "message": "News created successfully."
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# PUT: Update news by ID
class NewsUpdateView(APIView):
    def put(self, request, id):
        news = get_object_or_404(News, id=id)
        serializer = NewsSerializer(news, data=request.data, partial=True)  # partial=True allows partial updates
        if serializer.is_valid():
            serializer.save()
            return Response({
                "id": id,
                "message": "News updated successfully."
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# DELETE: Delete news by ID
class NewsDeleteView(APIView):
    def delete(self, request, id):
        news = get_object_or_404(News, id=id)
        news.delete()
        return Response({"message": "News deleted successfully."}, status=status.HTTP_200_OK)