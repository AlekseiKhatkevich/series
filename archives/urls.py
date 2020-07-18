from django.urls import include, path, register_converter
from rest_framework import routers

import archives.converters
import archives.views

register_converter(
    archives.converters.CommaSeparatedIntegersPathConverter,
    'int_list',
)

router = routers.SimpleRouter()
router.register(
    r'',
    archives.views.SeasonsViewSet,
    basename='seasonmodel',
)


urlpatterns = [
    path(
        'tvseries/<int:series_pk>/', include([
                path(
                    'upload-image/<str:filename>/',
                    archives.views.FileUploadDeleteView.as_view(),
                    name='upload',
                ),
                path(
                    'delete-image/<int_list:image_pk>/',
                    archives.views.FileUploadDeleteView.as_view(),
                    name='delete-image',
                ),
                path(
                    '',
                    archives.views.TvSeriesDetailView.as_view(),
                    name='tvseries-detail',
                ),
                path('seasons/', include(router.urls))
        ])),
    # path(
    #     'tvseries/<str:position>/<int:percent>/',
    #     'view',
    #     name='x-percent',
    # ),
    path(
        'tvseries/',
        archives.views.TvSeriesListCreateView.as_view(),
        name='tvseries',
    ),
]
