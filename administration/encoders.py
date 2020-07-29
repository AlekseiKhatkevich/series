from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.db.models.fields.files import ImageFieldFile
from drf_extra_fields.fields import DateRangeField
from psycopg2.extras import DateRange


class CustomEncoder(DjangoJSONEncoder):
    """
    Encoder to support daterange, ImageFieldFile and interrelationship serialization to JSON.
    """
    daterange_handler = DateRangeField()

    def default(self, o):
        if isinstance(o, DateRange):
            return self.daterange_handler.to_representation(o)
        elif isinstance(o, models.Model):
            return o.pk
        elif isinstance(o, ImageFieldFile):
            return o.__str__()
        else:
            return super().default(o)