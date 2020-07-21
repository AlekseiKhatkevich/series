import asyncio
from typing import Coroutine, Generator

import aiohttp
import guardian.models
from asgiref.sync import sync_to_async
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.postgres.aggregates import BoolAnd, StringAgg
from django.core.mail import send_mail
from django.db.models import Case, F, OuterRef, Q, Subquery, When, functions, CharField
from rest_framework import status

import archives.models
from series.constants import DEFAULT_OBJECT_LEVEL_PERMISSION_CODE
from series.helpers.custom_functions import get_model_fields_subset

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
                'pk', 'imdb_url', named=True)
        )

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

    def __call__(self, *args, **kwargs):
        series_and_statuses = asyncio.run(self.get_status())

        series_with_invalid_url_pks = [
            series.pk for series, response_status in series_and_statuses if
            response_status != status.HTTP_200_OK
        ]

        series_with_wrong_urls = self.get_series_with_invalid_urls(series_with_invalid_url_pks)

        return series_and_statuses

    def get_series_with_invalid_urls(self, series_pks):

        user_model_deferred_fields = get_model_fields_subset(
            model=get_user_model(),
            fields_to_remove=('id', 'email', 'first_name', 'last_name', 'deleted', 'masted_id'),
            prefix='entry_author__',
        )

        series_model = archives.models.TvSeriesModel
        series_with_invalid_url = series_model.objects.select_related('entry_author'). \
            filter(pk__in=series_pks).annotate(
            responsible=Case(
                #  If entry author is not soft deleted.
                When(
                    entry_author__deleted=False,
                    then=F('entry_author__email')
                ),
                # I entry author is soft-deleted but has master alive.
                When(
                    entry_author__master__isnull=False, entry_author__master__deleted=False,
                    then=F('entry_author__master__email')
                ),
                # If entry author is soft-deleted, hasn't master alive but has alive slaves.
                When(
                    # when not [author is deleted(True) = not all slaves are deleted(False)]
                    ~Q(entry_author__deleted=BoolAnd('entry_author__slaves__deleted')),
                    then=StringAgg(
                        'entry_author__slaves__email',
                        distinct=True,
                        delimiter=', ',
                        filter=Q(entry_author__slaves__deleted=False)
                    )),
                default=Subquery(guardian.models.UserObjectPermission.objects.filter(
                        object_pk=functions.Cast(OuterRef('id'), CharField()),
                        content_type__model=series_model.__name__.lower(),
                        content_type__app_label=series_model._meta.app_label.lower(),
                        permission__codename=DEFAULT_OBJECT_LEVEL_PERMISSION_CODE,
                        user__deleted=False,
                    )[:1].values_list('user__email', flat=True)
                    ),
            ))
        return series_with_invalid_url

    def send_one_email(self, series, user):
        """
        Sends one email to one address.
        """
        subject = f'Series "{series.name}" entry contains invalid URL to imdb.'
        message = f'You series "{series.name}" entry email to IMDB on web site {settings.SITE_NAME} ' \
                  f'contains invalid url {series.imdb_url}. Please check it and correct or update.' \
                  f' Thank you.'
        from_email = settings.ADMINS[0][-1]
        recipient_list = [user.email, ]
        send_mail(subject, message, from_email, recipient_list, fail_silently=False)