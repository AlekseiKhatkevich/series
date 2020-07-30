from django.apps import apps


class ModelNameConverter:
    """
    Converter to parse shortcut model name from url (3 possible choices) and return it as model instance.
    """
    regex = r'(imagemodel|seasonmodel|tvseriesmodel)'

    @staticmethod
    def to_python(value):
        return apps.get_model(app_label='archives', model_name=value)

    @staticmethod
    def to_url(value):
        return value
