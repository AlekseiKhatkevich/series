
class ModelNameConverter:
    """
    Converter to parse shortcut model name from url (3 possible choices) and return it.
    """
    regex = r'(imagemodel|seasonmodel|tvseriesmodel)'

    @staticmethod
    def to_python(value):
        return value

    @staticmethod
    def to_url(value):
        return value
