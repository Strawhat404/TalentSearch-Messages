from rest_framework import generics, status
from rest_framework.response import Response
from .models import Advert
from .serializers import AdvertSerializer

class AdvertListCreateView(generics.ListCreateAPIView):
    queryset = Advert.objects.all()
    serializer_class = AdvertSerializer

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