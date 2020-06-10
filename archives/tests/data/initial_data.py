import itertools
from io import BytesIO
from typing import Sequence
import random

from PIL import Image
from django.conf import settings
from django.core.files.base import ContentFile
from django.db.models.base import ModelBase

import archives.models

users_instances = Sequence[settings.AUTH_USER_MODEL,]
series_instances = Sequence[archives.models.TvSeriesModel,]
season_instances = Sequence[archives.models.SeasonModel,]
models_instance = Sequence[ModelBase,]


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


def create_images_instances(model_instances: models_instance) -> None:
    """
    Attaches generated images to model instances via generic relations.
    """
    instances_pool = []

    for instance in model_instances:
        instances_pool.append(
            archives.models.ImageModel(
                image=generate_test_image(),
                content_object=instance
            ))
    archives.models.ImageModel.objects.bulk_create(
        instances_pool
    )
