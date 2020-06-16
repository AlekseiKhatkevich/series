import itertools
import random
from io import BytesIO
from typing import Sequence

from PIL import Image
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import models

import archives.models

users_instances = Sequence[settings.AUTH_USER_MODEL, ]
series_instances = Sequence[archives.models.TvSeriesModel, ]
season_instances = Sequence[archives.models.SeasonModel, ]
models_instances = Sequence[models.Model]
image_instances = Sequence[archives.models.ImageModel, ]


def create_tvseries(users: users_instances) -> series_instances:
    """
    Creates test series for unittests.
    :param users: Container or iterable of user's instances.
    :return: Container of series instances.
    """
    tv_series_data = {
        'series_1':
            {'entry_author': users[0],
             'name': 'Django unleashed',
             'imdb_url': 'https://www.imdb.com'
             },
        'series_2':
            {'entry_author': users[1],
             'name': 'Shameless',
             'imdb_url': 'https://www.imdb.com/video/vi2867576345?ref_=hm_hp_i_3&listId=ls053181649'
             }
    }

    series = archives.models.TvSeriesModel.objects.bulk_create(
        [archives.models.TvSeriesModel(**fields) for fields in tv_series_data.values()]
    )
    return series


def create_seasons(series: series_instances, num_episodes: int = 2) -> season_instances:
    """
    Creates new seasons for tests. 2 episodes for each of 2 series by default.
    :param num_episodes: Number of episodes to create in each series.
    :param series: TvSeriesModel instances.
    :return: SeasonModel instances.
    """
    order = itertools.count(0)
    seasons = {}

    for single_series in series:
        for season_number in range(num_episodes):
            new_season_data = {
                f'{single_series.name} season {season_number + 1}': {
                    'series': single_series,
                    'season_number': season_number + 1,
                    'number_of_episodes': random.randint(7, 10),
                    '_order': next(order),
                }}
            seasons.update(new_season_data)

    seasons = archives.models.SeasonModel.objects.bulk_create(
        [archives.models.SeasonModel(**fields) for fields in seasons.values()]
    )
    return seasons


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


def generate_test_image_2() -> SimpleUploadedFile:
    """
    Generates simple test image.
    """
    small_gif = (
        b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9\x04'
        b'\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02'
        b'\x02\x4c\x01\x00\x3b'
    )
    return SimpleUploadedFile('small.gif', small_gif, content_type='image/gif')



def generate_test_image_as_file():
    """
    Generates small file.
    """
    img = Image.new('RGBA', (60, 30), color='red')
    img.save('test_image_file.png')
    return img


def create_images_instances(model_instances: models_instances, num_img: int = 1) -> image_instances:
    """
    Attaches generated images to model instances via generic relations.
    """
    instances_pool = []

    for instance in model_instances:
        for _ in range(num_img):
            instances_pool.append(
                archives.models.ImageModel(
                    image=generate_test_image(),
                    content_object=instance
                ))
    images = archives.models.ImageModel.objects.bulk_create(
        instances_pool
    )
    return images
