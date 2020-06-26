from rest_framework.test import APITestCase
from rest_framework.reverse import reverse

from users.helpers import create_test_users
import archives.models as archive_models
from archives.tests.data import initial_data


class TvSeriesModelPositiveTest(APITestCase):
    """
    Test for positive functionality of 'TvSeriesModel' in 'archives' app.
    """

    @classmethod
    def setUpTestData(cls):
        cls.users = create_test_users.create_users()
        cls.user_1, cls.user_2, cls.user_3 = cls.users

        cls.series_initial_data = {'entry_author': cls.user_1,
                                   'name': 'Fargo',
                                   'imdb_url': 'https://www.imdb.com/title/tt12162902/?ref_=hm_hp_cap_pri_5'
                                   }

    def setUp(self) -> None:
        self.series_1, self.series_2 = initial_data.create_tvseries(users=self.users)

    def test_create_model_instance(self):
        """
        Check if minimal set if correct required data is provided - model instance can be created and
        saved in DB.
        """
        series = archive_models.TvSeriesModel(
            **self.series_initial_data
        )
        series.full_clean()
        series.save()

        self.assertTrue(
            archive_models.TvSeriesModel.objects.all().exists()
        )

    def test_images_association(self):
        """
        Check possibility of model to get connected to Image via genericForeignKey.
        Check direct and reverse managers.
        """
        raw_image = initial_data.generate_test_image()
        image = archive_models.ImageModel(
            content_object=self.series_1,
            image=raw_image,
        )
        image.save(fc=False)

        self.assertEqual(
            image,
            self.series_1.images.get()
        )
        self.assertEqual(
            self.series_1,
            image.series.get()
        )

    def test_interrelationship_association(self):
        """
        Check symmetrical recursive foreignkey functionality.
        """
        self.series_1.interrelationship.add(
            self.series_2, through_defaults={
                'reason_for_interrelationship': 'No reason'}
        )
        self.assertEqual(
            self.series_1.interrelationship.get(),
            self.series_2
        )
        self.assertEqual(
            self.series_2.interrelationship.get(),
            self.series_1
        )
        self.assertEqual(
            self.series_1.group.get().reason_for_interrelationship,
            'No reason'
        )

    def test_add_rating(self):
        """
        Check possibility to add rating if correct rating data is provided.
        """
        self.series_1.refresh_from_db()

        self.assertIsNone(
            self.series_1.rating
        )

        self.series_1.rating = 5
        self.series_1.full_clean()
        self.series_1.save()

        self.assertEqual(
            self.series_1.rating,
            5
        )

    def test_str_(self):
        """
        Check whether or not string representation of the model instance works fine.
        """
        expected_str = f'{self.series_1.pk} / {self.series_1.name}'
        
        self.assertEqual(
            self.series_1.__str__(),
            expected_str
        )

    def test_changed_fields_property(self):
        """
        Check whether 'changed_fields' property returns names of the changed fields.
        """
        self.series_1.name = 'updated_name'
        self.series_1.is_finished = True

        self.assertCountEqual(
            ('name', 'is_finished', 'id'),
            self.series_1.changed_fields
        )

    def test_get_absolute_url(self):
        """
        Check that 'get_absolute_url' method returns correct url.
        """
        expected_result = reverse('tvseries-detail', args=(self.series_1.pk, ))

        self.assertEqual(
            self.series_1.get_absolute_url,
            expected_result,
        )

