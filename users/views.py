import djoser.views
from djoser.conf import settings as djoser_settings

from rest_framework.decorators import action


class CustomDjoserUserViewSet(djoser.views.UserViewSet):
    """
    Custom viewset based on Djoser viewset.
    """

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.prefetch_related('slaves')

    @action(['post'], detail=False)
    def set_slaves(self, request, *args, **kwargs):
        pass

    def get_permissions(self):
        if self.action == 'set_slaves':
            self.permission_classes = djoser_settings.PERMISSIONS.set_slaves
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action == 'set_slaves':
            return djoser_settings.SERIALIZERS.set_slaves
        return super().get_serializer_class()






