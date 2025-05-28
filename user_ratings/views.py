from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Avg, Count
from django.db.models.functions import Coalesce
from .models import UserRating
from .serializers import UserRatingSerializer, UserRatingUpdateSerializer
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.core.exceptions import ValidationError

User = get_user_model()

class UserRatingCreateListView(APIView):
    def post(self, request):
        """
        Create a new user rating, preventing duplicate ratings for the same user pair.
        """
        serializer = UserRatingSerializer(data=request.data)
        if serializer.is_valid():
            try:
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except IntegrityError:
                return Response(
                    {"error": "You have already rated this user. Please update the existing rating."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        """
        Get ratings for a specific user with optional filtering and sorting.
        Query parameters: rated_user_id (required), min_rating, sort, limit.
        """
        rated_user_id = request.query_params.get('rated_user_id')
        if not rated_user_id:
            return Response({"error": "rated_user_id is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            rated_user_id = int(rated_user_id)
            if not User.objects.filter(id=rated_user_id).exists():
                return Response({"error": "rated_user_id does not exist."}, status=status.HTTP_404_NOT_FOUND)
        except ValueError:
            return Response({"error": "rated_user_id must be an integer."}, status=status.HTTP_400_BAD_REQUEST)

        queryset = UserRating.objects.filter(rated_user_id=rated_user_id)

        # Filter by min_rating
        min_rating = request.query_params.get('min_rating')
        if min_rating:
            try:
                min_rating = int(min_rating)
                if min_rating < 1 or min_rating > 5:
                    raise ValueError
                queryset = queryset.filter(rating__gte=min_rating)
            except ValueError:
                return Response({"error": "min_rating must be an integer between 1 and 5."},
                                status=status.HTTP_400_BAD_REQUEST)

        # Sort by sort parameter
        sort = request.query_params.get('sort', 'newest')
        if sort == 'newest':
            queryset = queryset.order_by('-created_at')
        elif sort == 'highest':
            queryset = queryset.order_by('-rating', '-created_at')
        elif sort == 'lowest':
            queryset = queryset.order_by('rating', '-created_at')
        else:
            return Response({"error": "sort must be 'newest', 'highest', or 'lowest'."},
                            status=status.HTTP_400_BAD_REQUEST)

        # Limit results
        limit = request.query_params.get('limit')
        if limit:
            try:
                limit = int(limit)
                if limit <= 0:
                    raise ValueError
                queryset = queryset[:limit]
            except ValueError:
                return Response({"error": "limit must be a positive integer."}, status=status.HTTP_400_BAD_REQUEST)

        # Calculate average rating and total ratings
        stats = queryset.aggregate(
            average_rating=Coalesce(Avg('rating'), 0.0),
            total_ratings=Count('id')
        )
        average_rating = round(stats['average_rating'], 1) if stats['average_rating'] else 0.0
        total_ratings = stats['total_ratings']

        # Serialize ratings
        serializer = UserRatingSerializer(queryset, many=True)

        response_data = {
            'average_rating': average_rating,
            'total_ratings': total_ratings,
            'ratings': serializer.data
        }
        return Response(response_data, status=status.HTTP_200_OK)

class UserRatingUpdateDeleteView(APIView):
    def put(self, request, id):
        """
        Update an existing rating by ID.
        """
        try:
            rating = UserRating.objects.get(id=id)
        except UserRating.DoesNotExist:
            return Response({"error": "Rating not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = UserRatingUpdateSerializer(rating, data=request.data, partial=True)
        if serializer.is_valid():
            try:
                # Manually update rating and feedback to bypass model's save method
                UserRating.objects.filter(id=id).update(
                    rating=serializer.validated_data.get('rating', rating.rating),
                    feedback=serializer.validated_data.get('feedback', rating.feedback)
                )
                # Refresh the rating object to get updated_at
                rating.refresh_from_db()
                return Response({
                    'id': rating.id,
                    'message': 'Rating updated successfully',
                    'updated_at': rating.updated_at.isoformat()
                }, status=status.HTTP_200_OK)
            except ValidationError as e:
                # Handle any unexpected validation errors
                error_message = str(e)
                return Response(
                    {"non_field_errors": [error_message]},
                    status=status.HTTP_400_BAD_REQUEST
                )
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id):
        """
        Delete a rating by ID.
        """
        try:
            rating = UserRating.objects.get(id=id)
            rating.delete()
            return Response({"message": "Rating deleted successfully"}, status=status.HTTP_200_OK)
        except UserRating.DoesNotExist:
            return Response({"error": "Rating not found."}, status=status.HTTP_404_NOT_FOUND)

# Keep UserRatingSummaryView unchanged
class UserRatingSummaryView(APIView):
    def get(self, request):
        """
        Get rating summary for a specific user.
        Query parameter: user_id (required).
        """
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response({"error": "user_id is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user_id = int(user_id)
            if not User.objects.filter(id=user_id).exists():
                return Response({"error": "user_id does not exist."}, status=status.HTTP_404_NOT_FOUND)
        except ValueError:
            return Response({"error": "user_id must be an integer."}, status=status.HTTP_400_BAD_REQUEST)

        queryset = UserRating.objects.filter(rated_user_id=user_id)
        stats = queryset.aggregate(
            average_rating=Coalesce(Avg('rating'), 0.0),
            total_ratings=Count('id')
        )
        average_rating = round(stats['average_rating'], 1) if stats['average_rating'] else 0.0
        total_ratings = stats['total_ratings']

        # Calculate rating distribution
        rating_distribution = {
            str(i): queryset.filter(rating=i).count() for i in range(1, 6)
        }

        # Get last rating
        last_rating = queryset.order_by('-created_at').first()
        last_rating_data = None
        if last_rating:
            last_rating_data = {
                'rating': last_rating.rating,
                'feedback': last_rating.feedback,
                'created_at': last_rating.created_at.isoformat()
            }

        response_data = {
            'user_id': user_id,
            'average_rating': average_rating,
            'total_ratings': total_ratings,
            'rating_distribution': rating_distribution,
            'last_rating': last_rating_data
        }
        return Response(response_data, status=status.HTTP_200_OK)