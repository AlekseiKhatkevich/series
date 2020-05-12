import djoser.views
from djoser.conf import settings


class CustomDjoserUserViewSet(djoser.views.UserViewSet):

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()
        if settings.HIDE_USERS and self.action == "list" and not user.is_staff:
            queryset = queryset.filter(pk=user.pk)
        return queryset.prefetch_related('slaves')



