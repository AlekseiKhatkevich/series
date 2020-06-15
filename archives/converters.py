class CommaSeparatedIntegersPathConverter:
    """
    Converts comma separated integers to python list and other way around.
    Example:
        catches group 351,353 from url archives/tvseries/129/delete-image/351,353/
    """
    regex = r'(?<=/)\d+(?:,\d+)*(?=/?$)'

    @staticmethod
    def to_python(value):
        return tuple(int(v) for v in value.split(','))

    @staticmethod
    def to_url(value):
        return ','.join(map(str, value))




