from rest_framework.test import APISimpleTestCase

from series.helpers import project_decorators


class DecoratorsPositiveTest(APISimpleTestCase):
    """
    Positive test on a project level custom decorators.
    """

    @project_decorators.typeassert(string=str, integer=int, tup=tuple)
    class TestClass:
        def __init__(self, string: str, integer: int, tup: tuple) -> None:
            self.string = string
            self.integer = integer
            self.tup = tup

    def test_initialize_class_instance_typeassert(self):
        """
        For the decorator 'typeassert'.
        Check that 'get', 'set' and 'delete' methods works fine as well as attributes are defined in
        the class instance
        """
        kwargs = dict(string='test', integer=228, tup=(1, 2))
        instance = self.TestClass(**kwargs)
        # Check that all argument have been set in init.
        self.assertDictEqual(
            instance.__dict__,
            kwargs
        )
        # Check getter.
        self.assertEqual(
            instance.string,
            kwargs['string']
        )
        # Check setter.
        instance.integer = 112

        self.assertEqual(
            instance.integer,
            112
        )
        # Check deleter.
        del instance.tup

        self.assertFalse(
            hasattr(instance, 'tup')
        )

