import imagehash
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.db.models.fields.files import ImageFieldFile
from drf_extra_fields.fields import DateRangeField
from psycopg2.extras import DateRange

from archives.helpers.custom_fields import ImageHashField


class CustomEncoder(DjangoJSONEncoder):
    """
    Encoder to support daterange, ImageField, Image hash and interrelationship serialization to JSON.
    """
    daterange_handler = DateRangeField()
    image_hash_handler = ImageHashField()

    def default(self, o):
        if isinstance(o, DateRange):
            return self.daterange_handler.to_representation(o)
        elif isinstance(o, models.Model):
            return o.pk
        elif isinstance(o, ImageFieldFile):
            return o.__str__()
        elif isinstance(o, imagehash.ImageHash):
            return self.image_hash_handler.get_prep_value(o)
        else:
            return super().default(o)