from django.urls import path
from .views import RolesView, MembersView, CreatorsView, SatisfiedView

urlpatterns = [
    path('api/statistics/roles/', RolesView.as_view(), name='statistics_roles'),
    path('api/statistics/members/', MembersView.as_view(), name='statistics_members'),
    path('api/statistics/creators/', CreatorsView.as_view(), name='statistics_creators'),
    path('api/statistics/satisfied/', SatisfiedView.as_view(), name='statistics_satisfied'),
]