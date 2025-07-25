from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import UserRateThrottle
from .models import Job, Application
from .serializers import JobSerializer, ApplicationSerializer
from django.utils import timezone
from userprofile.models import Profile
from authapp.services import notify_new_job_posted
from django.http import Http404
from django.core.exceptions import ObjectDoesNotExist

class JobListCreateView(APIView):
    """
    API view for listing and creating jobs for the authenticated user.
    """
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    def get(self, request):
        """
        Fetch all non-expired jobs for all users.
        Returns a list of serialized job data.
        """
        current_date = timezone.now().date()
        if request.user.is_superuser or request.user.is_staff:
            jobs = Job.objects.all().order_by('-created_at')
        else:
            jobs = Job.objects.filter(project_end_date__gte=current_date).order_by('-created_at')
        serializer = JobSerializer(jobs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        """
        Create a new job for the authenticated user.
        Returns the job ID and success message or validation errors.
        """
        try:
            profile = request.user.profile
        except ObjectDoesNotExist:
            return Response({"error": "You must create a profile before posting a job."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = JobSerializer(data=request.data)
        if serializer.is_valid():
            job = serializer.save(profile_id=profile)
            notify_new_job_posted(job)
            response_data = {
                "id": job.id,
                "message": "Job created successfully."
            }
            return Response(response_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class JobDetailView(APIView):
    """
    API view for retrieving, updating, and deleting a specific job.
    """
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    def get_object(self, job_id, user_profile):
        """
        Helper method to get a job by ID for the authenticated user's profile.
        Returns the job instance or None if not found.
        """
        try:
            return Job.objects.get(id=job_id, profile_id__user=user_profile)
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
            raise Http404("Job not found.")

        serializer = JobSerializer(job)
        response_data = serializer.data

        if job.profile_id and job.profile_id.user != request.user:
            response_data.pop('applicant_count', None)

        return Response(response_data, status=status.HTTP_200_OK)

    def put(self, request, job_id):
        """
        Update a specific job, only allowed for the creator or an admin.
        Returns the job ID and success message or validation errors.
        """
        try:
            job = Job.objects.get(id=job_id)
        except Job.DoesNotExist:
            raise Http404("Job not found.")

        if not (job.profile_id and job.profile_id.user == request.user):
            return Response({"message": "You are not authorized to update this job."}, status=status.HTTP_403_FORBIDDEN)
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
        Delete a specific job, only allowed for the creator or an admin.
        Returns a success message or a 404/403 error if not found or unauthorized.
        """
        try:
            job = Job.objects.get(id=job_id)
        except Job.DoesNotExist:
            raise Http404("Job not found.")

        if not (request.user.is_superuser or request.user.is_staff or (job.profile_id and job.profile_id.user == request.user)):
            return Response({"message": "You are not authorized to delete this job."}, status=status.HTTP_403_FORBIDDEN)
        job.delete()
        return Response({"message": "Job deleted successfully."}, status=status.HTTP_200_OK)

class JobApplyView(APIView):
    """
    API view for applying to a specific job.
    """
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    def post(self, request, job_id):
        """
        Apply to a job with an opportunity description (cover letter).
        Returns a success message or error if validation fails.
        """
        job = Job.objects.filter(id=job_id).first()
        if not job:
            raise Http404("Job not found.")

        current_date = timezone.now().date()
        if job.project_end_date and job.project_end_date < current_date:
            return Response({"error": "Job has expired"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            profile = request.user.profile
        except ObjectDoesNotExist:
            return Response({"error": "You must create a profile before applying for a job."}, status=status.HTTP_400_BAD_REQUEST)

        if job.profile_id and job.profile_id.user == request.user:
            return Response({"error": "You cannot apply to your own job."}, status=status.HTTP_400_BAD_REQUEST)

        if Application.objects.filter(profile_id__user=request.user, job=job).exists():
            return Response({"error": "You have already applied to this job."}, status=status.HTTP_400_BAD_REQUEST)

        opportunity_description = request.data.get('opportunity_description')
        if not opportunity_description or not str(opportunity_description).strip():
            return Response({"error": "Opportunity description is missing"}, status=status.HTTP_400_BAD_REQUEST)

        Application.objects.create(
            profile_id=profile,
            job=job,
            opportunity_description=opportunity_description
        )

        return Response({"message": "Application submitted successfully"}, status=status.HTTP_201_CREATED)

class JobApplicantsView(APIView):
    """
    API view for retrieving applicants for a specific job.
    """
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    def get(self, request, job_id):
        """
        Retrieve a list of applicants for the specified job.
        Returns applicant data including name, applied_at, and opportunity_description.
        """
        job = Job.objects.filter(id=job_id).first()
        if not job:
            raise Http404("Job not found.")

        if not job.profile_id or job.profile_id.user != request.user:
            return Response({"message": "Unauthorized access."}, status=status.HTTP_403_FORBIDDEN)

        applicants = Application.objects.filter(job_id=job_id).select_related('profile_id')
        serializer = ApplicationSerializer(applicants, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)