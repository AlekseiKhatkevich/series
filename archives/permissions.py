import guardian.models
from django.db.models import Q
from django.utils import timezone
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
        if super().has_object_permission(request, view, obj):
            return True
        else:
            is_master = request.user == obj.entry_author.master
            is_slave = request.user.master == obj.entry_author
            return is_master or is_slave


class FriendsGuardianPermission(permissions.IsAuthenticated):
    """
    Permission class allows users with certain permissions access API endpoint. Based on Guardian
    permissions backend.
    """
    message = error_codes.NO_GUARDIAN_PERMISSION.message
    permission_code = constants.DEFAULT_OBJECT_LEVEL_PERMISSION_CODE

    def generate_condition(self, request, obj) -> dict:
        """
        Generates condition for queryset filter.
        """
        condition = dict(
            object_pk=obj.pk,
            content_type__model=obj.__class__.__name__.lower(),
            content_type__app_label=obj.__class__._meta.app_label.lower(),
            user=request.user,
            permission__codename=self.permission_code,
        )
        return condition

    def has_object_permission(self, request, view, obj):
        """
        Checks if user has guardian permission on object itself or on object's series.
        Either one is sufficiently enough to get an access.
        """
        principal_condition = Q(**self.generate_condition(request, obj))

        try:
            # We might have 'series' as view namespace attribute as well. Need not to fetch it from DB.
            series = getattr(view, 'series', None) or obj.series
            condition = principal_condition | Q(**self.generate_condition(request, series))
        except AttributeError:
            condition = principal_condition

        return guardian.models.UserObjectPermission.objects.filter(condition).exists()


class HandleDeletedUsersEntriesPermission(permissions.BasePermission):
    """
    Allows users who have specific group permission work with entries of a soft-deleted users
    after certain timedelta since they have been soft-deleted.
    """
    time_fringe = constants.DAYS_ELAPSED_SOFT_DELETED_USER
    group_permission_code = constants.HANDLE_DELETED_USERS_GROUP
    now = timezone.now()

    def has_object_permission(self, request, view, obj):
        author = obj.entry_author
        if not author.deleted_time:
            return False

        #  If user has soft-deleted for more then half-year and does not have master o slaves alive.
        if author.deleted and (self.now - author.deleted_time).days > self.time_fringe and \
                not author.have_slaves_or_master_alive:
            return request.user.is_staff or \
                   request.user.groups.filter(name=self.group_permission_code).exists()

        return False
