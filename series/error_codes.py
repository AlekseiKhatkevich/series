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
EMAIL_REQUIRED = exc_msg(
    'Field "email" is required. Please fill it.',
    'email_required',
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
    'master_of_self',
)
SUSPICIOUS_REQUEST = exc_msg(
    'Suspicious request from unknown ip.',
    'suspicious_request',
)
READ_ONLY = exc_msg(
    'This field is read only.',
    'read_only',
)
USER_SOFT_DELETED = exc_msg(
    f'User with this email is soft-deleted. Consider to undelete his account rather then create new one.',
    'user_soft_deleted',
)
SOFT_DELETED_DENIED = exc_msg(
    'Access to soft-deleted users is denied',
    'soft_deleted_denied',
)
NOT_SOFT_DELETED = exc_msg(
    'This user is not deleted. You can not undelete him.',
    'not_soft_deleted',
)
USER_IS_DELETED = exc_msg(
    'User is deleted.',
    'user_is_deleted',
)
ONLY_MASTERS_ALLOWED = exc_msg(
    'Access is allowed only to masters.',
    'only_masters_allowed',
)

NOT_YOUR_SLAVE = exc_msg(
    'This email does not belong to your slave account or this is not a slave account at all.',
    'not_your_slave',
)
INTERRELATIONSHIP_ON_SELF = exc_msg(
    'Series can not have interrelationship on itself.',
    'interrelationship_on_self',
)
WRONG_PATH = exc_msg(
    'Path does not exists or this is a file but not a folder',
    'wrong_path',
)
NOT_IN_TESTS = exc_msg(
    'This function or method is not applicable in tests',
    'not_in_tests',
)
NOT_A_BINARY = exc_msg(
    'This api endpoint only accepts binary file transmission. No multipart or JSON, sorry.',
    'not_a_binary'
)
ONLY_AUTHORS = exc_msg(
    'Only authors of this entry are allowed to make this action.',
    'only_authors'
)
ONLY_SLAVES_AND_MASTER = exc_msg(
    'Only slaves or master of the entry creator and entry creator himself are allowed to make this action.',
    'only_slaves_and_master'
)
NOT_AN_IMAGE = exc_msg(
    'This file is not an image.',
    'not_an-image'
)
IMAGE_NOT_EXISTS = exc_msg(
    'Image matching given pk does not exists.',
    'image_not_exists',
)


