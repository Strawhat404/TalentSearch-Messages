from django.urls import path
from .views import JobListCreateView, JobDetailView

urlpatterns = [
    path('', JobListCreateView.as_view(), name='job-list-create'),
    path('<int:job_id>/', JobDetailView.as_view(), name='job-detail'),
]