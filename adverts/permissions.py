from rest_framework import permissions
from django.utils import timezone


class IsAdvertOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an advert to modify it.
    Unauthenticated users can only read published adverts.
    """
    
    def has_permission(self, request, view):
        # Allow GET requests for everyone
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Require authentication for modification operations
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Allow read access for everyone to published adverts
        if request.method in permissions.SAFE_METHODS:
            # For unauthenticated users, only show published adverts that are currently running
            if not request.user.is_authenticated:
                now = timezone.now()
                return (obj.status == 'published' and 
                       obj.run_from and obj.run_from <= now and 
                       obj.run_to and obj.run_to >= now)
            # Authenticated users can see all adverts
            return True
        
        # For modification operations, only the creator can modify
        return obj.created_by == request.user


class IsAuthenticatedForModification(permissions.BasePermission):
    """
    Permission class that allows public read access but requires authentication for modifications.
    """
    
    def has_permission(self, request, view):
        # Allow GET requests for everyone
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Require authentication for modification operations
        return request.user and request.user.is_authenticated
 