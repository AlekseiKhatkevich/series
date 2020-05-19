from rest_framework import permissions, throttling

import users.models
from series import error_codes


class UserIPPermission(permissions.BasePermission):
    """
    Permissions allows only requests that comes from one of account owner 3 last recently used ip addresses.
    Or from admins.
    Or in case user doesnt have any ip entries yet.
    """
    message = error_codes.SUSPICIOUS_REQUEST.message

    def has_permission(self, request, view):
        is_admin = permissions.IsAdminUser().has_permission(request, view)

        try:
            user_email = request.data['email']
        except KeyError:
            self.message = error_codes.EMAIL_REQUIRED.message
            return False

        user_ip_address = throttling.BaseThrottle().get_ident(request)
        user_ips_in_db = \
            users.models.UserIP.objects.filter(user__email=user_email).values_list('ip', flat=True)

        return any((is_admin, not user_ips_in_db, user_ip_address in user_ips_in_db))
