from django.core.exceptions import ValidationError


def skip_if_none_none_zero_positive_validator(value: int) -> None:
    """
    Raises Validation error in case value is les then 1. Skips if value is None.
    Useful when field can hold none as a legit value
    """
    if value is None:
        return None
    elif value < 1:
        raise ValidationError(
            f'{value} must be greater or equal 1'
        )
