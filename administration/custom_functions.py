import asyncio
from typing import Coroutine, Generator

import aiohttp
from asgiref.sync import sync_to_async

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
        return (series for series in archives.models.TvSeriesModel.objects.all())

    @staticmethod
    async def head_status(session: aiohttp.ClientSession, series: series_instance) -> tuple:
        """
        Checks response status on HEAD request being sent to url address.
        """
        async with session.head(series.imdb_url) as response:
            return series, response.status

    async def get_status(self) -> Generator[series_instance, None, None]:
        """
        Runs HEAD requests in event loop asynchronously, then constricts generator with
        series, status pairs if pair is not an exception.
        """
        async with aiohttp.ClientSession() as session:
            series_to_statuses = await asyncio.gather(
                *(self.head_status(session, series) for series in await self.get_queryset()),
                return_exceptions=True,
            )

        return (pair for pair in series_to_statuses if not isinstance(pair, Exception))


result = asyncio.run(HandleWrongUrls().get_status())