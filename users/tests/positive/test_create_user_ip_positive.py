from rest_framework.test import APITestCase

from users.helpers import create_test_ips, create_test_users


class CreateTestIPSPositiveTest(APITestCase):
    """
    Test for script that create set of user IP model entries for tests.
    """

    @classmethod
    def setUpTestData(cls):
        cls.users = create_test_users.create_users()
        cls.user_1, cls.user_2, cls.user_3 = cls.users
        cls.ips = create_test_ips.create_ip_entries(cls.users)

    def test_are_created(self):
        """
        Check that for each user 3 IP model entries has been created.
        """
        for user in self.users:
            with self.subTest(user=user):
                self.assertEqual(
                    user.user_ip.all().count(),
                    3
                )

    def test_random_ip(self):
        """
        Check that we dont have same ip for each entry.
        """
        self.assertCountEqual(
            (ips := [ip.ip for ip in self.ips]),
            set(ips)
        )

    def test_offset_time(self):
        """
        Check that 'sample_time' in each entry is vary.
        """
        self.assertCountEqual(
            (dtms := [ip.sample_time for ip in self.ips]),
            set(dtms)
        )