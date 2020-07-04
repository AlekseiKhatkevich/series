import collections
import datetime

exc_msg = collections.namedtuple('exception_description', ['message', 'code'])

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
READ_ONLY_FIELD = exc_msg(
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
IMAGE_ALREADY_EXISTS = exc_msg(
    'This image is already exists in the database.',
    'image_already_exists',
)
NO_GUARDIAN_PERMISSION = exc_msg(
    'You do not have necessary permission from object creator to modify this object.',
    'no_guardian_permission',
)
READ_ONLY_ACTION = exc_msg(
    'As you dont have all necessary permissions - this endpoint is read only for you.',
    'read_only_action',
)
DRF_NO_AUTH = exc_msg(
    'Authentication credentials were not provided.',
    'no_auth_403',
)
DRF_NO_PERMISSIONS = exc_msg(
    'You do not have permission to perform this action.',
    'drf_no_permissions',
)
LOWER_BOUND = exc_msg(
    'Range should have lower bound.',
    'lower_bound',
)
UPPER_BOUND = exc_msg(
    'Range should have upper bound.',
    'upper_bound',
)
LOWER_GT_UPPER = exc_msg(
    'Upper bound should be gte. than lower one.',
    'lower_gt_upper',
)
INCORRECT_LOWER_BOUND = exc_msg(
    f'Lower bound should be greater than Lumiere brothers film release date and lower then '
    f'{datetime.datetime.now().year + 1}, December 31, inclusive.',
    'incorrect_lower_bound',
)
INCORRECT_UPPER_BOUND = exc_msg(
    f'Maximal future allowed year is {datetime.datetime.now().year + 1}, December 31, inclusive.',
    'incorrect_upper_bound',
)
NOT_DATETIME = exc_msg(
    "Value should be datetime or date type or it's subclass or None.",
    'no_datetime',
)
LAST_WATCHED_GTE_NUM_EPISODES = exc_msg(
    'Last watched episode number is greater then number of episodes.',
    'last_watched_gte_num_episodes',
)
MAX_KEY_GT_NUM_EPISODES = exc_msg(
    'Episode with maximal number in "episodes field is greater then number of episodes.',
    'max_key_gt_num_episodes',
)
EPISODES_DATES_NOT_SORTED = exc_msg(
    'Episodes dates should be gte each other in succession.',
    'episodes_dates_not_sorted',
)
