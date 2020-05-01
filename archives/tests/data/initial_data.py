import archives.models

from typing import Sequence
from PIL import Image
from io import BytesIO


from django.conf import settings
from django.core.files.base import ContentFile


users_instances = Sequence[settings.AUTH_USER_MODEL, ]
series_instances = Sequence[archives.models.TvSeriesModel, ]


def create_tvseries(users: users_instances) -> series_instances:
    """
    Creates test series for unittests.
    :param users: container or iterable of user's instances.
    :return: container of series instances.
    """
    tv_series_data = {
        'series_1':
            {'entry_author': users[0],
             'name': 'Django unleashed',
             'imdb_url': 'https://www.imdb.com'
             },
        'series_2':
            {'entry_author': users[0],
             'name': 'Shameless',
             'imdb_url': 'https://www.imdb.com/video/vi2867576345?ref_=hm_hp_i_3&listId=ls053181649'
             }
    }

    series = archives.models.TvSeriesModel.objects.bulk_create(
        [archives.models.TvSeriesModel(**fields) for fields in tv_series_data.values()]
    )
    return series


def generate_test_image() -> ContentFile:
    """
    Generates simple test image.
    """
    image = Image.new('RGBA', size=(50, 50), color=(155, 0, 0))
    file = BytesIO(image.tobytes())
    file.name = 'test.png'
    file.seek(0)
    django_friendly_file = ContentFile(file.read(), 'test.png')
    return django_friendly_file
