from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.response import Response
from rest_framework_simplejwt import exceptions as simplejwt_exceptions

from series import error_codes


class TokenViewBaseMixin:
    """
    Mixin overloads post method from DRF simpleJWT TokenViewBase in order to raise
    validation error on soft-deleted user.
    """

    def __init__(self) -> None:
        super().__init__()
        self.initialized_serializer = None

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        self.initialized_serializer = serializer

        try:
            serializer.is_valid(raise_exception=True)
        except simplejwt_exceptions.TokenError as e:
            raise simplejwt_exceptions.InvalidToken(e.args[0])

        if hasattr(serializer, 'user') and serializer.user.deleted:
            raise ValidationError(
                {'email': error_codes.SOFT_DELETED_DENIED.message},
                code=error_codes.SOFT_DELETED_DENIED.code,
            )

        return Response(serializer.validated_data, status=status.HTTP_200_OK)