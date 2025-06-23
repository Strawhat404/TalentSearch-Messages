from django.urls import path
from .views import JobListCreateView, JobDetailView, JobApplyView, JobApplicantsView

urlpatterns = [
    path('', JobListCreateView.as_view(), name='job-list-create'),
    path('<int:job_id>/', JobDetailView.as_view(), name='job-detail'),
    path('<int:job_id>/apply/', JobApplyView.as_view(), name='job-apply'),
    path('<int:job_id>/applicants/', JobApplicantsView.as_view(), name='job-applicants'),
]
