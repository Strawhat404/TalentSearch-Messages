from rest_framework import permissions

class CanVerifyProfiles(permissions.BasePermission):
    """
    Custom permission to only allow users with verify_profiles permission to verify profiles.
    """
    def has_permission(self, request, view):
        return request.user.has_perm('userprofile.verify_profiles')

class CanViewVerificationLogs(permissions.BasePermission):
    """
    Custom permission to only allow users with view_verification_logs permission to view verification logs.
    """
    def has_permission(self, request, view):
        return request.user.has_perm('userprofile.view_verification_logs') 