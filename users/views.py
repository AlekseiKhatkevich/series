import djoser.views
from djoser.conf import settings as djoser_settings
from djoser.compat import get_user_email

from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status


class CustomDjoserUserViewSet(djoser.views.UserViewSet):
    """
    Custom viewset based on Djoser viewset.
    """

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.prefetch_related('slaves')

    @action(['post'], detail=False)
    def set_slaves(self, request, *args, **kwargs):
        """
        Action for attaching slave account to a master account.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # Send activation email to slave.
        if djoser_settings.SEND_ACTIVATION_EMAIL:
            slave = serializer.slave
            context = {'slave': slave, 'master': request.user}
            to = [get_user_email(slave)]
            djoser_settings.EMAIL.slave_activation(self.request, context).send(to)
        else:  # Just attach slave to master directly without confirmation from slave's part.
            serializer.save()

        return Response(status=status.HTTP_202_ACCEPTED)

    def get_permissions(self):
        if self.action == 'set_slaves':
            self.permission_classes = djoser_settings.PERMISSIONS.set_slaves
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action == 'set_slaves':
            return djoser_settings.SERIALIZERS.set_slaves
        return super().get_serializer_class()
