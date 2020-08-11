import django.core.checks


@django.core.checks.register('rest_framework.serializers')
def check_serializers(app_configs, **kwargs):
    import inspect
    from rest_framework.serializers import ModelSerializer
    import django.conf.urls  # noqa, force import of all serializers.

    for serializer in ModelSerializer.__subclasses__():

        # Skip third-party apps.
        path = inspect.getfile(serializer)
        if path.find('site-packages') > -1:
            continue

        if hasattr(serializer.Meta, 'read_only_fields'):
            continue

        yield django.core.checks.Warning(
            'ModelSerializer must define read_only_fields.',
            hint='Set read_only_fields in ModelSerializer.Meta',
            obj=serializer,
            id='H300',
        )