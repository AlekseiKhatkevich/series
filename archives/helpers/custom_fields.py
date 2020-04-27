from django.contrib.postgres import fields as postgres_fields


class CustomJSONField(postgres_fields.JSONField):
    """
    Custom JSON field with modified 'empty_values' that would allow to store Null(none)and empty dict.
    https://stackoverflow.com/questions/55147169/django-admin-jsonfield-default-empty-dict-wont-save-in-admin
    """
    empty_values = ('', [], (), )
