from typing import Optional

from django.core import exceptions
from django.db.utils import IntegrityError
from django.http.response import HttpResponseBase
from django.views import View
from rest_framework import status
from rest_framework.response import Response as DRF_response
from rest_framework.views import exception_handler


def custom_exception_handler(exc: Exception, context: View) -> Optional[HttpResponseBase]:
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
    Returns None in case exception wasn't handled in this handler or it's superclass or DRF Response
    in case exception was handled.
    """
    response = exception_handler(exc, context)

    if isinstance(exc, (exceptions.ValidationError,)):
        data = exc.message_dict
        return DRF_response(data=data, status=status.HTTP_400_BAD_REQUEST, )
    # elif isinstance(exc,  IntegrityError,):
    #     data = str(exc)
    #     return DRF_response(data=data, status=status.HTTP_400_BAD_REQUEST, )

    return response
