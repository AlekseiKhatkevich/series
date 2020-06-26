import guardian.models
from rest_framework import permissions

from series import constants, error_codes


class ReadOnlyIfOnlyAuthenticated(permissions.BasePermission):
    """
    Permission allows any authenticated user read api but not change it.
    """
    message = error_codes.READ_ONLY_ACTION.message

    def has_permission(self, request, view):
        return request.user.is_authenticated and (request.method in permissions.SAFE_METHODS)

    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)


class IsObjectOwner(permissions.IsAuthenticated):
    """
    Permission allows to enter only to authors of an entry.
    """
    message = error_codes.ONLY_AUTHORS.message

    def has_object_permission(self, request, view, obj):
        return obj.entry_author == request.user


class MasterSlaveRelations(IsObjectOwner):
    """
    Permission that allows users and  master - salve relations with each other access an api endpoint.
    """
    message = error_codes.ONLY_SLAVES_AND_MASTER.message

    def has_object_permission(self, request, view, obj):
        is_master = request.user == obj.entry_author.master
        is_slave = request.user.master == obj.entry_author
        return super().has_object_permission(request, view, obj) or is_master or is_slave


class FriendsGuardianPermission(permissions.IsAuthenticated):
    """
    Permission class allows users with certain permissions access API endpoint. Based on Guardian
    permissions backend.
    """
    message = error_codes.NO_GUARDIAN_PERMISSION.message
    permission_code = constants.DEFAULT_OBJECT_LEVEL_PERMISSION_CODE

    def has_object_permission(self, request, view, obj):
        return guardian.models.UserObjectPermission.objects.filter(
            object_pk=obj.pk,
            content_type__model=obj.__class__.__name__.lower(),
            content_type__app_label=obj.__class__._meta.app_label.lower(),
            user=request.user,
            permission__codename=self.permission_code,
        ).exists()

