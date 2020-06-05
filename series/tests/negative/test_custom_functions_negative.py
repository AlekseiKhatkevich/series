from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from series.helpers import custom_functions


class CustomFunctionsNegativeTest(APITestCase):
    """
    Test for custom functions in series project root.
    """
    def test_get_model_fields_subset(self):
        """
        Check whether or not function 'get_model_fields_subset' raises exception in case incorrect
        app.modelname is provided.
        """
        model = 'fake.model'
        expected_error_message = f'Model with name "model" not found in app "fake".'

        with self.assertRaisesMessage(NameError, expected_error_message):
            custom_functions.get_model_fields_subset(model=model,)
