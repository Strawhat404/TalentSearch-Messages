"""
API views for managing jobs using Django REST Framework.
Handles listing, creating, retrieving, updating, and deleting jobs.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import Job
from .serializers import JobSerializer


class JobListCreateView(APIView):
    """
    API view for listing and creating jobs for the authenticated user.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Fetch all jobs for the authenticated user.
        Returns a list of serialized job data.
        """
        jobs = Job.objects.filter(user_id=request.user)
        serializer = JobSerializer(jobs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        """
        Create a new job for the authenticated user.
        Returns the job ID and success message or validation errors.
        """
        serializer = JobSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user_id=request.user)
            response_data = {
                "id": serializer.data['id'],
                "message": "Job created successfully."
            }
            return Response(response_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class JobDetailView(APIView):
    """
    API view for retrieving, updating, and deleting a specific job.
    """
    permission_classes = [IsAuthenticated]

    def get_object(self, job_id, user):
        """
        Helper method to get a job by ID for the authenticated user.
        Returns the job instance or None if not found.
        """
        try:
            return Job.objects.get(id=job_id, user_id=user)
        except Job.DoesNotExist:
            return None

    def get(self, request, job_id):
        """
        Retrieve a specific job by ID for the authenticated user.
        Returns serialized job data or a 404 error if not found.
        """
        job = self.get_object(job_id, request.user)
        if not job:
            return Response({"message": "Job not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = JobSerializer(job)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, job_id):
        """
        Update a specific job.
        Returns the job ID and success message or validation errors.
        """
        job = self.get_object(job_id, request.user)
        if not job:
            return Response({"message": "Job not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = JobSerializer(job, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            response_data = {
                "id": job.id,
                "message": "Job updated successfully."
            }
            return Response(response_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, job_id):
        """
        Delete a specific job.
        Returns a success message or a 404 error if not found.
        """
        job = self.get_object(job_id, request.user)
        if not job:
            return Response({"message": "Job not found."}, status=status.HTTP_404_NOT_FOUND)
        job.delete()
        return Response({"message": "Job deleted successfully."}, status=status.HTTP_200_OK)