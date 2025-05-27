from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import GalleryItem
from .serializers import GalleryItemSerializer
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.parsers import MultiPartParser
import os
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiTypes

class GalleryItemListCreateView(APIView):
    """
    API view for listing and creating gallery items.

    Handles POST requests to add new gallery items and GET requests to retrieve filtered items.
    """
    parser_classes = [MultiPartParser]

    def post(self, request):
        """
        Create a new gallery item for the authenticated user.

        Args:
            request (Request): The HTTP request object containing the gallery item data.

        Returns:
            Response: The created gallery item data or validation errors.
        """
        serializer = GalleryItemSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            # Get the full serialized data
            data = serializer.data
            # Create a response with actual id and profile_id, excluding 'profile'
            response_data = {
                "id": data["id"],  # Use actual ID
                "profile_id": data["profile_id"],  # Use actual profile_id
                "item_url": data["item_url"],
                "item_type": data["item_type"],
                "description": data["description"],
                "created_at": data["created_at"],
                "updated_at": data["updated_at"]
            }
            return Response(response_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        """
        Retrieve a list of gallery items filtered by profile_id and other query parameters.

        Args:
            request (Request): The HTTP request object with query parameters.

        Returns:
            Response: A list of gallery items matching the filters.
        """
        profile_id = request.query_params.get('profile_id', None)
        item_type = request.query_params.get('item_type', None)
        sort = request.query_params.get('sort', 'newest')
        limit = request.query_params.get('limit', 10)

        print(f"Received profile_id: {profile_id}")  # Debug log
        items = GalleryItem.objects.filter(profile_id=profile_id)  # Changed from profile_id__user__id to profile_id
        print(f"Queried items: {list(items)}")  # Debug log
        if item_type:
            items = items.filter(item_type=item_type)
        if sort == 'oldest':
            items = items.order_by('created_at')
        else:
            items = items.order_by('-created_at')
        items = items[:int(limit)]

        serializer = GalleryItemSerializer(items, many=True)
        # Create a list response with actual id and profile_id, excluding 'profile'
        response_data = [
            {
                "id": item["id"],  # Use actual ID
                "profile_id": item["profile_id"],  # Use actual profile_id
                "item_url": item["item_url"],
                "item_type": item["item_type"],
                "description": item["description"],
                "created_at": item["created_at"],
                "updated_at": item["updated_at"]
            }
            for item in serializer.data
        ]
        print(f"Serialized data: {response_data}")  # Debug log
        return Response(response_data)

class GalleryItemDetailView(APIView):
    """
    API view for retrieving, updating, and deleting a specific gallery item.
    """
    parser_classes = [MultiPartParser]

    @extend_schema(
        tags=['user_gallery'],
        summary='Get gallery item',
        description='Get a specific gallery item by ID',
        responses={
            200: GalleryItemSerializer,
            404: OpenApiTypes.OBJECT,
        },
        examples=[
            OpenApiExample(
                'Success Response',
                value={
                    'id': 1,
                    'profile_id': 'profile_uuid',
                    'item_url': 'item_url',
                    'item_type': 'image',
                    'description': 'Item description',
                    'created_at': '2024-03-20T10:00:00Z',
                    'updated_at': '2024-03-20T10:00:00Z'
                },
                status_codes=['200']
            ),
            OpenApiExample(
                'Not Found',
                value={'error': 'Gallery item not found'},
                status_codes=['404']
            )
        ]
    )
    def get(self, request, id):
        """
        Retrieve a specific gallery item by ID.

        Args:
            request (Request): The HTTP request object.
            id (int): The primary key of the gallery item.

        Returns:
            Response: The gallery item data or a 404 error if not found.
        """
        try:
            item = GalleryItem.objects.get(id=id)
            serializer = GalleryItemSerializer(item)
            data = serializer.data
            # Include profile for detail view with actual values
            response_data = {
                "id": data["id"],  # Use actual ID
                "profile_id": data["profile_id"],  # Use actual profile_id
                "item_url": data["item_url"],
                "item_type": data["item_type"],
                "description": data["description"],
                "created_at": data["created_at"],
                "updated_at": data["updated_at"],
                "profile": data["profile"]
            }
            return Response(response_data)
        except ObjectDoesNotExist:
            return Response({"message": "Gallery item not found."}, status=status.HTTP_404_NOT_FOUND)

    @extend_schema(
        tags=['user_gallery'],
        summary='Update gallery item',
        description='Update a gallery item',
        request=GalleryItemSerializer,
        responses={
            200: GalleryItemSerializer,
            400: OpenApiTypes.OBJECT,
            403: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
        },
        examples=[
            OpenApiExample(
                'Success Response',
                value={
                    'id': 1,
                    'profile_id': 'profile_uuid',
                    'item_url': 'updated_item_url',
                    'item_type': 'image',
                    'description': 'Updated description',
                    'created_at': '2024-03-20T10:00:00Z',
                    'updated_at': '2024-03-20T10:05:00Z'
                },
                status_codes=['200']
            ),
            OpenApiExample(
                'Validation Error',
                value={
                    'item_type': ['Invalid item type.'],
                    'description': ['This field is required.']
                },
                status_codes=['400']
            )
        ]
    )
    def put(self, request, id):
        """
        Update a specific gallery item by ID.

        Args:
            request (Request): The HTTP request object with updated data.
            id (int): The primary key of the gallery item.

        Returns:
            Response: Success message and updated data or validation errors.
        """
        try:
            item = GalleryItem.objects.get(id=id)
            serializer = GalleryItemSerializer(item, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    "id": str(item.id),  # Use actual ID as string
                    "message": "Gallery item updated successfully.",
                    "updated_at": item.updated_at.isoformat() + "Z"
                }, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except ObjectDoesNotExist:
            return Response({"message": "Gallery item not found."}, status=status.HTTP_404_NOT_FOUND)

    @extend_schema(
        tags=['user_gallery'],
        summary='Delete gallery item',
        description='Delete a gallery item',
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
    def delete(self, request, id):
        """
        Delete a specific gallery item by ID.

        Args:
            request (Request): The HTTP request object.
            id (int): The primary key of the gallery item.

        Returns:
            Response: Success message or a 404 error if not found.
        """
        try:
            item = GalleryItem.objects.get(id=id)
            if item.item_url and os.path.isfile(item.item_url.path):
                os.remove(item.item_url.path)
            item.delete()
            return Response({"message": "Gallery item deleted successfully."})
        except ObjectDoesNotExist:
            return Response({"message": "Gallery item not found."}, status=status.HTTP_404_NOT_FOUND)





