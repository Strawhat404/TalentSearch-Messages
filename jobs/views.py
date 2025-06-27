"""
API views for managing jobs using Django REST Framework.
Handles listing, creating, retrieving, updating, and deleting jobs.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import UserRateThrottle  # Import for default throttling
from .models import Job, Application
from .serializers import JobSerializer, ApplicationSerializer
from django.utils import timezone
from userprofile.models import Profile

class JobListCreateView(APIView):
    """
    API view for listing and creating jobs for the authenticated user.
    """
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]  # Apply default UserRateThrottle (1000/day)

    def get(self, request):
        """
        Fetch all non-expired jobs for all users.
        Returns a list of serialized job data.
        """
        current_date = timezone.now().date()
        jobs = Job.objects.filter(project_end_date__gte=current_date).order_by('created_at')
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
    throttle_classes = [UserRateThrottle]  # Apply default UserRateThrottle (1000/day)

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
        Retrieve a specific job by ID for any authenticated user.
        Returns serialized job data with applicant_count only if the user is the job creator,
        or a 404 error if the job does not exist.
        """
        try:
            job = Job.objects.get(id=job_id)
        except Job.DoesNotExist:
            return Response({"message": "Job not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = JobSerializer(job)
        response_data = serializer.data

        # Hide applicant_count if the user is not the job creator
        if job.user_id != request.user:
            response_data.pop('applicant_count', None)

        return Response(response_data, status=status.HTTP_200_OK)

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

class JobApplyView(APIView):
    """
    API view for applying to a specific job.
    """
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]  # Apply default UserRateThrottle (1000/day)

    def post(self, request, job_id):
        """
        Apply to a job with an opportunity description (cover letter).
        Returns a success message or error if validation fails.
        """
        job = Job.objects.filter(id=job_id).first()
        if not job:
            return Response({"message": "Job not found."}, status=status.HTTP_404_NOT_FOUND)

        # Validate job end date
        current_date = timezone.now().date()
        if job.project_end_date and job.project_end_date < current_date:
            return Response({"error": "Job has expired"}, status=status.HTTP_400_BAD_REQUEST)

        # Prevent the job creator from applying
        if job.user_id == request.user:
            return Response({"error": "You cannot apply to your own job."}, status=status.HTTP_400_BAD_REQUEST)

        # Check for existing application by the same user
        if Application.objects.filter(user=request.user, job=job).exists():
            return Response({"error": "You have already applied to this job."}, status=status.HTTP_400_BAD_REQUEST)

        # Validate opportunity description
        opportunity_description = request.data.get('opportunity_description')
        if not opportunity_description or not str(opportunity_description).strip():
            return Response({"error": "Opportunity description is missing"}, status=status.HTTP_400_BAD_REQUEST)

        # Create application
        Application.objects.create(
            user=request.user,
            job=job,
            opportunity_description=opportunity_description
        )

        return Response({"message": "Application submitted successfully"}, status=status.HTTP_201_CREATED)

class JobApplicantsView(APIView):
    """
    API view for retrieving applicants for a specific job.
    """
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]  # Apply default UserRateThrottle (1000/day)

    def get(self, request, job_id):
        """
        Retrieve a list of applicants for the specified job.
        Returns applicant data including name, applied_at, and opportunity_description.
        """
        job = Job.objects.filter(id=job_id).first()
        if not job:
            return Response({"message": "Job not found."}, status=status.HTTP_404_NOT_FOUND)

        # Check if the requesting user is the job poster
        if job.user_id != request.user:
            return Response({"message": "Unauthorized access."}, status=status.HTTP_403_FORBIDDEN)

        applicants = Application.objects.filter(job_id=job_id).select_related('user').prefetch_related('user__profile')
        serializer = ApplicationSerializer(applicants, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)