from django.core import exceptions
from django.db.utils import DatabaseError
from django.http import response
from django.views import View

from rest_framework import status
from rest_framework.response import Response as DRF_response
from rest_framework.views import exception_handler


def custom_exception_handler(exc: Exception, context: View) -> [response, None]:
    """
    Custom exceptions handler.
    Use-case. in case if django Validation error is conjured up (for example by model level validation),
    then standard error display will be changed to DRF-like JSON string, for example:
    {
    "master": [
        "Slave account can't have its own slaves"
    ]
    }
    exc - handled exception object
    context - view object from which response has came.
    """
    response = exception_handler(exc, context)

    if isinstance(exc, (exceptions.ValidationError, DatabaseError)):
        data = exc.message_dict
        return DRF_response(data=data, status=status.HTTP_400_BAD_REQUEST, )

    return response
