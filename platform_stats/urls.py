from django.urls import path
from .views import RolesView, MembersView, CreatorsView, SatisfiedView

urlpatterns = [
    path('roles/', RolesView.as_view(), name='statistics_roles'),
    path('members/', MembersView.as_view(), name='statistics_members'),
    path('creators/', CreatorsView.as_view(), name='statistics_creators'),
    path('satisfied/', SatisfiedView.as_view(), name='statistics_satisfied'),
]