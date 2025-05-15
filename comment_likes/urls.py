from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CommentReactionViewSet

router = DefaultRouter()
router.register(r'reactions', CommentReactionViewSet, basename='comment-reaction')

urlpatterns = [
    path('', include(router.urls)),
]
