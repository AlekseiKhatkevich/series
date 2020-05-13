from collections import namedtuple

exc_msg = namedtuple('exception_description', ['message', 'code'])


WRONG_COUNTRY_CODE = exc_msg(
    'Wrong country code. Country code should consist of 2 uppercase letters according ISO 3166',
    'wrong_country_code',
)
USER_DOESNT_EXISTS = exc_msg(
    'User with this email does not exists.',
    'user_doesnt_exists',
)
ZERO_IS_NOT_VALID = exc_msg(
    'Zero is not a valid integer for this field.',
    'zero_is_not_valid',
)
MASTER_FIELDS_REQUIRED = exc_msg(
    'Please provide input data for fields "master_password" and "master_email" or keep both fields empty.',
    'master_fields_required',
)
SLAVE_CANT_HAVE_SALVES = exc_msg(
    "Slave account can't have its own slaves.",
    'slave_cant_have_slave',
)
MASTER_CANT_BE_SLAVE = exc_msg(
    "This slaves's master can not be slave itself.",
    'master_cant_be_slave',
)
REQUIRED_TOGETHER_WRONG_FIELDS_NAMES = exc_msg(
    'In "required_together_fields" you specified a field or fields that are not belong to this exact serializer.',
    'required_together_wrong_fields_names',
)
SLAVE_FIELDS_REQUIRED = exc_msg(
    'Please provide input data for fields "slave_password" and "slave_email".',
    'slave_fields_required',
)
SLAVE_UNAVAILABLE = exc_msg(
    "This user account can't be slave. It either already someone's slave account or master account.",
    'slave_unavailable',
)
MASTER_OF_SELF = exc_msg(
    'Master field can not point to the same user whom it belongs to.',
    'master_of_self'
)


