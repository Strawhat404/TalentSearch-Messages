from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiParameter
from .models import Profile
from .serializers import ProfileSerializer

class ProfileViewSet(viewsets.ModelViewSet):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    @extend_schema(
        tags=['profiles'],
        summary="List profiles",
        description="Retrieve a list of all profiles with optional profession filter",
        parameters=[
            OpenApiParameter(
                name='profession',
                type=str,
                description='Filter profiles by profession'
            )
        ],
        responses={200: ProfileSerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        tags=['profiles'],
        summary="Create profile",
        description="Create a new user profile",
        request=ProfileSerializer,
        responses={201: ProfileSerializer}
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(
        tags=['profiles'],
        summary="Get profile details",
        description="Retrieve details of a specific profile",
        responses={200: ProfileSerializer, 404: None}
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        tags=['profiles'],
        summary="Update profile",
        description="Update details of a specific profile",
        request=ProfileSerializer,
        responses={200: ProfileSerializer, 404: None}
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(
        tags=['profiles'],
        summary="Delete profile",
        description="Delete a specific profile",
        responses={204: None, 404: None}
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    def get_queryset(self):
        queryset = Profile.objects.all()
        profession = self.request.query_params.get('profession', None)
        if profession:
            queryset = queryset.filter(profession__icontains=profession)
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @extend_schema(
        tags=['profiles'],
        summary="Get my profile",
        description="Retrieve the profile of the authenticated user",
        responses={200: ProfileSerializer, 404: None}
    )
    @action(detail=True, methods=['get'])
    def my_profile(self, request, pk=None):
        profile = get_object_or_404(Profile, user=request.user)
        serializer = self.get_serializer(profile)
        return Response(serializer.data) 