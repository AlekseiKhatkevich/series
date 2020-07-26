import asyncio
from typing import Coroutine, Generator, List

import aiohttp
from asgiref.sync import sync_to_async
from django.db.models import QuerySet
from rest_framework import status

import administration.tasks
import archives.models

series_instance = archives.models.TvSeriesModel
series_generator = Generator[series_instance, None, series_instance]


class HandleWrongUrls:
    """
    Checks statuses of each url in archives series and in case of status != 200 sends email
    to user in order to notify him.
    """
    @staticmethod
    @sync_to_async
    def get_queryset() -> Coroutine[series_generator, None, series_generator]:
        """
        Fetches all series from DB and turns this queryset to generator.
        """
        # noinspection PyTypeChecker
        return (
            series for series in archives.models.TvSeriesModel.objects.values_list(
                'pk', 'imdb_url', named=True,
            ))

    @staticmethod
    async def head_status(
            session: aiohttp.ClientSession,
            series: series_instance,
            semaphore: asyncio.Semaphore
    ) -> tuple:
        """
        Checks response status on HEAD request being sent to url address.
        """
        async with semaphore, session.head(series.imdb_url) as response:
            return series, response.status

    async def get_status(
            self,
            max_workers: int = 20,
            response_timeout: int = 7,
    ) -> Generator[series_instance, None, None]:
        """
        Runs HEAD requests in event loop asynchronously, then constricts generator with
        series, status pairs if pair is not an exception.
        """
        semaphore = asyncio.Semaphore(max_workers)

        async with aiohttp.ClientSession() as session:
            series_to_statuses = await asyncio.gather(
                *(asyncio.wait_for(self.head_status(session, series, semaphore), response_timeout)
                  for series in await self.get_queryset()
                  ), return_exceptions=True,
            )

        return (pair for pair in series_to_statuses if not isinstance(pair, Exception))

    @staticmethod
    def get_series_with_invalid_urls(series_pks: List[int]) -> QuerySet:
        """
        Returns queryset with limited values of series with invalid urls annotated with
        email of a person who is responsible for this series atm.
        """
        select = ('entry_author', 'entry_author__master', )
        prefetch = ('entry_author__slaves', )

        series_with_invalid_url = archives.models.TvSeriesModel.objects.select_related(*select). \
            prefetch_related(*prefetch).filter(pk__in=series_pks).annotate_with_responsible_user().\
            values('name', 'imdb_url', 'responsible', )

        return series_with_invalid_url

    def __call__(self, *args, **kwargs) -> str:
        """
        Starts whole process. Sends emails to responsible users via Celery finally.
        """
        series_and_statuses = asyncio.run(self.get_status())

        series_with_invalid_url_pks = [
            series.pk for series, response_status in series_and_statuses if
            response_status != status.HTTP_200_OK
        ]

        series_with_wrong_urls = self.get_series_with_invalid_urls(series_with_invalid_url_pks)

        for series in series_with_wrong_urls:
            administration.tasks.send_one_email.delay(series)

        return f'There are {len(series_with_invalid_url_pks)} series with invalid urls.'



