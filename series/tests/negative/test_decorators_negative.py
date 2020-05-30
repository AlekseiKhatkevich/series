from rest_framework.test import APISimpleTestCase

from series.helpers import project_decorators


class DecoratorsNegativeTest(APISimpleTestCase):
    """
    Negative test on a project level custom decorators.
    """

    @project_decorators.typeassert(string=str, integer=int, tup=tuple)
    class TestClass:
        def __init__(self, string: str, integer: int, tup: tuple) -> None:
            self.string = string
            self.integer = integer
            self.tup = tup

    def test_typeassert_wrong_key_message(self):
        """
        Check that after gotten decorated with 'typeassert' decorator , if getter receives non-existing
        attribute -then certain type of exception with messages is arisen.
        """
        kwargs = dict(string='test', integer=228, tup=(1, 2))
        instance = self.TestClass(**kwargs)
        wrong_arg = 'wrong_arg'
        expected_error_message = f"'{instance.__class__.__name__}' object has no attribute '{wrong_arg}'"

        with self.assertRaisesMessage(AttributeError, expected_error_message):
            getattr(instance, wrong_arg)

    def test_type_assert_receives_wrong_type_arg(self):
        """
        Check instance where decorated instance receives wrong type of argument.
        """
        kwargs = dict(string='test', integer=228, tup=2.3)
        expected_error_message = \
            f'Expected type {str(tuple)}. Instead have gotten type {str(type(2.3))}'

        with self.assertRaisesMessage(TypeError, expected_error_message):
            self.TestClass(**kwargs)