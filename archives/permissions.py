from rest_framework import permissions

from series import error_codes


class IsObjectOwner(permissions.BasePermission):
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
    message = (IsObjectOwner.message,
               error_codes.ONLY_SLAVES_AND_MASTER.message
               )

    def has_object_permission(self, request, view, obj):
        is_master = request.user == obj.entry_author.master
        is_slave = request.user.master == obj.entry_author
        return super().has_object_permission(request, view, obj) or is_master or is_slave
