# from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Count
from jobs.models import Job
from userprofile.models import Profile
from rest_framework.permissions import AllowAny

class RolesView(APIView):
    permission_classes = [AllowAny]  # Added to allow token-free access

    def get(self, request):
        # New roles posted in the last 7 days (since 08:07 PM EAT on June 6, 2025)
        seven_days_ago = timezone.now() - timezone.timedelta(days=7)
        new_roles_this_week = Job.objects.filter(created_at__gte=seven_days_ago).count()
        data = {'new_roles_this_week': new_roles_this_week}
        return Response(data, status=status.HTTP_200_OK)

class MembersView(APIView):
    permission_classes = [AllowAny]  # Added to allow token-free access

    def get(self, request):
        # Total number of registered users
        User = get_user_model()
        total_members = User.objects.count()
        data = {'total_members': total_members}
        return Response(data, status=status.HTTP_200_OK)

class CreatorsView(APIView):
    permission_classes = [AllowAny]  # Added to allow token-free access

    def get(self, request):
        # Total number of unique users who posted jobs
        creators_looking_for_talent = Job.objects.values('user_id').distinct().count()
        data = {'creators_looking_for_talent': creators_looking_for_talent}
        return Response(data, status=status.HTTP_200_OK)

class SatisfiedView(APIView):
    permission_classes = [AllowAny]  # Added to allow token-free access

    def get(self, request):
        # Total number of verified profiles
        satisfied_profiles = Profile.objects.filter(verified=True).count()
        data = {'satisfied_profiles': satisfied_profiles}
        return Response(data, status=status.HTTP_200_OK)