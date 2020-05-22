from rest_framework import permissions
from series import error_codes


class SoftDeletedUsersDenied(permissions.BasePermission):
    """
    Permission denies access to soft-deleted users.
    """
    message = error_codes.SOFT_DELETED_DENIED.message

    def has_permission(self, request, view):
        return not request.user.deleted
